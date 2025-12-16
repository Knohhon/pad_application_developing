import aio_pika
import asyncio
import json
import uuid
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

# Настройки из переменных окружения (с возможностью переопределения)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2Flocal")
QUEUE_DURABLE = os.getenv("QUEUE_DURABLE", "false").lower() == "true"
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "")
ROUTING_KEYS = {
    "product": os.getenv("PRODUCT_ROUTING_KEY", "product"),
    "order": os.getenv("ORDER_ROUTING_KEY", "order")
}

async def get_connection() -> aio_pika.Connection:
    """Установка соединения с RabbitMQ с повторными попытками"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(
                RABBITMQ_URL,
                loop=asyncio.get_running_loop(),
                timeout=5.0
            )
            print(f"✅ Connected to RabbitMQ at {RABBITMQ_URL}")
            return connection
        except Exception as e:
            print(f"⚠️ Connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise ConnectionError(f"Failed to connect to RabbitMQ after {max_retries} attempts") from e

async def ensure_queue_exists(channel: aio_pika.Channel, queue_name: str) -> aio_pika.Queue:
    """Проверка существования очереди с совместимыми параметрами"""
    try:
        # Попытка объявить очередь с параметрами, совместимыми с существующей
        queue = await channel.declare_queue(
            queue_name,
            durable=QUEUE_DURABLE,
            auto_delete=False,
            passive=False  # Не использовать passive mode для создания очереди
        )
        print(f"✅ Queue '{queue_name}' declared (durable={QUEUE_DURABLE})")
        return queue
    except aio_pika.exceptions.ChannelClosed as e:
        if "PRECONDITION_FAILED" in str(e):
            print(f"⚠️ Queue '{queue_name}' already exists with different parameters. Trying to use existing queue...")
            
            # Попытка получить информацию о существующей очереди без изменения параметров
            try:
                queue = await channel.declare_queue(
                    queue_name,
                    passive=True  # Только проверить существование
                )
                print(f"✅ Using existing queue '{queue_name}'")
                return queue
            except aio_pika.exceptions.ChannelClosed as inner_e:
                if "NOT_FOUND" in str(inner_e):
                    print(f"❌ Queue '{queue_name}' not found and cannot be created with compatible parameters")
                raise
        raise

async def send_message(routing_key: str, message: Dict[str, Any]):
    """Отправка сообщения в RabbitMQ через aio-pika с обработкой ошибок"""
    connection = None
    try:
        connection = await get_connection()
        channel = await connection.channel()
        
        # Гарантируем существование очереди
        await ensure_queue_exists(channel, routing_key)
        
        # Подготовка сообщения
        message_body = aio_pika.Message(
            body=json.dumps(message, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT if QUEUE_DURABLE else aio_pika.DeliveryMode.NOT_PERSISTENT,
            timestamp=datetime.utcnow(),
            headers={
                "source": "test_producer",
                "message_id": str(uuid.uuid4()),
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        
        # Отправка сообщения
        exchange = await channel.get_exchange(EXCHANGE_NAME) if EXCHANGE_NAME else channel.default_exchange
        
        await exchange.publish(
            message_body,
            routing_key=routing_key
        )
        
        formatted_message = json.dumps(message, indent=2, default=str)
        print(f"\nSent to queue '{routing_key}':")
        print(formatted_message)
        
    except Exception as e:
        print(f"Failed to send message to '{routing_key}': {str(e)}")
        raise
    finally:
        if connection:
            await connection.close()
            print("   RabbitMQ connection closed")

async def create_test_data():
    """Генерация тестовых данных и отправка в очереди"""
    products = []
    for i in range(5):
        product = {
            "id": str(uuid.uuid4()),
            "label": f"Test Product {i+1}",
            "count_in_package": 10 + i,
            "count_in_warehouse": 100 - i*10,
            "price": float(Decimal(f"{(i+1)*19.99:.2f}"))
        }
        products.append(product)
        await send_message(ROUTING_KEYS["product"], product)
        await asyncio.sleep(0.3)

    print("CREATING TEST ORDERS")
    
    for j in range(3):
        order = {
            "user_id": str(uuid.uuid4()),
            "address_id": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": products[j % 5]["id"],
                    "quantity": j + 1
                },
                {
                    "product_id": products[(j + 1) % 5]["id"],
                    "quantity": 1
                }
            ]
        }
        await send_message(ROUTING_KEYS["order"], order)
        await asyncio.sleep(0.3)

    print("TEST DATA GENERATION COMPLETED")
    print(f"5 products created")
    print(f"3 orders created")

async def health_check() -> bool:
    """Проверка доступности RabbitMQ"""
    try:
        connection = await aio_pika.connect_robust(
            RABBITMQ_URL,
            loop=asyncio.get_running_loop(),
            timeout=3.0
        )
        await connection.close()
        print("RabbitMQ health check passed")
        return True
    except Exception as e:
        print(f"RabbitMQ health check failed: {str(e)}")
        return False

async def main():
    """Основная функция запуска продюсера"""
    print("Starting test data producer...")
    print(f"RabbitMQ URL: {RABBITMQ_URL}")
    print(f"Queue durable: {QUEUE_DURABLE}")
    print(f"Exchange: '{EXCHANGE_NAME or 'default'}'")
    print(f"Product routing key: '{ROUTING_KEYS['product']}'")
    print(f"Order routing key: '{ROUTING_KEYS['order']}'")
    
    # Проверка доступности RabbitMQ
    if not await health_check():
        print("Cannot proceed without RabbitMQ connection")
        return
    
    try:
        await create_test_data()
    except Exception as e:
        print(f"Critical error during data generation: {str(e)}")
        raise
    finally:
        print("Producer execution completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProducer stopped by user")
    except Exception as e:
        print(f"Critical error: {str(e)}")
        exit(1)
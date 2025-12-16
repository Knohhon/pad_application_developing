import aio_pika
import asyncio
import json
import uuid
from datetime import datetime
from decimal import Decimal
import time
import os

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/local"
EXCHANGE_NAME = "" 
PRODUCT_ROUTING_KEY = "product"
ORDER_ROUTING_KEY = "order"

async def wait_for_rabbitmq(max_attempts: int = 10, delay: float = 2.0) -> bool:
    """Ожидание полной инициализации RabbitMQ с повторными попытками"""
    print("Ожидание готовности RabbitMQ...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await aio_pika.connect_robust(
                RABBITMQ_URL,
                timeout=3.0
            )
            await connection.close()
            print(f"RabbitMQ готов к работе (попытка {attempt}/{max_attempts})")
            return True
        except Exception as e:
            print(f"Попытка {attempt}/{max_attempts} не удалась: {str(e)}")
            if attempt < max_attempts:
                print(f"Следующая попытка через {delay} секунд...")
                await asyncio.sleep(delay)
            else:
                print(f"RabbitMQ не отвечает после {max_attempts} попыток")
                return False

async def send_message(routing_key: str, message: dict):
    """Отправка сообщения без объявления очереди (только публикация)"""
    connection = None
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        message_body = aio_pika.Message(
            body=json.dumps(message, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
            timestamp=datetime.now(),
            headers={
                "source": "test_producer",
                "message_id": str(uuid.uuid4()),
                "sent_at": datetime.now().isoformat()
            }
        )
        
        await channel.default_exchange.publish(
            message_body,
            routing_key=routing_key
        )
        
        print(f"\nОтправлено в '{routing_key}':")
        print(json.dumps(message, indent=2, default=str))
        
    except Exception as e:
        print(f"Ошибка отправки в '{routing_key}': {str(e)}")
        raise
    finally:
        if connection and not connection.is_closed:
            await connection.close()

async def create_test_data():
    """Генерация и отправка тестовых данных"""
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ")
    
    # Создаем 5 продуктов
    products = []
    for i in range(5):
        product = {
            "label": f"Продукт #{i+1}",
            "count_in_package": 5 * (i+1),
            "count_in_warehouse": 100 - (i * 15),
            "price": float(Decimal(f"{(i+1) * 15.50:.2f}"))
        }
        products.append(product)
        await send_message(PRODUCT_ROUTING_KEY, product)
        await asyncio.sleep(0.3)

    print("СОЗДАНИЕ ТЕСТОВЫХ ЗАКАЗОВ")
    
    for j in range(3):
        order = {
            "user_id": str(uuid.uuid4()),
            "address_id": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": j + 1
                },
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 2
                }
            ]
        }
        await send_message(ORDER_ROUTING_KEY, order)
        await asyncio.sleep(0.3)

    print("ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО ОТПРАВЛЕНЫ!")
    print(f"5 продуктов в очередь '{PRODUCT_ROUTING_KEY}'")
    print(f"3 заказа в очередь '{ORDER_ROUTING_KEY}'")

async def main():
    """Основная логика запуска"""
    print("ЗАПУСК ТЕСТОВОГО ПРОДЮСЕРА")
    print(f"URL подключения: {RABBITMQ_URL}")
    print(f"Виртуальный хост: local")
    print(f"Очередь продуктов: '{PRODUCT_ROUTING_KEY}'")
    print(f"Очередь заказов: '{ORDER_ROUTING_KEY}'")
    
    if not await wait_for_rabbitmq():
        print("Продюсер остановлен из-за недоступности RabbitMQ")
        return
    
    try:
        await create_test_data()
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        time.sleep(3)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПродюсер остановлен пользователем")
    except Exception as e:
        print(f"\nОШИБКА: {str(e)}")
        exit(1)
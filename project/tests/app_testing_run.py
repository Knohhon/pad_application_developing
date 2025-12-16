from faststream import FastStream
from faststream.rabbit import RabbitBroker
import asyncio

broker = RabbitBroker("amqp://guest:guest@localhost:5672/local")
app = FastStream(broker)

@broker.subscriber("order")
async def handle(msg):
    print(msg)

@app.after_startup
async def test_publish():
    await broker.publish(
        "message",
        "order",
    )

async def main():
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())

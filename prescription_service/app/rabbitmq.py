import aio_pika
import os
import json
import asyncio

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")


async def send_prescription_uploaded_message(message_data: dict):
    """Отправка сообщения о загрузке нового рецепта"""
    try:
        connection = await aio_pika.connect_robust(AMQP_URL)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message_data).encode()),
                routing_key="prescription_uploaded"
            )
        print(f"Sent prescription uploaded message: {message_data}")
    except Exception as e:
        print(f"Failed to send prescription uploaded message: {e}")


async def process_cart_cleared_message(msg: aio_pika.IncomingMessage):
    """Обработка сообщения об очистке корзины"""
    async with msg.process():
        try:
            data = json.loads(msg.body.decode())
            print(f"Received cart cleared message for user: {data['user_id']}")
            # Здесь может быть логика, например, уведомление пользователя
            # что рецепты могут понадобиться снова при новом заказе
        except Exception as e:
            print(f"Error processing cart cleared message: {e}")


async def consume_messages():
    """Запуск потребителя RabbitMQ"""
    try:
        connection = await aio_pika.connect_robust(AMQP_URL)
        async with connection:
            channel = await connection.channel()

            # Объявляем очередь для сообщений об очистке корзины
            cart_cleared_queue = await channel.declare_queue("cart_cleared", durable=True)

            # Начинаем потребление сообщений
            await cart_cleared_queue.consume(process_cart_cleared_message)

            print("Prescription Service started consuming messages...")

            # Бесконечное ожидание
            await asyncio.Future()

    except Exception as e:
        print(f"RabbitMQ connection error: {e}")
        # Переподключение через 5 секунд
        await asyncio.sleep(5)
        await consume_messages()
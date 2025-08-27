# import pika
# import json
# import time
# from ratelimit import limits, sleep_and_retry
# from .hyatt import ExtractHyatt
#
# # Allow max 5 calls per 60 seconds
# @sleep_and_retry
# @limits(calls=5, period=60)
# def throttled_extract(hotel_id, check_in_date, check_out_date, guest_count):
#     extractor = ExtractHyatt()
#     extractor.get_search_data(hotel_id, check_in_date, check_out_date, guest_count)
#
# def callback(ch, method, properties, body):
#     try:
#         data = json.loads(body)
#
#         # Validate required keys
#         required_keys = ['hotel_id', 'check_in_date', 'check_out_date','guest_count']
#         if not all(key in data for key in required_keys):
#             print(f"[Consumer] Invalid message format: missing keys in {data}")
#             ch.basic_ack(delivery_tag=method.delivery_tag)
#             return
#
#         print(f"[Consumer] Received: {data}")
#
#         # Throttled extraction logic
#         throttled_extract(
#             data['hotel_id'],
#             data['check_in_date'],
#             data['check_out_date'],
#             data['guest_count']
#         )
#
#     except Exception as e:
#         print(f"[Consumer] Error processing message: {e}\nRaw body: {body}")
#
#     finally:
#         # Always acknowledge to avoid message requeue loop
#         ch.basic_ack(delivery_tag=method.delivery_tag)
#
# import pika
#
# def start_consumer(username, password):
#     credentials = pika.PlainCredentials(username, password)
#     connection = pika.BlockingConnection(
#         pika.ConnectionParameters('localhost', 5672, '/', credentials)
#     )
#     channel = connection.channel()
#
#     channel.queue_declare(queue='task_queue', durable=True)
#     channel.basic_qos(prefetch_count=1)
#
#     channel.basic_consume(queue='task_queue', on_message_callback=callback)
#
#     print("[Consumer] Waiting for messages. To exit press CTRL+C")
#     channel.start_consuming()
#
#
# if __name__ == "__main__":
#     start_consumer('user', 'password')


import asyncio
import json
from ratelimit import limits, sleep_and_retry
from aio_pika import connect_robust, IncomingMessage
from .hyatt import ExtractHyatt

# Allow max 5 calls per 60 seconds
@sleep_and_retry
@limits(calls=5, period=60)
async def throttled_extract(hotel_id, check_in_date, check_out_date, guest_count):
    extractor = ExtractHyatt()
    await extractor.get_search_data(hotel_id, check_in_date, check_out_date, guest_count)

async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)

            required_keys = ['hotel_id', 'check_in_date', 'check_out_date', 'guest_count']
            if not all(key in data for key in required_keys):
                print(f"[Consumer] Invalid message format: missing keys in {data}")
                return

            print(f"[Consumer] Received: {data}")

            await throttled_extract(
                data['hotel_id'],
                data['check_in_date'],
                data['check_out_date'],
                data['guest_count']
            )
        except Exception as e:
            print(f"[Consumer] Error processing message: {e}")

async def main(username, password):
    connection = await connect_robust(
        "amqp://{}:{}@localhost/".format(username, password)
    )
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue("task_queue", durable=True)
    await queue.consume(on_message)

    print("[Consumer] Waiting for messages. To exit press CTRL+C")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    import sys
    username = 'user'
    password = 'password'
    asyncio.run(main(username, password))

# client.py
import pika
import json
from pathlib import Path

import pika
import json

def send_to_queue(data, username, password):
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost', 5672, '/', credentials)
    )
    channel = connection.channel()

    channel.queue_declare(queue='task_queue', durable=True)
    message = json.dumps(data)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )
    print(f"[Client] Sent: {data}")
    connection.close()


if __name__ == "__main__":

    # ---- Read request.json ----
    request_filepath = Path(__file__).parent/ "request.json"
    with request_filepath.open("r", encoding="utf-8") as f:
        dataList = json.load(f)

    for data in dataList["data"]:
        message = {
            "hotel_id": data["hotel_id"],
            "check_in_date": data["check_in_date"],
            "check_out_date": data["check_out_date"],
            "guest_count": int(data["guest_count"])
        }

        send_to_queue(message, 'user', 'password')

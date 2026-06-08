from aiokafka import AIOKafkaProducer
import json

producer: AIOKafkaProducer | None = None

async def start_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()

async def stop_producer():
    await producer.stop()

async def publish_alert_created(alert_id: int, patient_id: int, created_at: str):
    await producer.send(
        "healthcare.alerts.created",
        value={
            "alert_id": alert_id,
            "patient_id": patient_id,
            "created_at": created_at
        }
    )
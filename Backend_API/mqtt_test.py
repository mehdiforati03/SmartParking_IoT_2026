import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone

BROKER = "broker.emqx.io"
PORT = 1883
CLIENT_ID = "SmartPark2026_PUB_TEST"

def iso_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def publish_sensor_like(
    spot_id: str,
    status: str,
    distance_cm: float | None = None,
    threshold_cm: float = 50.0,
    debounce_n: int = 4,
):
    topic = f"smart_parking_2026/parking/spots/{spot_id}/status"
    payload = {
        "id": spot_id,
        "status": status,
        "distance_cm": distance_cm,
        "threshold_cm": float(threshold_cm),
        "debounce_n": int(debounce_n),
        "ts": iso_now(),
    }


    if distance_cm is None:
        payload.pop("distance_cm")

    client = mqtt.Client(client_id=CLIENT_ID)

    client.connect(BROKER, PORT)
    client.publish(topic, json.dumps(payload))
    client.disconnect()

    print(f"[PUB] {topic} <- {payload}")

if __name__ == "__main__":

    #publish_sensor_like("A01", "OCCUPIED", distance_cm=18.5)


    publish_sensor_like("A01", "FREE", distance_cm=200.0)

    #publish_sensor_like("A01", "OCCUPIED", distance_cm=20.0)

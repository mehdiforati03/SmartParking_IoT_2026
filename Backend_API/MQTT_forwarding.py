import paho.mqtt.client as mqtt
import json
import requests

API_BASE = "http://localhost:3000"

BROKER = "broker.emqx.io"
PORT = 1883
CLIENT_ID = "SmartPark2026_P6"
TOPIC = "smart_parking_2026/parking/spots/+/status"

def build_update_payload(payload: dict):
    out = {"status": payload.get("status")}

    dc = payload.get("distance_cm")
    tc = payload.get("threshold_cm")
    dn = payload.get("debounce_n")

    if isinstance(dc, (int, float)):
        out["distance"] = float(dc)
    if isinstance(tc, (int, float)):
        out["threshold"] = float(tc)
    if isinstance(dn, int):
        out["debounce"] = dn

    return out

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"✅ Connected: reason_code={reason_code}")
    client.subscribe(TOPIC)
    print(f"✅ Subscribed to {TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        spot_id = payload.get("id")
        status = payload.get("status")

        if not spot_id or status not in ["FREE", "OCCUPIED"]:
            return

        update_body = build_update_payload(payload)

        r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
        print(f"➡️ {msg.topic} -> REST {r.status_code}")

        if r.status_code == 404:
            create_body = {"id": spot_id, "label": payload.get("label") or spot_id}
            for k in ("distance", "threshold", "debounce"):
                if k in update_body:
                    create_body[k] = update_body[k]

            requests.post(f"{API_BASE}/places", json=create_body, timeout=2)
            r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
            print(f"🔁 retry -> REST {r.status_code}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

client = mqtt.Client(client_id=CLIENT_ID) 
client.on_connect = on_connect
client.on_message = on_message

print(f"🔌 Connecting to {BROKER}:{PORT} ...")
client.connect(BROKER, PORT)
client.loop_forever()

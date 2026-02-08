import paho.mqtt.client as mqtt
import json
import requests

API_BASE = "http://localhost:3000"

BROKER = "broker.emqx.io"
PORT = 1883
CLIENT_ID = "SmartPark2026_P6"
TOPIC = "smart_parking_2026/parking/spots/+/status"
TOPIC_BARRIER = "smart_parking_2026/parking/barriers/+/state"

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

def topic_barrier_id(topic: str):
    #smart_parking_2026/parking/barriers/{id}/state
    parts = topic.split("/")
    if len(parts) >= 2:
        return parts[-2]  # {id}
    return None

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"✅ Connected: reason_code={reason_code}")
    client.subscribe(TOPIC)
    client.subscribe(TOPIC_BARRIER)
    print(f"✅ Subscribed to {TOPIC}")
#########################
#fonctions de traitemens#
#########################

def forward_spot(payload: dict, topic: str):
    spot_id = payload.get("id")
    status = payload.get("status")
    if not spot_id or status not in ["FREE", "OCCUPIED"]:
        return

    update_body = build_update_payload(payload)

    r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
    print(f"➡️ {topic} -> REST {r.status_code}")

    if r.status_code == 404:
        create_body = {"id": spot_id, "label": payload.get("label") or spot_id}
        for k in ("distance", "threshold", "debounce"):
            if k in update_body:
                create_body[k] = update_body[k]

        requests.post(f"{API_BASE}/places", json=create_body, timeout=2)
        r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
        print(f"🔁 retry -> REST {r.status_code}")

def forward_barrier_state(payload: dict, topic: str):
    state = payload.get("state")
    if state not in ["OPENING", "OPENED", "CLOSING", "CLOSED"]:
        return

    barrier_id = topic_barrier_id(topic)
    if not barrier_id:
        return

    r = requests.put(
        f"{API_BASE}/barrier/{barrier_id}/state",
        json={"state": state},
        timeout=2
    )
    print(f"🚧 {topic} state={state} -> REST {r.status_code}")
######
#main#
######
def on_message(client, userdata, msg):


import paho.mqtt.client as mqtt
import json
import requests

API_BASE = "http://localhost:3000"

BROKER = "broker.emqx.io"
PORT = 1883
CLIENT_ID = "SmartPark2026_P6"
TOPIC = "smart_parking_2026/parking/spots/+/status"
TOPIC_BARRIER = "smart_parking_2026/parking/barriers/+/state"

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

def topic_barrier_id(topic: str):
    #smart_parking_2026/parking/barriers/{id}/state
    parts = topic.split("/")
    if len(parts) >= 2:
        return parts[-2]  # {id}
    return None

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"✅ Connected: reason_code={reason_code}")
    client.subscribe(TOPIC)
    client.subscribe(TOPIC_BARRIER)
    print(f"✅ Subscribed to {TOPIC}")
#########################
#fonctions de traitemens#
#########################

def forward_spot(payload: dict, topic: str):
    spot_id = payload.get("id")
    status = payload.get("status")
    if not spot_id or status not in ["FREE", "OCCUPIED"]:
        return

    update_body = build_update_payload(payload)

    r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
    print(f"➡️ {topic} -> REST {r.status_code}")

    if r.status_code == 404:
        create_body = {"id": spot_id, "label": payload.get("label") or spot_id}
        for k in ("distance", "threshold", "debounce"):
            if k in update_body:
                create_body[k] = update_body[k]

        requests.post(f"{API_BASE}/places", json=create_body, timeout=2)
        r = requests.put(f"{API_BASE}/places/{spot_id}/status", json=update_body, timeout=2)
        print(f"🔁 retry -> REST {r.status_code}")

def forward_barrier_state(payload: dict, topic: str):
    state = payload.get("state")
    if state not in ["OPENING", "OPENED", "CLOSING", "CLOSED"]:
        return

    barrier_id = topic_barrier_id(topic)
    if not barrier_id:
        return

    r = requests.put(
        f"{API_BASE}/barrier/{barrier_id}/state",
        json={"state": state},
        timeout=2
    )
    print(f"🚧 {topic} state={state} -> REST {r.status_code}")
######
#main#
######
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if "/parking/spots/" in topic and topic.endswith("/status"):
            forward_spot(payload, topic)
        elif "/parking/barriers/" in topic and topic.endswith("/state"):
            forward_barrier_state(payload, topic)

    except Exception as e:
        print(f"⚠️ Error: {e}")

client = mqtt.Client(client_id=CLIENT_ID) 
client.on_connect = on_connect
client.on_message = on_message

print(f"🔌 Connecting to {BROKER}:{PORT} ...")
client.connect(BROKER, PORT)
client.loop_forever()


client = mqtt.Client(client_id=CLIENT_ID) 
client.on_connect = on_connect
client.on_message = on_message

print(f"🔌 Connecting to {BROKER}:{PORT} ...")
client.connect(BROKER, PORT)
client.loop_forever()

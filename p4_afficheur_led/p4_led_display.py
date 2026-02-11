from flask import Flask, jsonify
import json
from datetime import datetime
import paho.mqtt.client as mqtt

app = Flask(__name__)

SPOTS = [f"A{i:02d}" for i in range(1, 21)]
places = {sid: "FREE" for sid in SPOTS}

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
PREFIX = "smart_parking_2026"

MQTT_SPOTS_TOPIC = f"{PREFIX}/parking/spots/+/status"
MQTT_LED_TOPIC = f"{PREFIX}/parking/display/available"

MQTT_BARRIER_ENTRY_STATE = f"{PREFIX}/parking/barriers/entry/state"
MQTT_BARRIER_EXIT_STATE = f"{PREFIX}/parking/barriers/exit/state"

mqtt_client = None

barrier = {
    "entry": {"state": "UNKNOWN", "ts": None},
    "exit": {"state": "UNKNOWN", "ts": None},
}


def _normalize_place_id(raw):
    if raw is None:
        return None
    raw = str(raw).upper().strip()
    if not (raw.startswith("A") and raw[1:].isdigit()):
        return None
    return f"A{int(raw[1:]):02d}"


def publish_led_summary():
    if mqtt_client is None:
        return

    total = len(places)
    occupied = sum(1 for s in places.values() if s == "OCCUPIED")
    free = total - occupied

    payload = {"count": free, "ts": datetime.now().isoformat(timespec="seconds")}
    mqtt_client.publish(MQTT_LED_TOPIC, json.dumps(payload), qos=1, retain=True)


def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(MQTT_SPOTS_TOPIC, qos=1)
    client.subscribe(MQTT_BARRIER_ENTRY_STATE, qos=1)
    client.subscribe(MQTT_BARRIER_EXIT_STATE, qos=1)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload_str = msg.payload.decode("utf-8", errors="ignore").strip()

    if topic.startswith(f"{PREFIX}/parking/spots/") and topic.endswith("/status"):
        parts = topic.split("/")
        if len(parts) < 5:
            return

        place_id = _normalize_place_id(parts[3])
        if place_id is None:
            return

        status = None
        try:
            data = json.loads(payload_str)
            status = str(data.get("status", "")).upper()

            incoming_id = _normalize_place_id(data.get("id"))
            if incoming_id is not None:
                place_id = incoming_id
        except Exception:
            status = payload_str.upper()

        if status not in ("FREE", "OCCUPIED"):
            return

        if place_id in places:
            places[place_id] = status
            publish_led_summary()
        return

    if topic in (MQTT_BARRIER_ENTRY_STATE, MQTT_BARRIER_EXIT_STATE):
        try:
            data = json.loads(payload_str)
        except Exception:
            return

        state = str(data.get("state", "")).upper()
        if state not in ("OPENING", "OPENED", "CLOSING", "CLOSED"):
            return

        which = "entry" if topic == MQTT_BARRIER_ENTRY_STATE else "exit"
        barrier[which]["state"] = state
        barrier[which]["ts"] = datetime.now().isoformat(timespec="seconds")
        return


def start_mqtt():
    global mqtt_client
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="SmartPark2026_P4",
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    mqtt_client = client


@app.get("/")
def led_display():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>Afficheur LED - Smart Parking</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #0b0f14;
      color: white;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }
    .panel {
      background: #111827;
      padding: 40px;
      border-radius: 20px;
      box-shadow: 0 0 30px rgba(0,0,0,0.6);
      text-align: center;
      width: 460px;
    }
    h1 {
      margin-bottom: 18px;
      font-size: 20px;
      color: #30ff88;
    }
    .count {
      font-size: 56px;
      font-weight: bold;
      letter-spacing: 1px;
    }
    .label {
      font-size: 16px;
      color: #cfcfcf;
      margin-top: 6px;
    }
    .status {
      margin-top: 16px;
      font-size: 22px;
      color: #ffcc00;
    }
    .hint {
      margin-top: 10px;
      font-size: 12px;
      color: #9aa4b2;
    }
    .barriers {
      margin-top: 22px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      text-align: left;
    }
    .card {
      background: #0f172a;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 14px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .icon {
      width: 16px;
      height: 16px;
      border-radius: 6px;
      background: #6b7280;
      box-shadow: 0 0 12px rgba(0,0,0,0.5);
      flex: 0 0 auto;
    }
    .meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .meta .title {
      font-weight: 700;
      font-size: 13px;
      color: #e5e7eb;
    }
    .meta .state {
      font-size: 12px;
      color: #9aa4b2;
    }
  </style>
</head>
<body>
  <div class="panel">
    <h1>Afficheur LED – Parking Intelligent</h1>

    <div class="count" id="free">-- / --</div>
    <div class="label">Places libres</div>

    <div class="status" id="state">Chargement...</div>
    <div class="hint">Mise à jour automatique (toutes les 2 secondes)</div>

    <div class="barriers">
      <div class="card">
        <div class="icon" id="entryIcon"></div>
        <div class="meta">
          <div class="title">Barrière Entrée</div>
          <div class="state" id="entryState">UNKNOWN</div>
        </div>
      </div>

      <div class="card">
        <div class="icon" id="exitIcon"></div>
        <div class="meta">
          <div class="title">Barrière Sortie</div>
          <div class="state" id="exitState">UNKNOWN</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function colorForBarrierState(s) {
      if (s === "OPENED") return "#22c55e";
      if (s === "OPENING") return "#f59e0b";
      if (s === "CLOSING") return "#f59e0b";
      if (s === "CLOSED") return "#ef4444";
      return "#6b7280";
    }

    async function update() {
      const r = await fetch('/api/parking/summary');
      const data = await r.json();

      document.getElementById('free').innerText = data.free + " / " + data.total;

      if (data.free === 0) {
        document.getElementById('state').innerText = "Parking complet";
      } else {
        document.getElementById('state').innerText = "Places disponibles";
      }

      const b = await fetch('/api/barriers');
      const bd = await b.json();

      const entryS = (bd.entry && bd.entry.state) ? bd.entry.state : "UNKNOWN";
      const exitS  = (bd.exit  && bd.exit.state)  ? bd.exit.state  : "UNKNOWN";

      document.getElementById("entryState").innerText = entryS;
      document.getElementById("exitState").innerText  = exitS;

      document.getElementById("entryIcon").style.background = colorForBarrierState(entryS);
      document.getElementById("exitIcon").style.background  = colorForBarrierState(exitS);
    }

    update();
    setInterval(update, 2000);
  </script>
</body>
</html>
"""


@app.get("/api/parking/places")
def get_places():
    return jsonify([{"id": pid, "status": status} for pid, status in places.items()])


@app.get("/api/parking/summary")
def get_summary():
    total = len(places)
    occupied = sum(1 for s in places.values() if s == "OCCUPIED")
    free = total - occupied
    return jsonify({"total": total, "occupied": occupied, "free": free})


@app.get("/api/barriers")
def get_barriers():
    return jsonify(barrier)


if __name__ == "__main__":
    start_mqtt()
    publish_led_summary()
    app.run(host="127.0.0.1", port=3000, debug=True, use_reloader=False)

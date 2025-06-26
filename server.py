import json
import random
from flask import Flask, request, jsonify
import crypto_utils
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from ambulance import Ambulance
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel, ValidationError

app = Flask(__name__)
DEV = False
socketio = SocketIO(app, debug=True, cors_allowed_origins='*')
scheduler = BackgroundScheduler()
AMBULANCE_UPDATES_ROOM = "ambulance_updates"
AMBULANCE_SCHEDULE_INTERVAL = 0.5
AMBULANCE_ADVANCE_INTERVAL = 1
AMBULANCE_SCHEDULE_CHANCE = 50
description_options = [
    "CPR in progres",
    "difficulty breathing",
    "MVC"
]
available_ambulance_ids = {
    "BLS": list(range(600, 700)) + list(range(702, 800)) + list(range(800, 1000)) + list(range(1001, 2501)) + list(
        range(3000, 3401)),
    "MICU": list(range(11, 501))
}

active_ambulances = {
    "BLS": list(),
    "MICU": list()
}


def random_time():
    return random.randint(1 if DEV else 3, 2 if DEV else 45)


def dequeue_ambulance(a_type="BLS"):
    if not available_ambulance_ids[a_type]:
        raise ValueError(f"Cannot dequeue ambulance, All {a_type} ambulance on schedule")
    a_id = random.choice(available_ambulance_ids[a_type])
    active_ambulances[a_type].append(a_id)
    available_ambulance_ids[a_type].remove(a_id)
    a_desc = random.choice(description_options)
    ambulance = Ambulance(id=a_id, a_type=a_type, time_till_arrival=random_time(), desc=a_desc)

    return ambulance


def enqueue_ambulance(amb: Ambulance):
    active_ambulances[amb.a_type].remove(amb.id)
    available_ambulance_ids[amb.a_type].append(amb.id)


@socketio.on("receive_updates")
def on_receive_updates():
    print("Client registered on receive_updates")
    join_room(AMBULANCE_UPDATES_ROOM)


@app.post("/post_ambulance")
def post_ambulance():
    binary_data = request.get_data()  # this gives you the raw bytes
    decrypted = crypto_utils.decrypt_message(binary_data)
    jso = json.loads(decrypted)
    ambulance = jso["ambulance"]
    description = jso["description"]
    a_type = ambulance["type"]
    a_code = ambulance["code"]
    if a_code in available_ambulance_ids[a_type]:
        available_ambulance_ids[a_type].remove(a_code)
        active_ambulances[a_type].append(a_code)
        ambulance = Ambulance(id=a_code, a_type=a_type, time_till_arrival=random_time(), desc=description)
        manager.add_ambulance(ambulance)

    return 'OK', 200


class AmbulanceUpdateRequest(BaseModel):
    a_type: str
    a_code: int


@app.route("/ambulance_info", methods=["POST"])
def ambulance_info():
    try:
        data = request.get_json()
        req = AmbulanceUpdateRequest(**data)  # ✅ manually parse using Pydantic

        if req.a_code not in active_ambulances.get(req.a_type, []):
            print("Invalid ambulance from target")
            return jsonify({"message": "Invalid ambulance"}), 400

        # Simulate response
        return AmbulanceManager.dump_single_ambulance(manager.ambulances[req.a_code]), 200

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422


@socketio.on("stop_receive_updates")
def on_stop_receive_updates():
    print("Client unregistered on receive_updates")
    leave_room(AMBULANCE_UPDATES_ROOM)


class AmbulanceManager:
    def __init__(self, initial_ambulances):
        self.ambulances = initial_ambulances

    @staticmethod
    def dump_single_ambulance(ambulance):
        return crypto_utils.encrypt_message(json.dumps({
            "arrival_time": ambulance.time_till_arrival,
            "type": ambulance.a_type,
            "description": ambulance.desc
        }))

    def dump_ambulance_data(self):
        return crypto_utils.encrypt_message(json.dumps({
            ambulance.id: {
                "arrival_time": ambulance.time_till_arrival,
                "type": ambulance.a_type,
                "description": ambulance.desc
            }
            for ambulance in self.ambulances.values()
        }))

    def add_ambulance(self, a: Ambulance):
        self.ambulances[a.id] = a

    def remove_ambulance(self, a: Ambulance):
        del self.ambulances[a.id]

    def advance_ambulance(self, id: str, by=1):
        self.ambulances[id].advance_time(by)

    def update_ambulance_time(self, id: str, time=1):
        self.ambulances[id].update_time(time)


manager = AmbulanceManager({})


def advance_ambulances():
    print("Advancing Ambulances")
    for a_type, ambulances in active_ambulances.items():
        for amb_id in ambulances:
            manager.advance_ambulance(amb_id)


def ambulance_pullback(ambulance: Ambulance):
    print("ambulance_pullback")
    # remove from manager's active ambulances
    manager.remove_ambulance(ambulance)
    # put back in the available queue
    enqueue_ambulance(ambulance)


def schedule_ambulance(a_type: str):
    amb = dequeue_ambulance(a_type=a_type)
    manager.add_ambulance(amb)
    from datetime import datetime, timedelta
    print(f"Scheduling pullback in: {amb.time_till_arrival} minutes")
    run_time = datetime.now() + timedelta(minutes=amb.time_till_arrival)
    # ambulance pullback action
    scheduler.add_job(
        func=ambulance_pullback,
        trigger='date',  # One-shot execution
        run_date=run_time,  # Exact time to run
        args=[amb],  # Function parameters
        id=f'ambulance_pullback_{amb.id}',
        replace_existing=True
    )


def random_type_schedule_ambulance():
    if random.randint(1, 100) < AMBULANCE_SCHEDULE_CHANCE:
        a_type = random.choice(["BLS", "MICU"])
        print(f"Scheduling ambulance of type {a_type}")
        schedule_ambulance(a_type)


def send_ambulance_alert():
    print("Sending ambulance alert")
    socketio.emit(AMBULANCE_UPDATES_ROOM, manager.dump_ambulance_data(), to=AMBULANCE_UPDATES_ROOM)


if __name__ == "__main__":
    print("Starting the sender")
    scheduler.add_job(advance_ambulances, 'interval', minutes=AMBULANCE_ADVANCE_INTERVAL, id='advance_ambulances')
    scheduler.add_job(random_type_schedule_ambulance, 'interval', minutes=AMBULANCE_SCHEDULE_INTERVAL,
                      id='schedule_ambulances')
    scheduler.add_job(send_ambulance_alert, 'interval', minutes=0.05, id='send_ambulance_alert')
    scheduler.start()
    random_type_schedule_ambulance()
    import os

    if DEV:
        app.run(host='localhost', port=5003)
    else:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

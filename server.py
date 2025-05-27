import json
import random
from flask import Flask, request
from crypto_utils import encrypt_message, decrypt_message
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from ambulance import Ambulance
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
socketio = SocketIO(app, debug=True, cors_allowed_origins='*')
scheduler = BackgroundScheduler()
AMBULANCE_UPDATES_ROOM = "ambulance_updates"
AMBULANCE_SCHEDULE_INTERVAL = 0.05
AMBULANCE_SCHEDULE_CHANCE = 20

available_ambulance_ids = {
    "BLS": list(range(600, 700)) + list(range(702, 800)) + list(range(800, 1000)) + list(range(1001, 2501)) + list(
        range(3000, 3401)),
    "MICU": list(range(11, 501))
}

active_ambulances = {
    "BLS": list(),
    "MICU": list()
}


def dequeue_ambulance(a_type="BLS"):
    if not available_ambulance_ids[a_type]:
        raise ValueError(f"Cannot dequeue ambulance, All {a_type} ambulance on schedule")
    a_id = random.choice(available_ambulance_ids[a_type])
    active_ambulances[a_type].append(a_id)
    available_ambulance_ids[a_type].remove(a_id)
    ambulance = Ambulance(id=a_id, a_type=a_type, time_till_arrival=30)

    return ambulance


@socketio.on("receive_updates")
def on_receive_updates():
    print("Client registered on receive_updates")
    join_room(AMBULANCE_UPDATES_ROOM)


@socketio.on("stop_receive_updates")
def on_stop_receive_updates():
    print("Client unregistered on receive_updates")
    leave_room(AMBULANCE_UPDATES_ROOM)


class AmbulanceManager:
    def __init__(self, initial_ambulances):
        self.ambulances = initial_ambulances

    def dump_ambulance_data(self):
        return json.dumps({
            ambulance.id: {
                "arrival_time": ambulance.time_till_arrival,
                "type": ambulance.a_type
            }
            for ambulance in self.ambulances.values()
        })

    def add_ambulance(self, a: Ambulance):
        self.ambulances[a.id] = a

    def advance_ambulance(self, id: str, by=1):
        self.ambulances[id].advance_time(by)

    def update_ambulance_time(self, id: str, time=1):
        self.ambulances[id].update_time(time)


manager = AmbulanceManager({})

manager.add_ambulance(dequeue_ambulance())


def advance_ambulances():
    print("Advancing Ambulances")
    random_type = random.choice(["BLS", "MICU"])
    if not active_ambulances[random_type]:
        return
    ambulance_id = random.choice(active_ambulances[random_type])
    if random.randint(1, 100) < 50:
        manager.advance_ambulance(ambulance_id)


def schedule_ambulance():
    if random.randint(1, 100) < AMBULANCE_SCHEDULE_CHANCE:
        a_type = random.choice(["BLS", "MICU"])
        print(f"Scheduling ambulance of type {a_type}")
        manager.add_ambulance(dequeue_ambulance(a_type=a_type))


def send_ambulance_alert():
    print("Sending ambulance alert")
    socketio.emit(AMBULANCE_UPDATES_ROOM, manager.dump_ambulance_data(), to=AMBULANCE_UPDATES_ROOM)


if __name__ == "__main__":
    print("Starting the sender")
    scheduler.add_job(advance_ambulances, 'interval', minutes=0.2, id='advance_ambulances')
    scheduler.add_job(schedule_ambulance, 'interval', minutes=AMBULANCE_SCHEDULE_INTERVAL, id='schedule_ambulances')
    scheduler.add_job(send_ambulance_alert, 'interval', minutes=0.1, id='send_ambulance_alert')
    scheduler.start()
    app.run(port=5003)

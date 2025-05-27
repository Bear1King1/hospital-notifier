import json
from ambulance import Ambulance
import requests
from crypto_utils import encrypt_message
import tkinter as tk
import socketio
import threading

RECEIVER_SERVER_URL = 'http://localhost:5003/chosen'
sio = socketio.Client()

# Create the main application window
app = tk.Tk()
app.title("Server Data Display")
app.geometry("600x200")

container = tk.Frame(app)
container.pack(expand=True)

ambulances = {}
GRID_DIM = 4


class AmbulanceUI(Ambulance):
    ambulances_count = -1

    def __init__(self, id: str, card: tk.Frame, label: tk.Label, time_till_arrival: int = 0, a_type: str = "BLS"):
        super().__init__(id=id, time_till_arrival=time_till_arrival, a_type=a_type)
        AmbulanceUI.ambulances_count += 1
        self.ord = AmbulanceUI.ambulances_count
        self.card = card
        self.label = label

    def update_time(self, t: int):
        super().update_time(t)
        self.label.config(text=f"Ambulance {self.id} arriving in {self.time_till_arrival} minutes")

    @staticmethod
    def create_ambulance(id: str, time_arrival: int = 0, a_type:str = "BLS"):
        wrapper = tk.Frame(container, width=130, height=110)
        wrapper.pack_propagate(False)
        shadow = tk.Frame(wrapper, bg="#888888", width=120, height=100)
        shadow.place(x=5, y=5)
        card = tk.Frame(wrapper, bg="white", width=120, height=100, highlightthickness=1,
                        highlightbackground="#cccccc")
        card.place(x=0, y=0)
        label_l = tk.Label(card, text=id, bg="white", fg="black", font=("Arial", 12), wraplength=100,
                           justify="center")
        label_l.place(relx=0.5, rely=0.5, anchor="center")
        am = AmbulanceUI(label=label_l, card=wrapper, id=id, time_till_arrival=time_arrival,a_type=a_type)
        wrapper.grid(row=am.ord // GRID_DIM, column=am.ord % GRID_DIM, padx=10)
        ambulances[id] = am
        return am


# Socket.IO event handlers
@sio.event
def connect():
    print("Connected to server")
    sio.emit("receive_updates")


@sio.event
def disconnect():
    print("Disconnected from server")
    sio.emit("stop_receive_updates")


def update_ambulances(data: dict):
    ordered = sorted(data.items(), key=lambda am: am[1]["arrival_time"])
    for (am_id, a_data) in ordered:
        if am_id not in ambulances:
            AmbulanceUI.create_ambulance(am_id, a_data["arrival_time"], a_data["type"])
        else:
            ambulances[am_id].update_time(a_data["arrival_time"])


@sio.on('ambulance_updates')
def on_status_update(data):
    print("Received data from server:", data)

    # Safely update the UI using app.after
    def update_ui():
        ambulance_details = json.loads(data)
        update_ambulances(data=ambulance_details)

    app.after(0, update_ui)


# Thread for running the socket client
def receive_messages():
    try:
        sio.connect('http://localhost:5003')  # Change port as needed
        sio.wait()
    except Exception as e:
        print("Socket connection failed:", e)


# Start Socket.IO client in a thread
threading.Thread(target=receive_messages, daemon=True).start()

# Start the main Tkinter event loop
app.mainloop()

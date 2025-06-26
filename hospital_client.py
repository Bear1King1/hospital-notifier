import json
from ambulance import Ambulance
import requests
import crypto_utils
import tkinter as tk
import socketio
import threading

DEV = False

RECEIVER_SERVER_URL = 'http://localhost:5003/chosen' if DEV else "https://ambulance-server-9ff3.onrender.com/chosen"
SENDER_SERVER_URL = 'http://localhost:5003/ambulance_info' if DEV else "https://ambulance-server-9ff3.onrender.com/ambulance_info"
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

    def __init__(self, id: str, card: tk.Frame, label: tk.Label, time_till_arrival: int = 0, a_type: str = "BLS",
                 desc: str = ""):
        super().__init__(id=id, time_till_arrival=time_till_arrival, a_type=a_type, desc=desc)
        AmbulanceUI.ambulances_count += 1
        self.ord = AmbulanceUI.ambulances_count
        self.arrived = False
        self.card = card
        self.label = label

    def update_time(self, t: int):
        super().update_time(t)
        if self.arrived:
            return
        desc = f"\nDescription: {self.desc}" if self.desc else ""
        if t == 0:
            self.arrived = True
            self.label.config(text=f"Ambulance {self.id} Arrived {desc}")

            def remove_ambulance():
                self.card.destroy()
                AmbulanceUI.ambulances_count -= 1
                del ambulances[self.id]

            app.after(1000 * 30, remove_ambulance)
            return
        self.label.config(text=f"Ambulance {self.id} arriving in {self.time_till_arrival} minutes {desc}")

    @staticmethod
    def create_ambulance(id: str, time_arrival: int = 0, a_type: str = "BLS", desc: str = ""):
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
        am = AmbulanceUI(label=label_l, card=wrapper, id=id, time_till_arrival=time_arrival, a_type=a_type, desc=desc)
        am.update_time(time_arrival)
        wrapper.grid(row=am.ord // GRID_DIM, column=am.ord % GRID_DIM, padx=10)

        # Add click event
        def on_click(event):
            print("clicked label")
            request_ambulance_update(am)

        label_l.bind("<Button-1>", on_click)
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


def request_ambulance_update(ambulance: AmbulanceUI):
    try:
        response = requests.post(
            SENDER_SERVER_URL,
            json={"a_code": ambulance.id, "a_type": ambulance.a_type},
        )
        print("recevied response")
        # Access the raw bytes
        encrypted_bytes = response.content  # or response.raw.read()
        # Now decrypt it
        decrypted_json = crypto_utils.decrypt_message(encrypted_bytes)
        # If it's a JSON string, parse it
        ambulance_data = json.loads(decrypted_json)
        ambulance.desc = ambulance_data["description"]
        ambulance.update_time(ambulance_data["arrival_time"])
        print(f"Manually updated ambulance {ambulance.id}")
    except Exception as e:
        print(e)
        print("Problem manually updating ambulance", e)


def update_ambulances(data: dict):
    ordered = sorted(data.items(), key=lambda am: am[1]["arrival_time"])
    for (am_id, a_data) in ordered:
        if am_id not in ambulances:
            AmbulanceUI.create_ambulance(am_id, a_data["arrival_time"], a_data["type"], a_data["description"])
        else:
            ambulances[am_id].update_time(a_data["arrival_time"])


@sio.on('ambulance_updates')
def on_status_update(data):
    print("Received raw-data from server:", data)
    data = crypto_utils.decrypt_message(data)
    print("Received data from server:", data)

    # Safely update the UI using app.after
    def update_ui():
        ambulance_details = json.loads(data)
        update_ambulances(data=ambulance_details)

    app.after(0, update_ui)


# Thread for running the socket client
def receive_messages():
    try:
        host = "http://localhost:5003" if DEV else 'https://ambulance-server-9ff3.onrender.com'
        sio.connect(host)  # Change port as needed
        sio.wait()
    except Exception as e:
        print("Socket connection failed:", e)


# Start Socket.IO client in a thread
threading.Thread(target=receive_messages, daemon=True).start()

# Start the main Tkinter event loop
app.mainloop()

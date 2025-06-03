import json
import random

import requests
from crypto_utils import encrypt_message
import tkinter as tk
from tkinter import ttk

SENDER_SERVER_URL = 'http://127.0.0.1:5003/post_ambulance'

options = [
    "CPR in progres",
    "difficulty breathing",
    "MVC"
]
ambulance = {"type": "MICU", "code": 375}
selected_option = None


def random_time():
    return random.randint(3, 45)


def send_ambulance_message():
    if not selected_option:
        return
    message = {
        "ambulance": ambulance,
        "description": selected_option
    }
    response = requests.post(
        SENDER_SERVER_URL,
        data=encrypt_message(json.dumps(message)),
        headers={'Content-Type': 'application/octet-stream'}
    )


def submit():
    send_ambulance_message()


def on_selection(event):
    global selected_option
    selected_option = combo_var.get()
    selected_label.config(text=f"Selected: {selected_option}")


# Create the main app window
app = tk.Tk()
app.title("Urgency Selector")
app.geometry("300x200")

# Frame for layout
frm = ttk.Frame(app, padding=10)
frm.pack(fill=tk.BOTH, expand=True)

# Label
ttk.Label(frm, text="Choose an option:").pack(pady=(0, 5))

# Combobox options
combo_var = tk.StringVar()
combo = ttk.Combobox(frm, textvariable=combo_var, values=options, state="readonly")
combo.pack()

# Bind selection event to update label
combo.bind("<<ComboboxSelected>>", on_selection)

# Submit Button
submit_btn = ttk.Button(frm, text="Submit", command=submit)
submit_btn.pack(pady=10)

# Label to show selected value
selected_label = ttk.Label(frm, text="Selected: None")
selected_label.pack()

# Start GUI loop
app.mainloop()

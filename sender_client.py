import requests
from crypto_utils import encrypt_message
import tkinter as tk
from tkinter import ttk

SENDER_SERVER_URL = 'http://localhost:5002/submit'


def submit():
    urgency_choice = str_var.get()
    if urgency_choice:
        encrypted_data = encrypt_message(urgency_choice)
        response = requests.post(SENDER_SERVER_URL, data=encrypted_data)


app = tk.Tk()
frm = ttk.Frame(app, padding=10)
frm.grid()
ttk.Label(app, text="Choose option: ").grid(column=0, row=0)
options = ["a", "b", "c"]
str_var = tk.StringVar()
for i, option in enumerate(options):
    tk.Radiobutton(app, text=option, value=option, variable=str_var).grid(column=1, row=i)

tk.Button(app, text="Submit", command=submit).grid(column=2, row=0)
app.mainloop()

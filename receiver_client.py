import requests
from crypto_utils import encrypt_message
import tkinter as tk
from tkinter import ttk

RECEIVER_SERVER_URL = 'http://localhost:5003/chosen'


def update():
    try:
        response = requests.get(RECEIVER_SERVER_URL)
        label.config(text=response.text)
    except Exception as e:
        label.config(text=f"Error: {str(e)}")
    finally:
        # Schedule the next update
        app.after(1000, update)


# Create the main application window
app = tk.Tk()
app.title("Server Data Display")

# Create and configure the frame
frm = ttk.Frame(app, padding=10)
frm.grid(padx=5, pady=5)

# Create and configure the label with appropriate size
label = ttk.Label(frm, text="Waiting for data...")
label.grid(column=0, row=0, padx=10, pady=10)

# Start the update cycle
app.after(1000, update)  # First update after a short delay

# Start the main event loop
app.mainloop()

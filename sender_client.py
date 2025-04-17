import requests
from crypto_utils import encrypt_message

SENDER_SERVER_URL = 'http://localhost:5002/submit'

def submit():
    urgency_choice = options.get()
    if urgency_choice:
        encrypted_data = encrypt_message(urgency_choice)
        response = requests.post(SENDER_SERVER_URL, data=encrypted_data)
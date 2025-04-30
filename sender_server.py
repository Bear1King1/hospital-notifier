import requests
from flask import Flask, request
from crypto_utils import encrypt_message, decrypt_message

app = Flask(__name__)

RECEIVER_SERVER_URL = 'http://localhost:5003/receive'


@app.route("/submit", methods=["POST"])
def handle_submit():
    encrypted_data = request.data
    decrypted_data = decrypt_message(encrypted_data)
    print(decrypted_data)

    requests.post(RECEIVER_SERVER_URL, data=encrypted_data)
    return "OK", 200


if __name__ == "__main__":
    app.run(port=5002)

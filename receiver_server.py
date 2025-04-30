import requests
from flask import Flask, request
from crypto_utils import encrypt_message, decrypt_message

app = Flask(__name__)

decrypted_data = ""


@app.route("/receive", methods=["POST"])
def handle_receive():
    global decrypted_data
    encrypted_data = request.data
    decrypted_data = decrypt_message(encrypted_data)
    print(decrypted_data)

    return "OK", 200


@app.route("/chosen", methods=["GET"])
def handle_chosen():
    return decrypted_data


if __name__ == "__main__":
    app.run(port=5003)

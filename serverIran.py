import os
import sys

import requests
from flask import Flask, send_file, request, jsonify
from cryptography.fernet import Fernet

KEY = b'Hl5Py6FTVNRPtTRtWkNOWwO9l_17B9SqOM-3_b3feOw='
app = Flask(__name__)
cipher = Fernet(KEY)


@app.route("/get_from_europe", methods=["POST"])
def get_from_europe():
    if request.method == "POST":
        user_id, file = request.form.get("user_id"), request.form.get("file")
        r = requests.get(f"http://127.0.0.1:5000/api/{user_id}/{file}")
        try:
            os.mkdir(user_id)
        except FileExistsError:
            pass
        except Exception as e:
            print(e, file=sys.stderr)
        with open(f"{user_id}/{file}", 'wb') as f:
            f.write(r.content)
        return jsonify({"success": True})


@app.route("/download/<encrypted_path>")
def download(encrypted_path):
    file_path = cipher.decrypt(encrypted_path).decode()
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(port=8000)

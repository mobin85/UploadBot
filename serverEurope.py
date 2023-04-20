from flask import Flask, send_file
import os

app = Flask(__name__)


@app.route("/api/<user_id>/<file>")
def send(user_id, file):
    if os.path.exists(f := os.path.join("downloads", user_id, file)):
        return send_file(f, as_attachment=True)
    return "There Was An Error!"


if __name__ == '__main__':
    app.run(debug=True)


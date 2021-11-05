from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Server and Bot are Up and Running. Dev: Shaqalito#2110"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()

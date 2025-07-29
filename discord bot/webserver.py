from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def index():
    return 'hello from flask'

def run():
    app.run(host='0.0.0.0', port=8000)

def keepalive():
    server = Thread(target=run)
    server.start

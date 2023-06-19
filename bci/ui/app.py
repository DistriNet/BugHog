import logging
import logging.handlers
import os

from flask import Flask, send_from_directory
from flask_socketio import SocketIO

from bci.ui.blueprints.api import api


app = Flask(__name__)
app.register_blueprint(api)
socketio = SocketIO(app)

# We don't store anything sensitive in the session, so we can use a simple secret key
app.secret_key = 'secret_key'


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('frontend', 'dist/index.html')


@app.route('/<path:file_path>', methods=['GET'])
def serve_static_files(file_path):
    path = os.path.join('dist', file_path)
    return send_from_directory('frontend', path)


if __name__ == "__main__":
    # Configure flask logger
    filer_handler = logging.handlers.RotatingFileHandler("/app/logs/flask.log", mode='a', backupCount=2)
    filer_handler.setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').addHandler(filer_handler)

    # Debug is set to false because it would otherwise auto-reload (run the program twice)
    socketio.run(app, debug=False, host="0.0.0.0")

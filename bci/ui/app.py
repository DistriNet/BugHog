import logging
import logging.handlers
import os

from flask import Flask, send_from_directory

from bci.ui.blueprints.api import api


app = Flask(__name__)


def create_app():
    app.register_blueprint(api)
    # We don't store anything sensitive in the session, so we can use a simple secret key
    app.secret_key = 'secret_key'
    return app


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('frontend', 'dist/index.html')


@app.route('/<path:file_path>', methods=['GET'])
def serve_static_files(file_path):
    path = os.path.join('dist', file_path)
    return send_from_directory('frontend', path)


if __name__ == '__main__':
    # Used when running in devcontainer
    app = create_app()
    app.run(debug=False, host='0.0.0.0')

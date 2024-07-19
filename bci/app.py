import signal

from flask import Flask
from flask_sock import Sock

from bci.main import Main as bci_api

sock = Sock()

def create_app():
    bci_api.initialize()

    # Blueprint modules are only imported after loggers are configured
    from bci.web.blueprints.api import api
    from bci.web.blueprints.experiments import exp

    app = Flask(__name__)
    # We don't store anything sensitive in the session, so we can use a simple secret key
    app.secret_key = 'secret_key'

    app.register_blueprint(api)
    app.register_blueprint(exp)
    sock.init_app(app)

    # Configure signal handlers
    signal.signal(signal.SIGTERM, bci_api.sigint_handler)
    signal.signal(signal.SIGINT, bci_api.sigint_handler)

    return app


if __name__ == '__main__':
    # Used when running in devcontainer
    app = create_app()
    app.run(debug=False, host='0.0.0.0')

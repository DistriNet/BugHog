import signal

from flask import Flask
from flask_sock import Sock

from bci.configuration import Global, Loggers
from bci.main import Main

sock = Sock()


def create_app():
    Loggers.configure_loggers()

    if not Global.check_required_env_parameters():
        raise Exception('Not all required environment variables are available')

    # Instantiate main object and add to global flask context
    main = Main()

    # Blueprint modules are only imported after loggers are configured
    from bci.web.blueprints.api import api
    from bci.web.blueprints.experiments import exp
    from bci.web.blueprints.test import test

    app = Flask(__name__)
    # We don't store anything sensitive in the session, so we can use a simple secret key
    app.config['main'] = main
    app.secret_key = 'secret_key'

    app.register_blueprint(api)
    app.register_blueprint(exp)
    app.register_blueprint(test)
    sock.init_app(app)

    # Configure signal handlers
    signal.signal(signal.SIGTERM, main.sigint_handler)
    signal.signal(signal.SIGINT, main.sigint_handler)

    return app


if __name__ == '__main__':
    # Used when running in devcontainer
    app = create_app()
    app.run(debug=False, host='0.0.0.0')

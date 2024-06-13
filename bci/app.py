from flask import Flask

from bci.web.blueprints.api import api
from bci.web.blueprints.experiments import exp

app = Flask(__name__)


def create_app():
    app.register_blueprint(api)
    app.register_blueprint(exp)
    # We don't store anything sensitive in the session, so we can use a simple secret key
    app.secret_key = 'secret_key'
    return app


if __name__ == '__main__':
    # Used when running in devcontainer
    app = create_app()
    app.run(debug=False, host='0.0.0.0')

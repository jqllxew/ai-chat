import os
import sys

if not os.path.exists('config.yaml'):
    print("[ERROR] config.yaml file not found")
    sys.exit()

from flask import Flask
from route.qq import qq_api
from route.test import test_api

server = Flask(__name__)
server.register_blueprint(qq_api)
server.register_blueprint(test_api)


@server.route('/', methods=['GET'])
def index():
    return f"<h1>AI-chat<h1/>"


if __name__ == '__main__':
    server.run(port=7666, host='0.0.0.0')

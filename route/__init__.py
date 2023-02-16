from flask import Flask
from .qq import qq_api
from .test import test_api
from .wx import wx_api

server = Flask(__name__)
server.register_blueprint(qq_api)
server.register_blueprint(test_api)
server.register_blueprint(wx_api)


@server.route('/', methods=['GET'])
def index():
    return f"<h1>AI-chat<h1/>"


__all__ = ["server"]

from flask import Flask

from logger import handler
from .qq import qq_api
from .test import test_api
from .wx import wx_api

server = Flask(__name__)

server.register_blueprint(qq_api)
server.register_blueprint(test_api)
server.register_blueprint(wx_api)

server.logger.handlers = []
server.logger.addHandler(handler)


@server.route('/', methods=['GET'])
def index():
    return """<h1>AI-chat<h1/>
    <input id='file' type='file'></input>
    """


__all__ = ["server"]

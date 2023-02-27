import os
import sys
if not os.path.exists('config.yaml') \
        and not os.path.exists('config_example.yaml'):
    print("[ERROR] config.yaml file not found")
    sys.exit()
from config import server as server_conf, display
from route import server
from waitress import serve

if __name__ == '__main__':
    port = display(server_conf['port'])
    if port is None:
        port = 7666
    serve(app=server, port=port, host='0.0.0.0')

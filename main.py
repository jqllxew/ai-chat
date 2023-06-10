import argparse
import ctypes
import os
import sys
if not os.path.exists('config.yaml') \
        and not os.path.exists('config_example.yaml'):
    print("[ERROR] config.yaml file not found")
    sys.exit()
from config import server as server_conf, display
from route import server

if __name__ == '__main__':
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=None, help='端口')
    parser.add_argument('--waitress', action='store_true', help='waitress启动')
    opts = parser.parse_args()
    port = opts.port or display(server_conf['port'])
    if port is None:
        port = 7666
    if opts.waitress:
        from waitress import serve

        serve(app=server, port=port, host='0.0.0.0')
    else:
        server.run(port=port, host='0.0.0.0')
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

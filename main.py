import os
import sys

if not os.path.exists('config.yaml') \
        and not os.path.exists('config_example.yaml'):
    print("[ERROR] config.yaml file not found")
    sys.exit()

if __name__ == '__main__':
    from config import port
    from route import server
    if port is None:
        port = 7666
    server.run(port=port, host='0.0.0.0')

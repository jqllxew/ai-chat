import os
import sys

if not os.path.exists('config.yaml'):
    print("[ERROR] config.yaml file not found")
    sys.exit()

if __name__ == '__main__':
    from route import server
    server.run(port=7666, host='0.0.0.0')

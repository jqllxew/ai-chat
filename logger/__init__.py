import logging
from config import server as server_conf, display


class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置不同级别日志对应的颜色
        self._colors = {
            logging.DEBUG: '\033[1;34m',
            logging.INFO: '\033[1;32m',
            logging.WARNING: '\033[1;33m',
            logging.ERROR: '\033[1;31m',
            logging.CRITICAL: '\033[1;35m'
        }

    def format(self, record):
        # 添加颜色
        color = self._colors.get(record.levelno, '')
        message = super().format(record)
        return color + message + '\033[0m'


formatter = ColoredFormatter(
    fmt='[%(asctime)s]-[%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
log_level = display(server_conf['log-level'])
logger.setLevel(logging.getLevelName(log_level) if log_level else logging.INFO)

__all__ = ["logger", "handler"]

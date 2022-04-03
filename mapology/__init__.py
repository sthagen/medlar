import logging
import os
import pathlib
from typing import no_type_check

APP_ALIAS = 'mapology'
APP_ENV = APP_ALIAS.upper()
DEBUG = bool(os.getenv(f'{APP_ENV}_DEBUG', ''))
log = logging.getLogger()  # Temporary refactoring: module level logger
LOG_FOLDER = pathlib.Path('logs')
LOG_FILE = f'{APP_ALIAS}.log'
LOG_PATH = pathlib.Path(LOG_FOLDER, LOG_FILE) if LOG_FOLDER.is_dir() else pathlib.Path(LOG_FILE)
LOG_LEVEL = logging.INFO


@no_type_check
def init_logger(name=None, level=None):
    """Initialize module level logger"""
    global log  # pylint: disable=global-statement

    log_format = {
        'format': '%(asctime)s.%(msecs)03d %(levelname)s [%(name)s]: %(message)s',
        'datefmt': '%Y-%m-%dT%H:%M:%S',
        # 'filename': LOG_PATH,
        'level': LOG_LEVEL if level is None else level,
    }
    logging.basicConfig(**log_format)
    log = logging.getLogger(APP_ENV if name is None else name)
    log.propagate = True


init_logger(name=APP_ENV, level=logging.DEBUG if DEBUG else None)

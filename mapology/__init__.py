"""The mapology control data and name dispatch."""
import logging
import os
import pathlib
from typing import no_type_check

ENCODING = 'utf-8'

COUNTRY_PAGE = os.getenv('GEO_COUNTRY_PAGE', '')
PATH_NAV = os.getenv('GEO_PATH_NAV', '')
LIB_PATH = os.getenv('GEO_LIB_PATH', '/ndb/_/leaflet')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')
FOOTER_HTML = os.getenv('GEO_FOOTER_HTML', ' ')
FS_PREFIX_PATH = os.getenv('GEO_PREFIX_PATH', 'prefix')
FS_DB_ROOT_PATH = os.getenv('GEO_DB_ROOT_PATH', 'db')

APP_ALIAS = 'mapology'
APP_ENV = APP_ALIAS.upper()
DEBUG_ENV_VAR = f'{APP_ENV}_DEBUG'
DEBUG = bool(os.getenv(DEBUG_ENV_VAR, ''))
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


def country_blurb(phrase: str) -> str:
    """Return the first word in the hope it is meaningful."""
    if COUNTRY_PAGE:
        return COUNTRY_PAGE.lower()
    return phrase.split()[0].lower()

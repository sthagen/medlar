"""Render the prefix page apps from the prefix abd prefix table stores."""
import collections
import copy
import datetime as dti
import json
import logging
import operator
import os
import pathlib
import sys
from typing import Callable, Collection, Dict, Iterator, List, Tuple, Union, no_type_check

ENCODING = 'utf-8'
THIS_YY_INT = int(dti.datetime.utcnow().strftime("%y"))

COUNTRY_PAGE = os.getenv('GEO_COUNTRY_PAGE', '')
PATH_NAV = os.getenv('GEO_PATH_NAV', '')
HOST_NAV = os.getenv('GEO_HOST_NAV', 'localhost')
AERONAUTICAL_ANNOTATIONS = os.getenv('GEO_PRIMARY_LAYER_SWITCH', 'Airports')

FS_PREFIX_PATH = os.getenv('GEO_PREFIX_PATH', 'prefix')

AIRP = 'airport'
RUNW = 'runways'
FREQ = 'frequencies'
LOCA = 'localizers'
GLID = 'glideslopes'

CC_HINT = 'CC_HINT'
City = 'City'
CITY = City.upper()
ICAO = 'ICAO'
IC_PREFIX = 'IC_PREFIX'
IC_PREFIX_ICAO = f'{IC_PREFIX}_{ICAO}'
ITEM = 'ITEM'
KIND = 'KIND'
PATH = 'PATH'
HOST = 'HOST'
ANCHOR = 'ANCHOR'
TEXT = 'TEXT'
URL = 'URL'
ZOOM = 'ZOOM'
DEFAULT_ZOOM = 16

icao = 'icao_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'
DEFAULT_OUT_PREFIX = 'prefix'

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

ATTRIBUTION = f'{KIND} {ITEM} of '

PREFIX_STORE = pathlib.Path('prefix-store.json')
PREFIX_TABLE_STORE = pathlib.Path('prefix-table-store.json')

Point = collections.namedtuple('Point', ['label', 'lat', 'lon'])

# GOOGLE_MAPS_URL = f'https://www.google.com/maps/search/?api=1&query={{lat}}%2c{{lon}}'  # Map + pin Documented
GOOGLE_MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{lat}+{lon}'  # Sat + pin Undocumented

# load html poor person template from file
with open(pathlib.Path('mapology', 'templates', 'html', 'prefix.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read().replace('AERONAUTICAL_ANNOTATIONS', AERONAUTICAL_ANNOTATIONS)


def country_page_hack(phrase: str) -> str:
    """Return the first word in the hope it is meaningful."""
    if COUNTRY_PAGE:
        return COUNTRY_PAGE.lower()
    return phrase.split()[0].lower()


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the prefix renderings."""
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print('usage: prefixes.py')
        return 2

    with open(PREFIX_STORE, 'rt', encoding=ENCODING) as source:
        prefix_store = json.load(source)

    with open(PREFIX_TABLE_STORE, 'rt', encoding=ENCODING) as source:
        prefix_table_store = json.load(source)

    prefixes = sorted(prefix_table_store.keys())
    num_prefixes = len(prefixes)
    many = num_prefixes > 10  # tenfold magic
    numbers = ('latitude', 'longitude', 'elevation')
    for current, prefix in enumerate(sorted(prefixes), start=1):
        region_name = prefix_table_store[prefix]['name']
        airports = sorted(prefix_table_store[prefix]['airports'], key=operator.itemgetter('icao'))
        html = copy.deepcopy(HTML_PAGE)  # noqa

        message = f'processing {current :>3d}/{num_prefixes} {prefix} --> ({region_name}) ...'
        if not many or not current % 10 or current == num_prefixes:
            log.info(message)

        if DEBUG:
            log.debug('%s - %s' % (prefix, region_name))
        for airport in airports:
            row = [str(cell) if key not in numbers else str(round(cell, 3)) for key, cell in airport.items()]
            if DEBUG:
                log.info('- | %s |' % (' | '.join(row)))

    return 0


sys.exit(main(sys.argv[1:]))

#! /usr/bin/env python
"""Generate index page for the rendered prefix trees."""
import collections
import json
import logging
import os
import pathlib
import sys
from typing import Collection, Dict, List, Mapping, Union, no_type_check

FeatureDict = Dict[str, Collection[str]]
PHeaderDict = Dict[str, Collection[str]]
PFeatureDict = Dict[str, Collection[str]]

ENCODING = 'utf-8'

COUNTRY_PAGE = os.getenv('GEO_COUNTRY_PAGE', '')
PATH_NAV = os.getenv('GEO_PATH_NAV', '')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')
AERONAUTICAL_ANNOTATIONS = os.getenv('GEO_PRIMARY_LAYER_SWITCH', 'Airports')

FS_PREFIX_PATH = os.getenv('GEO_PREFIX_PATH', 'prefix')
FS_DB_ROOT_PATH = os.getenv('GEO_DB_ROOT_PATH', 'db')

FS_DB_STORE_PART = 'prefix-store'
FS_DB_TABLE_PART = 'prefix-table'
FS_DB_HULLS_PART = 'prefix-hulls'

DB_ROOT = pathlib.Path(FS_DB_ROOT_PATH)
DB_FOLDER_PATHS = {
    'hulls': DB_ROOT / FS_DB_HULLS_PART,
    'store': DB_ROOT / FS_DB_STORE_PART,
    'table': DB_ROOT / FS_DB_TABLE_PART,
}

DB_INDEX_PATHS = {
    'hulls': DB_ROOT / f'{FS_DB_HULLS_PART}.json',
    'store': DB_ROOT / f'{FS_DB_STORE_PART}.json',
    'table': DB_ROOT / f'{FS_DB_TABLE_PART}.json',
}

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
ITEM = 'ITEM'
KIND = 'KIND'
PATH = 'PATH'
BASE_URL_TARGET = 'BASE_URL'
ANCHOR = 'ANCHOR'
TEXT = 'TEXT'
URL = 'URL'
ZOOM = 'ZOOM'
DEFAULT_ZOOM = 1
FOOTER_HTML = 'FOOTER_HTML'
FOOTER_HTML_CONTENT = ' '

icao = 'icao_lower'
ic_prefix_token = 'ic_prefix_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'

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
with open(pathlib.Path('mapology', 'templates', 'html', 'index.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read()


def load_db_index(kind: str) -> Mapping[str, str]:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'rt', encoding=ENCODING) as handle:
        return json.load(handle)


def dump_db_index(kind: str, data: Mapping[str, str]) -> None:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'wt', encoding=ENCODING) as handle:
        json.dump(data, handle, indent=2)


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print('usage: indexer.py')
        return 2

    store_index = load_db_index('store')
    table_index = load_db_index('table')
    hulls_index = load_db_index('hulls')

    prefixes = sorted(table_index.keys())
    row_slot_set = set(prefix[0] for prefix in prefixes)
    col_slot_set = set(prefix[1] for prefix in prefixes)
    columns = sorted(col_slot_set)
    rows = sorted(row_slot_set)

    table = {f'{k}{j}': '<td>&nbsp;</td>' for k in rows for j in columns}
    log.info('I\\C |' + ' | '.join(columns))
    for row in rows:
        log.info(row)

    regions, total_airports = 0, 0
    for prefix in store_index:
        with open(store_index[prefix], 'rt', encoding=ENCODING) as handle:
            prefix_store = json.load(handle)

        with open(table_index[prefix], 'rt', encoding=ENCODING) as handle:
            table_store = json.load(handle)

        regions += 1
        count = len(prefix_store['features'])
        total_airports += count
        region_name = table_store['name']
        table[prefix] = f'<td><a href="{prefix}/" class="nd" title="{region_name}">{count}</a></td>'

    tr_pad = 12
    sp = ' '
    th_pad = tr_pad + 2
    data_cols = [f'{sp * tr_pad}<tr>', f'{sp * th_pad}<th>I\\C</th>']
    for col in columns:
        data_cols.append(f'{sp * th_pad}<th>{col}</th>')
    data_cols.append(f'{sp * tr_pad}</tr>')

    data_rows = []
    for k in rows:
        row = [f'<tr><th>{k}</th>']
        for j in columns:
            row.append(table[f'{k}{j}'])
        row.append('\n')
        data_rows.append(''.join(row))

        html_dict = {
            ANCHOR: 'prefix/',
            PATH: PATH_NAV,
            LAT_LON: '0, 0',
            ZOOM: str(DEFAULT_ZOOM),
            BASE_URL_TARGET: BASE_URL,
            'NUMBER_REGIONS': str(regions),
            'TOTAL_AIRPORTS': str(total_airports),
            FOOTER_HTML: FOOTER_HTML_CONTENT,
            'DATA_COLS': '\n'.join(data_cols),
            'DATA_ROWS': ''.join(data_rows),
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path('prefix', 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

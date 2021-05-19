#! /usr/bin/env python
"""Generate index page for the all present ICAO prefixes."""
import collections
import copy
import functools
import json
import os
import pathlib
import sys
from typing import Callable, Collection, Dict, Iterator, List, Tuple, Union

FeatureDict = Dict[str, Collection[str]]
PHeaderDict = Dict[str, Collection[str]]
PFeatureDict = Dict[str, Collection[str]]

ENCODING = 'utf-8'

COUNTRY_PAGE = os.getenv('GEO_COUNTRY_PAGE', '')
PATH_NAV = os.getenv('GEO_PATH_NAV', '')
HOST_NAV = os.getenv('GEO_HOST_NAV', 'localhost')
AERONAUTICAL_ANNOTATIONS = os.getenv('GEO_PRIMARY_LAYER_SWITCH', 'Airports')

FS_PREFIX_PATH = os.getenv('GEO_PREFIX_PATH', 'prefix')
DERIVE_GEOJSON_NAME = 'derive'

REC_SEP = ','
STDIN_TOKEN = '-'
TRIGGER_START_OF_DATA = "csv <- 'marker_label,lat,lon"
TRIGGER_END_OF_DATA = "'"

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
HOST = 'HOST'
ANCHOR = 'ANCHOR'
TEXT = 'TEXT'
URL = 'URL'
ZOOM = 'ZOOM'
DEFAULT_ZOOM = 4

icao = 'icao_lower'
ic_prefix_token = 'ic_prefix_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'

ATTRIBUTION = f'{KIND} {ITEM} of '

PREFIX_STORE = pathlib.Path('prefix-store.json')

Point = collections.namedtuple('Point', ['label', 'lat', 'lon'])

# GOOGLE_MAPS_URL = f'https://www.google.com/maps/search/?api=1&query={{lat}}%2c{{lon}}'  # Map + pin Documented
GOOGLE_MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{lat}+{lon}'  # Sat + pin Undocumented

# load html poor person template from file
with open(pathlib.Path('mapology', 'templates', 'html', 'index.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read()

prefix_store = {}
if PREFIX_STORE.exists() and PREFIX_STORE.is_file() and PREFIX_STORE.stat().st_size:
    with open(PREFIX_STORE, 'rt', encoding=ENCODING) as handle:
        prefix_store = json.load(handle)


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 0:
        print("Usage: indexer")
        return 2

    alphabet = tuple('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    table = {f'{k}{j}': '<td>&nbsp;</td>' for k in alphabet for j in alphabet}
    regions, total_airports = 0, 0
    for ic in prefix_store:
        regions += 1
        count = len(prefix_store[ic]["features"])
        total_airports += count
        table[ic] = f'<td><a href="{ic}/" title="{ic}">{count}</a></td>'

    data_rows = []
    for k in alphabet:
        row = [f'<tr><th>{k}</th>']
        for j in alphabet:
            row.append(table[f'{k}{j}'])
        row.append('\n')
        data_rows.append(''.join(row))

        html_dict = {
            ANCHOR: f'prefix/',
            PATH: PATH_NAV,
            HOST: HOST_NAV,
            'NUMBER_REGIONS': str(regions),
            'TOTAL_AIRPORTS': str(total_airports),
            'DATA_ROWS': ''.join(data_rows),
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path('prefix', 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    return 0


sys.exit(main(sys.argv[1:]))

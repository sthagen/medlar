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
HOST_NAV = os.getenv('GEO_HOST_NAV', 'localhost:8080')
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
DEFAULT_ZOOM = 4

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

    slash = '/'
    prefixes = sorted(prefix_table_store.keys())
    num_prefixes = len(prefixes)
    many = num_prefixes > 10  # tenfold magic
    numbers = ('latitude', 'longitude', 'elevation')
    for current, prefix in enumerate(sorted(prefixes), start=1):
        region_name = prefix_table_store[prefix]['name']
        my_prefix_path = f'{DEFAULT_OUT_PREFIX}/{prefix}'
        airports = sorted(prefix_table_store[prefix]['airports'], key=operator.itemgetter('icao'))

        message = f'processing {current :>3d}/{num_prefixes} {prefix} --> ({region_name}) ...'
        if not many or not current % 10 or current == num_prefixes:
            log.info(message)

        if DEBUG:
            log.debug('%s - %s' % (prefix, region_name))
        data_rows = []
        for airport in airports:
            row = [str(cell) if key not in numbers else f'{round(cell, 3) :7.03f}' for key, cell in airport.items()]
            # monkey patching
            # ensure cycles are state with two digits zero left padded
            year, cyc = row[6].split(slash)
            row[6] = f'{year}/{int(cyc) :02d}'
            # create a link to the airport page on the ICAO cell of the airport in the table row
            # example: '<a href="AGAT/" class="nd" title="AGAT(Atoifi, Solomon Islands)">AGAT</a>'
            an_icao = row[2]
            a_name = row[8]
            row[2] = f'<a href="{an_icao}/" class="nd" title="{a_name}">{an_icao}</a>'
            if DEBUG:
                log.info('- | %s |' % (' | '.join(row)))
            data_rows.append(
                f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td>'
                f'<td class="ra">{row[3]}</td><td class="ra">{row[4]}</td><td class="ra">{row[5]}</td>'
                f'<td class="la">{row[6]}</td><td class="ra">{row[7]}</td>'
                f'<td class="la">{row[8]}</td></tr>'
            )

        min_lat, min_lon = 90, 180
        max_lat, max_lon = -90, -180
        ra_count = 0  # region_airports_count
        cc_count = 1  # HACK A DID ACK TODO: do not fix country count to wun
        for airport in airports:
            ra_count += 1
            # name has eg. "<a href='KLGA/' target='_blank' title='KLGA(La Guardia, New York, USA)'>KLGA</a>"
            # name_mix = airport['name']
            # name_mix has eg. "KLGA(La Guardia, New York, USA)'>KLGA</a>" LATER TODO
            # code, rest = name_mix.split('(', 1)
            # name = rest.split(')', 1)[0]
            # coords = airport["geometry"]["coordinates"]
            lon, lat = airport['longitude'], airport['latitude']
            min_lat = min(min_lat, lat)
            min_lon = min(min_lon, lon)
            max_lat = max(max_lat, lat)
            max_lon = max(max_lon, lon)

        prefix_lat = 0.5 * (max_lat + min_lat)
        prefix_lon = 0.5 * (max_lon + min_lon)
        bbox_disp = f"[({round(min_lat, 3) :7.03f}, {round(min_lon, 3) :7.03f}), ({round(max_lat, 3) :7.03f}, {round(max_lon, 3) :7.03f})]"
        log.debug("Identified bounding box lat, lon in %s for prefix %s" % (bbox_disp, prefix))
        log.debug((f"Set center of prefix map to lat, lon = (%f, %f) for prefix %s" % (prefix_lat, prefix_lon, prefix)))
        prefix_root = pathlib.Path(FS_PREFIX_PATH)
        map_folder = pathlib.Path(prefix_root, prefix)
        map_folder.mkdir(parents=True, exist_ok=True)
        geojson_path = str(pathlib.Path(map_folder, f'{prefix.lower()}-geo.json'))
        with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
            json.dump(prefix_store[prefix], geojson_handle, indent=2)

        html_dict = {
            ANCHOR: f'prefix/{prefix}/',
            CC_HINT: region_name,
            cc_page: region_name.split()[0].lower(),
            Cc_page: region_name.split()[0].title(),
            LAT_LON: f'{prefix_lat},{prefix_lon}',
            PATH: PATH_NAV,
            HOST: HOST_NAV,
            ZOOM: str(DEFAULT_ZOOM),
            IC_PREFIX: prefix,
            'IrealCAO': ICAO,
            'ic_prefix_lower-geo.json': f'{prefix.lower()}-geo.json',
            'REGION_AIRPORT_COUNT_DISPLAY': f'{ra_count} airport{"" if ra_count == 1 else "s"}',
            'COUNTRY_COUNT_DISPLAY': f'{cc_count} region{"" if cc_count == 1 else "s"}',
            'BBOX': f' contained in lat, lon bounding box {bbox_disp}',
            'DATA_ROWS': '\n'.join(data_rows) + '\n',
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path(my_prefix_path, 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    return 0


sys.exit(main(sys.argv[1:]))

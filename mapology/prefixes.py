"""Render the prefix page apps from the prefix abd prefix table stores."""
import collections
import copy
import datetime as dti
import functools
import json
import logging
import operator
import os
import pathlib
import sys
from typing import List, Mapping, Union, no_type_check

ENCODING = 'utf-8'
THIS_YY_INT = int(dti.datetime.utcnow().strftime('%y'))

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
IC_PREFIX_ICAO = f'{IC_PREFIX}_{ICAO}'
ITEM = 'ITEM'
KIND = 'KIND'
PATH = '/PATH'
BASE_URL_TARGET = 'BASE_URL'
ANCHOR = 'ANCHOR'
TEXT = 'TEXT'
URL = 'URL'
ZOOM = 'ZOOM'
DEFAULT_ZOOM = 4
FOOTER_HTML = 'FOOTER_HTML'
FOOTER_HTML_CONTENT = ' '

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


@no_type_check
def convex_hull(coords):
    """Executes scan to return points in counter-clockwise order that are on the convex hull (Graham)."""
    turn_left, turn_right, turn_none = 1, -1, 0  # noqa

    def compare(a, b):
        return float(a > b) - float(a < b)

    def turn(p, q, r):
        return compare((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1]), 0)

    def keep_left(hull, r):
        while len(hull) > 1 and turn(hull[-2], hull[-1], r) != turn_left:
            hull.pop()
        if not len(hull) or hull[-1] != r:
            hull.append(r)
        return hull

    points = sorted(coords)
    lower_hull = functools.reduce(keep_left, points, [])
    upper_hull = functools.reduce(keep_left, reversed(points), [])
    return lower_hull.extend(upper_hull[i] for i in range(1, len(upper_hull) - 1)) or lower_hull


ATTRIBUTION = f'{KIND} {ITEM} of '

PREFIX_STORE = pathlib.Path('prefix-store.json')
PREFIX_TABLE_STORE = pathlib.Path('prefix-table-store.json')
PREFIX_HULL_STORE = pathlib.Path('prefix-hull-store.json')

THE_HULLS = {
    'type': 'FeatureCollection',
    'name': 'Prefix Region Convex Hulls',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'features': [],
}
HULL_TEMPLATE = {
    'type': 'Feature',
    'id': '',
    'properties': {'name': ''},
    'geometry': {'type': 'Polygon', 'coordinates': []},
}

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


@no_type_check
def load_db_index(kind: str) -> Mapping[str, str]:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'rt', encoding=ENCODING) as handle:
        return json.load(handle)


def dump_db_index(kind: str, data: Mapping[str, str]) -> None:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'wt', encoding=ENCODING) as handle:
        json.dump(data, handle, indent=2)


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the prefix renderings."""
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print('usage: prefixes.py')
        return 2

    store_index = load_db_index('store')
    table_index = load_db_index('table')
    hulls_index = load_db_index('hulls')

    prefix_hull_store = copy.deepcopy(THE_HULLS)
    slash = '/'
    prefixes = sorted(store_index.keys())
    num_prefixes = len(prefixes)
    many = num_prefixes > 10  # tenfold magic
    numbers = ('latitude', 'longitude', 'elevation')
    for current, prefix in enumerate(sorted(prefixes), start=1):

        with open(store_index[prefix], 'rt', encoding=ENCODING) as handle:
            prefix_store = json.load(handle)

        with open(table_index[prefix], 'rt', encoding=ENCODING) as handle:
            table_store = json.load(handle)

        hulls_index[prefix] = str(DB_FOLDER_PATHS['hulls'] / f'{prefix}.json')

        region_name = table_store['name']
        my_prefix_path = f'{DEFAULT_OUT_PREFIX}/{prefix}'
        airports = sorted(table_store['airports'], key=operator.itemgetter('icao'))

        message = f'processing {current :>3d}/{num_prefixes} {prefix} --> ({region_name}) ...'
        if not many or not current % 10 or current == num_prefixes:
            log.info(message)

        if DEBUG:
            log.debug('%s - %s' % (prefix, region_name))
        data_rows = []
        trial_coords = []
        for airport in airports:
            trial_coords.append((airport['latitude'], airport['longitude']))
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

        prefix_hull = copy.deepcopy(HULL_TEMPLATE)
        prefix_hull['id'] = prefix
        prefix_hull['properties']['name'] = region_name  # type: ignore

        hull_coords = [[lon, lat] for lat, lon in convex_hull(trial_coords)]

        lon_min = min(lon for lon, _ in hull_coords)
        lon_max = max(lon for lon, _ in hull_coords)
        if lon_min < -120 and +120 < lon_max:
            log.info('Problematic region found (convex hull crossing the outer sign change of longitudes): %s' % prefix)
            lon_sign = tuple(+1 if lon > 0 else -1 for lon, _ in hull_coords)
            lon_neg_count = sum(-datum for datum in lon_sign if datum < 0)
            lon_pos_count = sum(datum for datum in lon_sign if datum > 0)
            if lon_pos_count and lon_neg_count:  # Does the polygon cross the longitude sign change?
                log.info('- (%d positive / %d negative) longitudes: %s' % (lon_pos_count, lon_neg_count, prefix))
                patch_me_up = lon_neg_count > lon_pos_count
                add_me = +360 if patch_me_up else -360
                if patch_me_up:
                    log.info('- patching upwards (adding 360 degrees to longitude where negative): %s' % prefix)
                    hull_coords = [[lon + add_me, lat] if lon < 0 else [lon, lat] for lon, lat in hull_coords]
                else:
                    log.info('- patching downwards (adding 360 degrees to longitude where positive): %s' % prefix)
                    hull_coords = [[lon + add_me, lat] if lon > 0 else [lon, lat] for lon, lat in hull_coords]

        if prefix == 'ET':
            log.info('Patching a North-Eastern ear onto the hull: %s' % prefix)

            @no_type_check
            def et_earify(pair):
                """Monkey patch the ET region to offer an ear to select outside of ED."""
                lon_ne = 12.27  # 9333333333334,
                lat_ne = 53.91  # 8166666666664
                magic_lon = 13.648875
                magic_lat = 54.551359
                lon, lat = pair
                return [magic_lon, magic_lat] if lon > lon_ne and lat > lat_ne else [lon, lat]

            hull_coords = [et_earify(pair) for pair in hull_coords]

        prefix_hull['geometry']['coordinates'].append(hull_coords)  # type: ignore
        prefix_hull_store['features'].append(copy.deepcopy(prefix_hull))  # type: ignore
        # problem regions A1, NZ, NF, PA, UH,

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
        bbox_disp = f'[({", ".join(f"{round(v, 3) :7.03f}" for v in (min_lat, min_lon,max_lat, max_lon))}]'
        log.debug('Identified bounding box lat, lon in %s for prefix %s' % (bbox_disp, prefix))
        log.debug(('Set center of prefix map to lat, lon = (%f, %f) for prefix %s' % (prefix_lat, prefix_lon, prefix)))
        prefix_root = pathlib.Path(FS_PREFIX_PATH)
        map_folder = pathlib.Path(prefix_root, prefix)
        map_folder.mkdir(parents=True, exist_ok=True)
        geojson_path = str(pathlib.Path(map_folder, f'{prefix.lower()}-geo.json'))
        with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
            json.dump(prefix_store, geojson_handle, indent=2)

        html_dict = {
            ANCHOR: f'prefix/{prefix}/',
            CC_HINT: region_name,
            cc_page: region_name.split()[0].lower(),
            Cc_page: region_name.split()[0].title(),
            LAT_LON: f'{prefix_lat},{prefix_lon}',
            PATH: PATH_NAV,
            BASE_URL_TARGET: BASE_URL,
            ZOOM: str(DEFAULT_ZOOM),
            IC_PREFIX: prefix,
            'IrealCAO': ICAO,
            'ic_prefix_lower-geo.json': f'{prefix.lower()}-geo.json',
            'REGION_AIRPORT_COUNT_DISPLAY': f'{ra_count} airport{"" if ra_count == 1 else "s"}',
            'COUNTRY_COUNT_DISPLAY': f'{cc_count} region{"" if cc_count == 1 else "s"}',
            'BBOX': f' contained in lat, lon bounding box {bbox_disp}',
            FOOTER_HTML: FOOTER_HTML_CONTENT,
            'DATA_ROWS': '\n'.join(data_rows) + '\n',
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path(my_prefix_path, 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

        with open(hulls_index[prefix], 'wt', encoding=ENCODING) as handle:
            json.dump(prefix_hull, handle, indent=2)

    dump_db_index('hulls', hulls_index)

    with open(pathlib.Path(FS_PREFIX_PATH) / 'region-hulls-geo.json', 'wt', encoding=ENCODING) as handle:
        json.dump(prefix_hull_store, handle, indent=2)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

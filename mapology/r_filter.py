#! /usr/bin/env python
"""Transform the R airport script data portion into a leaflet geojson file.
Constructing the City hints:
$ grep airport_name ????/index.json | tr "a-z" "A-Z" | \
  sed "s/$ESC$/INDEX$ESC$.JSON://g; s/AIRPORT_NAME//g;" | tr -d " " | tr -s '"' | sed s/^/'"'/g
Valid Google Maps query GET URLs (official with map and pin - but no satellite):
https://www.google.com/maps/search/?api=1&query={lat}%2c{lon}
Old unofficial but as of 2020-11-04 still working satellite and pin:
https://maps.google.com/maps?t=k&q=loc:{lat}+{lon}
"""
import collections
import copy
import datetime as dti
import functools
import json
import logging
import os
import pathlib
import sys
from typing import Callable, Collection, Dict, Iterator, List, Tuple, Union, no_type_check

FeatureDict = Dict[str, Collection[str]]
PHeaderDict = Dict[str, Collection[str]]
PFeatureDict = Dict[str, Collection[str]]

ENCODING = 'utf-8'
THIS_YY_INT = int(dti.datetime.utcnow().strftime("%y"))

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
with open(pathlib.Path('mapology', 'templates', 'html', 'page.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read().replace('AERONAUTICAL_ANNOTATIONS', AERONAUTICAL_ANNOTATIONS)

GEO_JSON_HEADER = {
    'type': 'FeatureCollection',
    'name': f'Airport - {ICAO} ({City}, {CC_HINT})',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'features': [],
}
GEO_JSON_FEATURE: FeatureDict = {
    'type': 'Feature',
    'properties': {
        'name': f"<a href='{URL}' target='_blank' title='{KIND} {ITEM} of {ICAO}({CITY}, {CC_HINT})'>{TEXT}</a>",
    },
    'geometry': {
        'type': 'Point',
        'coordinates': [],  # Note: lon, lat
    },
}

GEO_JSON_PREFIX_HEADER: PHeaderDict = {
    'type': 'FeatureCollection',
    'name': f'Region - {IC_PREFIX} ({CC_HINT})',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'features': [],
}
GEO_JSON_PREFIX_FEATURE: PFeatureDict = {
    'type': 'Feature',
    'properties': {
        'name': f"<a href='{URL}' target='_blank' title='{KIND} {ITEM} of {ICAO}({CITY}, {CC_HINT})'>{TEXT}</a>",
    },
    'geometry': {
        'type': 'Point',
        'coordinates': [],  # Note: lon, lat
    },
}

JSON_PREFIX_TABLE_HEADER = {
    'type': 'x-prefix-table',
    'name': f'Region - {IC_PREFIX} ({CC_HINT})',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'airports': [],
}

JSON_PREFIX_TABLE_ROW = {
    'area_code': '',
    'prefix': '',
    'icao': '',
    'latitude': '',
    'longitude': '',
    'elevation': '',
    'updated': '',
    'record_number': '',
    'airport_name': '',
}

# load data like: {"prefix/00/00C/:": "ANIMAS",}
with open(pathlib.Path('prefix_airport_names_for_index.json'), 'rt', encoding=ENCODING) as handle:
    airport_path_to_name = json.load(handle)


def icao_from_key_path(text: str) -> str:
    """HACK A DID ACK"""
    return text.rstrip('/:').rsplit('/', 1)[1]


# Example: {"GCFV": "FUERTEVENTURA",}
airport_name = {icao_from_key_path(k): v for k, v in airport_path_to_name.items()}
prefix_path = {icao_from_key_path(k): k.rstrip(':') for k in airport_path_to_name}

# load data like: {"AG": "Solomon Islands",}
with open(pathlib.Path('icao_prefix_to_country_name.json'), 'rt', encoding=ENCODING) as handle:
    flat_prefix = json.load(handle)

prefix_store = {}
if PREFIX_STORE.exists() and PREFIX_STORE.is_file() and PREFIX_STORE.stat().st_size:
    with open(PREFIX_STORE, 'rt', encoding=ENCODING) as handle:
        prefix_store = json.load(handle)

prefix_table_store = {}
if PREFIX_TABLE_STORE.exists() and PREFIX_TABLE_STORE.is_file() and PREFIX_TABLE_STORE.stat().st_size:
    with open(PREFIX_TABLE_STORE, 'rt', encoding=ENCODING) as handle:
        prefix_table_store = json.load(handle)


def derive_base_facts_path(folder: pathlib.Path, icao_identifier:str) -> pathlib.Path:
    """DRY."""
    return pathlib.Path(folder, f'airport-{icao_identifier.upper()}.json')


def derive_geojson_in_path(folder: pathlib.Path, icao_identifier: str) -> pathlib.Path:
    """DRY."""
    return pathlib.Path(folder, f'airport-{icao_identifier.upper()}.geojson')


def parse_cycle_date(cycle_date_code:str) -> list[int, int]:
    """Parse string encoded cycle date into full (YYYY, cycle number)- pair."""
    dt, cy = int(cycle_date_code[:2]), int(cycle_date_code[2:])
    dt = 1900 + dt if dt > THIS_YY_INT else 2000 + dt
    return [dt, cy]


def parse_int_or_empty(decimals:str) -> Union[int, None]:
    """Parse string encoded decimal and yield integer or None."""
    return None if not decimals.strip() else int(decimals.strip())


def parse_base_facts(folder: pathlib.Path, icao_identifier: str) -> dict[str, Union[str, float]]:
    """Some additional attributes for the airport from database parsing.

    If available will populate the table of the page:
    <th>Cust.Region</th><th>Prefix</th><th>ICAO</th><th>Latitude</th><th>Longitude</th><th>Elevation</th>
    <th>Updated</th><th>Rec#</th><th>Airport Name</th>

    and may correct the prefix semantics in the page for prefix to country mapping.
    """
    with open(derive_base_facts_path(folder, icao_identifier), "rt", encoding=ENCODING) as raw_handle:
        data = json.load(raw_handle)
    conv = data["airport_converted"]
    raw = data["airport_raw"]
    return {
        "airport_name": raw["airport_name"].strip(),
        "customer_area_code": raw["customer_area_code"].strip().upper(),  # "USA"
        "icao_code": raw["icao_code"].strip().upper(),  # "K2"
        "icao_identifier": raw["icao_identifier"].strip().upper(),  # "04CA"
        "ifr_capability": raw["ifr_capability"].strip(),  # "N"
        "longest_runway": raw["longest_runway"].strip(),  # "080"
        "longest_runway_surface_code": raw["longest_runway_surface_code"].strip(),  # " " -> ''
        "magnetic_true_indicator": raw["magnetic_true_indicator"].strip(),  # "M"
        "magnetic_variation": raw["magnetic_variation"].strip(),  # "E0140"
        "public_military_indicator": raw["public_military_indicator"].strip(),  # "P"
        "recommended_navaid": raw["recommended_navaid"].strip(),  # "    " -> ''
        "speed_limit": parse_int_or_empty(raw["speed_limit"]),  # in km/h
        "speed_limit_altitude": raw["speed_limit_altitude"].strip(),  # in feet for speed limit
        "time_zone": raw["time_zone"].strip(),  # "U00" or similarly
        "transition_level": parse_int_or_empty(raw["transition_level"]),  # in feet
        "transitions_altitude": parse_int_or_empty(raw["transitions_altitude"]),  # in feet
        "latitude": conv["latitude"],  # signed degrees as float
        "longitude": conv["longitude"],  # signed degrees as float
        "elevation": conv["elevation"],  # meters above mean sea level as float
        "record_type": raw["record_type"].strip().upper(),
        "section_code": raw["section_code"].strip().upper(),
        "subsection_code": raw["subsection_code"].strip().upper(),
        "cycle_date": parse_cycle_date(raw["cycle_date"]),  # Code "1913" -> [2019, 13]
        "file_record_number": int(raw["file_record_number"].strip()),  # Five digits wrap around counter within db
    }


def country_page_hack(phrase: str) -> str:
    """Return the first word in the hope it is meaningful."""
    if COUNTRY_PAGE:
        return COUNTRY_PAGE.lower()
    return phrase.split()[0].lower()


def read_stdin() -> Iterator[str]:
    """A simple stdin line based reader (generator)."""
    readline = sys.stdin.readline()
    while readline:
        yield readline
        readline = sys.stdin.readline()


def read_file(path: str) -> Iterator[str]:
    """A simple file line based reader (generator)."""
    with open(path, 'rt', encoding=ENCODING) as r_handle:
        for line in r_handle:
            if DEBUG:
                log.debug(line.strip())
            yield line.strip()


def is_runway(label: str) -> bool:
    """Detect if label is a runway label"""
    return label.startswith('RW') and len(label) < 7


def is_frequency(label: str) -> bool:
    """Detect if label is a frequency label"""
    return '_' in label and label.index('_') == 2 and len(label) == 10


def maybe_localizer(label: str) -> bool:
    """Detect if label is maybe a localizer label"""
    return '_' not in label and len(label) < 7


def maybe_glideslope(label: str) -> bool:
    """Detect if label is maybe a glideslope label"""
    return '_' in label and len(label) > 5 and any([label.endswith(t) for t in ('DME', 'ILS', 'TAC')])


def parse(record: str, seen: Dict[str, bool], data: Dict[str, List[Point]]) -> bool:
    """Parse the record in a context sensitive manner (seen) into data."""

    def update(aspect: str, new_point: Point) -> bool:
        """DRY."""
        if aspect not in data:
            data[aspect] = []
        data[aspect].append(new_point)
        seen[aspect] = True
        # log.debbug(data[aspect][-1])
        return True

    try:
        label, lat, lon = record.split(REC_SEP)
    except ValueError as err:
        log.warning('<<<%s>>>' % record)
        log.error(err)
        return False

    point = Point(label, lat, lon)
    if not seen[AIRP]:
        return update(AIRP, point)

    if is_frequency(label):  # ARINC424 source may provide airports without runways but with frequencies
        return update(FREQ, point)

    if is_runway(label):
        return update(RUNW, point)

    if seen[RUNW] and maybe_localizer(label):
        return update(LOCA, point)
    if seen[RUNW] and maybe_glideslope(label):
        return update(GLID, point)

    return False


def parse_data(reader: Callable[[], Iterator[str]]) -> Tuple[Dict[str, bool], Dict[str, List[Point]]]:
    """Parse the R language level data and return the entries and categories seen."""
    on = False  # The data start is within the file - not at the beginning
    seen = {k: False for k in (AIRP, RUNW, FREQ, LOCA, GLID)}
    data: Dict[str, List[Point]] = {}
    for line in reader():
        # log.debug('Read: %s' % line.strip())
        if on:
            record = line.strip().strip(TRIGGER_END_OF_DATA)
            found = parse(record, seen, data)
            if not found:
                log.warning('Unhandled ->>>>>>%s' % record)
        if not on:
            on = line.startswith(TRIGGER_START_OF_DATA)
        else:
            if line.strip().endswith(TRIGGER_END_OF_DATA):
                break
    return seen, data


def make_feature(coord_stack: Dict[Tuple[str, str], int], feature_data: List[Point], kind: str, cc: str, icao: str, apn: str) -> List[FeatureDict]:
    """DRY."""
    local_features = []
    for triplet in feature_data:
        label = triplet.label
        lat_str = triplet.lat
        lon_str = triplet.lon
        pair = (lat_str, lon_str)
        if pair in coord_stack:
            coord_stack[pair] += 2
        else:
            coord_stack[pair] = 0
        feature = copy.deepcopy(GEO_JSON_FEATURE)
        name = feature['properties']['name']  # type: ignore
        name = name.replace(ICAO, icao).replace(KIND, kind)
        name = name.replace(ITEM, label).replace(TEXT, label)
        name = name.replace(CITY, apn)
        name = name.replace(CC_HINT, cc)
        name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=float(lat_str), lon=float(lon_str)))
        if coord_stack[pair]:
            spread = '<br>' * coord_stack[pair]
            name = f'{spread}{name}'

        feature['properties']['name'] = name  # type: ignore
        feature['geometry']['coordinates'].append(float(lon_str))  # type: ignore
        feature['geometry']['coordinates'].append(float(lat_str))  # type: ignore

        local_features.append(feature)

    return local_features


def make_airport(coord_stack: Dict[Tuple[str, str], int], point: Point, cc: str, icao: str, apn: str) -> FeatureDict:
    """DRY."""
    geojson = copy.deepcopy(GEO_JSON_HEADER)
    name = geojson['name']
    name = name.replace(ICAO, icao).replace(City, apn.title())  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore
    geojson['name'] = name

    airport = copy.deepcopy(GEO_JSON_FEATURE)
    name = airport['properties']['name']  # type: ignore
    name = name.replace(ICAO, icao).replace(TEXT, icao).replace(ATTRIBUTION, '')  # type: ignore
    name = name.replace(CITY, apn.title())  # type: ignore
    name = name.replace(URL, './')  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore

    pair = (str(point.lat), str(point.lon))
    if pair in coord_stack:
        coord_stack[pair] += 2
    else:
        coord_stack[pair] = 0
    if coord_stack[pair]:
        spread = '<br>' * coord_stack[pair]
        name = f'{spread}{name}'

    airport['properties']['name'] = name  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lon))  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lat))  # type: ignore

    geojson['features'] = [airport]  # type: ignore
    return geojson


def add_prefix(icp: str, cc: str) -> PHeaderDict:
    """DRY."""
    geojson = copy.deepcopy(GEO_JSON_PREFIX_HEADER)
    name = geojson['name']
    name = name.replace(IC_PREFIX, icp).replace(CC_HINT, cc)  # type: ignore
    geojson['name'] = name
    return geojson


def add_table_prefix(icp: str, cc: str) -> PHeaderDict:
    """DRY."""
    table = copy.deepcopy(JSON_PREFIX_TABLE_HEADER)
    name = table['name']
    name = name.replace(IC_PREFIX, icp).replace(CC_HINT, cc)  # type: ignore
    table['name'] = name
    return table


def make_table_row(facts):
    row = copy.deepcopy(JSON_PREFIX_TABLE_ROW)
    row['area_code'] = facts['customer_area_code']
    row['prefix'] = facts['icao_code']
    row['icao'] = facts["icao_identifier"]
    row['latitude'] = facts['latitude']
    row['longitude'] = facts['longitude']
    row['elevation'] = facts['elevation']
    row['updated'] = f'{"/".join(str(f) for f in facts["cycle_date"])}'
    row['record_number'] = facts['file_record_number']
    row['airport_name'] = facts['airport_name']
    return row


def add_airport(point: Point, cc: str, icao: str, apn: str) -> PFeatureDict:
    """DRY."""
    airport = copy.deepcopy(GEO_JSON_PREFIX_FEATURE)
    name = airport['properties']['name']  # type: ignore
    name = name.replace(ICAO, icao).replace(TEXT, icao).replace(ATTRIBUTION, '')  # type: ignore
    name = name.replace(CITY, apn.title())  # type: ignore
    name = name.replace(URL, f'{icao}/')  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore
    airport['properties']['name'] = name  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lon))  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lat))  # type: ignore

    return airport


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print('usage: r_filter.py base/r/IC[/ICAO]')
        return 2

    slash, magic = '/', '/r/'
    bootstrap = argv[0].rstrip(slash)  # ensure it does not end with a slash
    # is now either where/ever/r or where/ever/r/CC or where/ever/r/CC/ICAO
    full = bootstrap.endswith(magic.rstrip(slash))
    cc_only = not full and slash not in bootstrap.rsplit(magic, 1)[1]
    tasks = []
    if full:
        for path in pathlib.Path(bootstrap).iterdir():
            if path.is_dir():
                for sub_path in path.iterdir():
                    if sub_path.is_dir():
                        tasks.append(str(sub_path))
    elif cc_only:
        for path in pathlib.Path(bootstrap).iterdir():
            if path.is_dir():
                tasks.append(str(path))
    else:
        tasks.append(bootstrap)

    num_tasks = len(tasks)
    many = num_tasks > 4200  # hundredfold magic
    for current, task in enumerate(sorted(tasks), start=1):
        booticao = task.rstrip(slash).rsplit(slash, 1)[1]
        r_path = f'{task}/airport-with-runways-{booticao}.r'
        r_file_name = pathlib.Path(r_path).name
        g_folder = pathlib.Path(str(pathlib.Path(r_path).parent).replace('/r/', '/geojson/'))  # HACK
        s_folder = pathlib.Path(str(pathlib.Path(r_path).parent).replace('/r/', '/json/'))  # HACK

        reader = functools.partial(read_file, r_path)
        seen, data = parse_data(reader)  # type: ignore

        runway_count = 0
        if data and AIRP in data:
            triplet = data[AIRP][0]
            root_icao, root_lat, root_lon = triplet.label.strip(), float(triplet.lat), float(triplet.lon)
            facts = parse_base_facts(s_folder, root_icao)
            s_name = facts["airport_name"]
            s_area_code = facts["customer_area_code"]
            s_prefix = facts["icao_code"]
            ic_prefix = s_prefix  # HACK A DID ACK

            message = f'processing {current :>5d}/{num_tasks} {ic_prefix}/{root_icao} --> ({s_name}) ...'
            if not many or not current % 100 or current == num_tasks:
                log.info(message)

            s_identifier = facts["icao_identifier"]
            s_lat = facts["latitude"]
            s_lon = facts["longitude"]
            s_elev = facts["elevation"]
            s_updated = f'{"/".join(str(f) for f in facts["cycle_date"])}'
            s_rec_num = facts["file_record_number"]
            geojson_path = derive_geojson_in_path(g_folder, s_identifier)

            if s_identifier not in airport_name:
                airport_name[s_identifier] = s_name

            data_row = (
                f'<tr><td>{s_area_code}</td><td>{s_prefix}</td><td>{s_identifier}</td>'
                f'<td>{s_lat}</td><td>{s_lon}</td><td>{s_elev}</td><td>{s_updated}</td><td>{s_rec_num}</td>'
                f'<td>{s_name}</td></tr>'
            )

            try:
                cc_hint = flat_prefix[ic_prefix]
            except KeyError as err:
                log.debug("Naive prefix matcher failed falling back to raw data: %s" % str(err).replace("\n", "$NL$"))
                log.debug("DETAILS: %s" % str(facts))
                cc_hint = flat_prefix.get(facts.get("icao_code", "ZZ"))

            try:
                my_prefix_path = prefix_path[root_icao]
            except KeyError as err:
                log.debug("Naive prefix path matcher failed falling back to derivation: %s" % str(err).replace("\n", "$NL$"))
                my_prefix_path = f'/prefix/{ic_prefix}/{root_icao}/'

            markers = cc_hint, root_icao, s_name

            coord_stack = {}
            geojson = make_airport(coord_stack, triplet, *markers)

            if RUNW in data:
                geojson['features'].extend(make_feature(coord_stack, data[RUNW], 'Runway', *markers))  # type: ignore
                runway_count = len(data[RUNW])  # HACK A DID ACK for zoom heuristics

            if FREQ in data:
                geojson['features'].extend(make_feature(coord_stack, data[FREQ], 'Frequency', *markers))  # type: ignore

            if LOCA in data:
                geojson['features'].extend(make_feature(coord_stack, data[LOCA], 'Localizer', *markers))  # type: ignore

            if GLID in data:
                geojson['features'].extend(make_feature(coord_stack, data[GLID], 'Glideslope', *markers))  # type: ignore

            # Process prefix store
            if ic_prefix not in prefix_store:
                # Create initial entry for ICAO prefix
                prefix_store[ic_prefix] = add_prefix(ic_prefix, cc_hint)

            # Process prefix table store
            if ic_prefix not in prefix_table_store:
                # Create initial entry for ICAO prefix
                prefix_table_store[ic_prefix] = add_table_prefix(ic_prefix, cc_hint)

            ic_airport_names = set(airp['properties']['name'] for airp in prefix_store[ic_prefix]['features'])
            ic_airport = add_airport(triplet, *markers)
            if ic_airport['properties']['name'] not in ic_airport_names:
                prefix_store[ic_prefix]['features'].append(ic_airport)
                prefix_table_store[ic_prefix]['airports'].append(make_table_row(facts))

            prefix_root = pathlib.Path(FS_PREFIX_PATH)
            map_folder = pathlib.Path(prefix_root, ic_prefix, root_icao)
            map_folder.mkdir(parents=True, exist_ok=True)
            if geojson_path == DERIVE_GEOJSON_NAME:
                geojson_path = str(pathlib.Path(map_folder, f'{root_icao.lower()}-geo.json'))
            geo_json_name = pathlib.Path(geojson_path).name
            with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
                json.dump(geojson, geojson_handle, indent=2)
            log.debug('Wrote geojson to %s' % str(geojson_path))
            geojson_path = str(pathlib.Path(map_folder, f'{root_icao.lower()}-geo.json'))
            geo_json_name = pathlib.Path(geojson_path).name
            with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
                json.dump(geojson, geojson_handle, indent=2)
            log.debug('Wrote geojson to %s' % str(geojson_path))

            html_dict = {
                f'{ANCHOR}/{IC_PREFIX_ICAO}': my_prefix_path,
                f'{ANCHOR}/{IC_PREFIX}': f'prefix/{ic_prefix}/',
                ICAO: root_icao,
                icao: root_icao.lower(),
                City: airport_name[root_icao].title(),
                CITY: airport_name[root_icao],
                CC_HINT: cc_hint,
                cc_page: country_page_hack(cc_hint),
                Cc_page: country_page_hack(cc_hint).title(),
                LAT_LON: f'{root_lat},{root_lon}',
                PATH: PATH_NAV,
                HOST: HOST_NAV,
                URL: GOOGLE_MAPS_URL.format(lat=root_lat, lon=root_lon),
                ZOOM: str(max(DEFAULT_ZOOM - runway_count + 1, 9)),
                'IrealCAO': ICAO,
                'index.json': geo_json_name,
                'index.r.txt': r_file_name,
                'index.txt': f'airport-{root_icao}.json',
                IC_PREFIX: ic_prefix,
                'DATA_ROWS': f'{data_row}\n',
            }
            html_page = HTML_PAGE
            for key, replacement in html_dict.items():
                html_page = html_page.replace(key, replacement)

            html_path = pathlib.Path(map_folder, 'index.html')
            with open(html_path, 'wt', encoding=ENCODING) as html_handle:
                html_handle.write(html_page)

            with open(PREFIX_TABLE_STORE, 'wt', encoding=ENCODING) as json_prefix_table_handle:
                json.dump(prefix_table_store, json_prefix_table_handle, indent=2)

            with open(PREFIX_STORE, 'wt', encoding=ENCODING) as geojson_prefix_handle:
                json.dump(prefix_store, geojson_prefix_handle, indent=2)

        else:
            log.warning('no airport found with R sources.')

    return 0


sys.exit(main(sys.argv[1:]))

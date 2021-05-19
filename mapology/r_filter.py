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
ANCHOR = 'ANCHOR'
TEXT = 'TEXT'
URL = 'URL'
ZOOM = 'ZOOM'
DEFAULT_ZOOM = 16

icao = 'icao_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'

ATTRIBUTION = f'{KIND} {ITEM} of '

PREFIX_STORE = pathlib.Path('prefix-store.json')

Point = collections.namedtuple('Point', ['label', 'lat', 'lon'])

# GOOGLE_MAPS_URL = f'https://www.google.com/maps/search/?api=1&query={{lat}}%2c{{lon}}'  # Map + pin Documented
GOOGLE_MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{lat}+{lon}'  # Sat + pin Undocumented

# load html poor person template from file
with open(pathlib.Path('mapology', 'templates', 'html', 'page.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read()

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
            print(line.strip())
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
        # print(data[aspect][-1])
        return True

    try:
        label, lat, lon = record.split(REC_SEP)
    except ValueError as err:
        print('DEBUG: <<<', record, '>>>')
        print(err)
        return False

    point = Point(label, lat, lon)
    if not seen[AIRP]:
        return update(AIRP, point)

    if is_frequency(label):  # ARINC424 source ma provide airports without runways but with frequencies
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
        # print('Read:', line, end='')
        if on:
            record = line.strip().strip(TRIGGER_END_OF_DATA)
            found = parse(record, seen, data)
            if not found:
                print('WARNING Unhandled ->>>>>>', record)
        if not on:
            on = line.startswith(TRIGGER_START_OF_DATA)
        else:
            if line.strip().endswith(TRIGGER_END_OF_DATA):
                break
    return seen, data


def make_feature(feature_data: List[Point], kind: str, cc: str, ric: str) -> List[FeatureDict]:
    """DRY."""
    local_features = []
    for triplet in feature_data:
        label = triplet.label
        lat_str = triplet.lat
        lon_str = triplet.lon
        feature = copy.deepcopy(GEO_JSON_FEATURE)
        name = feature['properties']['name']  # type: ignore
        name = name.replace(ICAO, ric).replace(KIND, kind)
        name = name.replace(ITEM, label).replace(TEXT, label)
        name = name.replace(CITY, airport_name[ric])
        name = name.replace(CC_HINT, cc)
        name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=float(lat_str), lon=float(lon_str)))

        feature['properties']['name'] = name  # type: ignore
        feature['geometry']['coordinates'].append(float(lon_str))  # type: ignore
        feature['geometry']['coordinates'].append(float(lat_str))  # type: ignore

        local_features.append(feature)

    return local_features


def make_airport(point: Point, cc: str, ric: str) -> FeatureDict:
    """DRY."""
    geojson = copy.deepcopy(GEO_JSON_HEADER)
    name = geojson['name']
    name = name.replace(ICAO, ric).replace(City, airport_name[ric].title())  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore
    geojson['name'] = name

    airport = copy.deepcopy(GEO_JSON_FEATURE)
    name = airport['properties']['name']  # type: ignore
    name = name.replace(ICAO, ric).replace(TEXT, ric).replace(ATTRIBUTION, '')  # type: ignore
    name = name.replace(CITY, airport_name[ric].title())  # type: ignore
    name = name.replace(URL, './')  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore
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


def add_airport(point: Point, cc: str, ric: str) -> PFeatureDict:
    """DRY."""
    airport = copy.deepcopy(GEO_JSON_PREFIX_FEATURE)
    name = airport['properties']['name']  # type: ignore
    name = name.replace(ICAO, ric).replace(TEXT, ric).replace(ATTRIBUTION, '')  # type: ignore
    name = name.replace(CITY, airport_name[ric].title())  # type: ignore
    name = name.replace(URL, f'{ric}/')  # type: ignore
    name = name.replace(CC_HINT, cc)  # type: ignore
    airport['properties']['name'] = name  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lon))  # type: ignore
    airport['geometry']['coordinates'].append(float(point.lat))  # type: ignore

    return airport


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2:
        r_path, geojson_path = argv[:2]
    else:
        r_path, geojson_path = STDIN_TOKEN, DERIVE_GEOJSON_NAME

    if not geojson_path:
        geojson_path = DERIVE_GEOJSON_NAME

    reader = read_stdin if r_path == STDIN_TOKEN else functools.partial(read_file, r_path)
    seen, data = parse_data(reader)  # type: ignore

    runway_count = 0
    if data and AIRP in data:
        triplet = data[AIRP][0]
        root_icao, root_lat, root_lon = triplet.label.strip(), float(triplet.lat), float(triplet.lon)
        ic_prefix = root_icao[:2]
        cc_hint = flat_prefix[ic_prefix]
        markers = cc_hint, root_icao

        geojson = make_airport(triplet, *markers)

        if RUNW in data:
            geojson['features'].extend(make_feature(data[RUNW], 'Runway', *markers))  # type: ignore
            runway_count = len(data[RUNW])  # HACK A DID ACK for zoom heuristics

        if FREQ in data:
            geojson['features'].extend(make_feature(data[FREQ], 'Frequency', *markers))  # type: ignore

        if LOCA in data:
            geojson['features'].extend(make_feature(data[LOCA], 'Localizer', *markers))  # type: ignore

        if GLID in data:
            geojson['features'].extend(make_feature(data[GLID], 'Glideslope', *markers))  # type: ignore

        # Process prefix store
        if ic_prefix not in prefix_store:
            # Create initial entry for ICAO prefix
            prefix_store[ic_prefix] = add_prefix(ic_prefix, cc_hint)

        ic_airport_names = set(airp['properties']['name'] for airp in prefix_store[ic_prefix]['features'])
        ic_airport = add_airport(triplet, *markers)
        if ic_airport['properties']['name'] not in ic_airport_names:
            prefix_store[ic_prefix]['features'].append(ic_airport)

        prefix_root = pathlib.Path(FS_PREFIX_PATH)
        map_folder = pathlib.Path(prefix_root, ic_prefix, root_icao)
        map_folder.mkdir(parents=True, exist_ok=True)
        if geojson_path == DERIVE_GEOJSON_NAME:
            geojson_path = str(pathlib.Path(map_folder, f'{root_icao.lower()}-geo.json'))
        with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
            json.dump(geojson, geojson_handle, indent=2)

        html_dict = {
            ANCHOR: prefix_path[root_icao],
            ICAO: root_icao,
            icao: root_icao.lower(),
            City: airport_name[root_icao].title(),
            CITY: airport_name[root_icao],
            CC_HINT: cc_hint,
            cc_page: country_page_hack(cc_hint),
            Cc_page: country_page_hack(cc_hint).title(),
            LAT_LON: f'{root_lat},{root_lon}',
            PATH: PATH_NAV,
            URL: GOOGLE_MAPS_URL.format(lat=root_lat, lon=root_lon),
            ZOOM: str(max(DEFAULT_ZOOM - runway_count + 3, 9)),
            'IrealCAO': ICAO,
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path(map_folder, 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

        with open(PREFIX_STORE, 'wt', encoding=ENCODING) as geojson_prefix_handle:
            json.dump(prefix_store, geojson_prefix_handle, indent=2)

    else:
        print('WARNING: no airport found in R source.')

    return 0


sys.exit(main(sys.argv[1:]))

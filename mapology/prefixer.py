#! /usr/bin/env python
"""Generate prefix page for the requested ICAO prefix."""
import collections
import json
import os
import pathlib
import sys
from typing import List, Union

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
with open(pathlib.Path('mapology', 'templates', 'html', 'prefix.html'), 'rt', encoding=ENCODING) as handle:
    HTML_PAGE = handle.read().replace('AERONAUTICAL_ANNOTATIONS', AERONAUTICAL_ANNOTATIONS)

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


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: prefixer 2_LETTER_ICAO_PREFIX")

    ic_prefix = argv[0].upper()
    cc_hint = flat_prefix[ic_prefix]
    geojson_airports = prefix_store[ic_prefix]  # Let it crash when prefix not known
    geojson_path = DERIVE_GEOJSON_NAME

    ra_count = 0  # region_airports_count
    cc_count = 1  # HACK A DID ACK TODO: do not fix country count to wun
    illas = []
    if geojson_airports:
        min_lat, min_lon = 90, 180
        max_lat, max_lon = -90, -180
        coordinates = []
        for airport in geojson_airports["features"]:
            ra_count += 1
            # name has eg. "<a href='KLGA/' target='_blank' title='KLGA(La Guardia, New York, USA)'>KLGA</a>"
            name_mix = airport['properties']['name'].split("title='", 1)[1]
            # name_mix has eg. "KLGA(La Guardia, New York, USA)'>KLGA</a>"
            code, rest = name_mix.split('(', 1)
            name = rest.split(')', 1)[0]
            coords = airport["geometry"]["coordinates"]
            lon, lat = coords[0], coords[1]
            illas.append((code, str(lat), str(lon), name))
            coordinates.append((lon, lat))
            min_lat = min(min_lat, lat)
            min_lon = min(min_lon, lon)
            max_lat = max(max_lat, lat)
            max_lon = max(max_lon, lon)

        prefix_lat = 0.5 * (max_lat + min_lat)
        prefix_lon = 0.5 * (max_lon + min_lon)
        print(f"Found {len(coordinates)} airports for prefix {ic_prefix}")
        bbox_disp = f"[({min_lat}, {min_lon}), ({max_lat}, {max_lon})]"
        print(f"Identified bounding box lat, lon in {bbox_disp} for prefix {ic_prefix}")
        print(f"Set center of prefix map to lat, lon = ({prefix_lat}, {prefix_lon}) for prefix {ic_prefix}")
        prefix_root = pathlib.Path(FS_PREFIX_PATH)
        map_folder = pathlib.Path(prefix_root, ic_prefix)
        map_folder.mkdir(parents=True, exist_ok=True)
        if geojson_path == DERIVE_GEOJSON_NAME:
            geojson_path = str(pathlib.Path(map_folder, f'{ic_prefix.lower()}-geo.json'))
        with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
            json.dump(geojson_airports, geojson_handle, indent=2)

        data_rows = []
        for code, lat_str, lon_str, airport_name in sorted(illas):
            code_link = f'<a href="{code}/">{code}</a>'
            row = f'<tr><td>{code_link}</td><td>{lat_str}</td><td>{lon_str}</td><td>{airport_name}</td></tr>'
            data_rows.append(row)

        html_dict = {
            ANCHOR: f'prefix/{ic_prefix}/',
            ic_prefix_token: ic_prefix.lower(),
            CC_HINT: cc_hint,
            cc_page: country_page_hack(cc_hint),
            Cc_page: country_page_hack(cc_hint).title(),
            LAT_LON: f'{prefix_lat},{prefix_lon}',
            PATH: PATH_NAV,
            HOST: HOST_NAV,
            ZOOM: str(DEFAULT_ZOOM),
            IC_PREFIX: ic_prefix,
            'IrealCAO': ICAO,
            'REGION_AIRPORT_COUNT_DISPLAY': f'{ra_count} airport{"" if ra_count == 1 else "s"}',
            'COUNTRY_COUNT_DISPLAY': f'{cc_count} countr{"y" if cc_count == 1 else "ies"}',
            'DATA_ROWS': '\n'.join(data_rows),
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path(map_folder, 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    else:
        print('WARNING: no airports found in prefix store for', ic_prefix)

    return 0


sys.exit(main(sys.argv[1:]))

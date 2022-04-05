#! /usr/bin/env python
"""Generate index page for the rendered prefix trees."""
import json
import os
import pathlib
import sys
from typing import Collection, Dict, List, Union

import mapology.db as db
import mapology.template_loader as template
from mapology import BASE_URL, ENCODING, FOOTER_HTML, FS_PREFIX_PATH, LIB_PATH, PATH_NAV, log

FeatureDict = Dict[str, Collection[str]]
PHeaderDict = Dict[str, Collection[str]]
PFeatureDict = Dict[str, Collection[str]]

HTML_TEMPLATE = os.getenv('GEO_INDEX_HTML_TEMPLATE', '')
HTML_TEMPLATE_IS_EXTERNAL = bool(HTML_TEMPLATE)
if not HTML_TEMPLATE:
    HTML_TEMPLATE = 'prefix_index_template.html'

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
FOOTER_HTML_KEY = 'FOOTER_HTML'
LIB_PATH_KEY = 'LIB_PATH'

icao = 'icao_lower'
ic_prefix_token = 'ic_prefix_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'

ATTRIBUTION = f'{KIND} {ITEM} of '

# GOOGLE_MAPS_URL = f'https://www.google.com/maps/search/?api=1&query={{lat}}%2c{{lon}}'  # Map + pin Documented
GOOGLE_MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{lat}+{lon}'  # Sat + pin Undocumented


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print('usage: mapology index')
        return 2

    store_index = db.load_index('store')
    table_index = db.load_index('table')

    prefixes = sorted(table_index.keys())
    row_slot_set = set(prefix[0] for prefix in prefixes)
    col_slot_set = set(prefix[1] for prefix in prefixes)
    columns = sorted(col_slot_set)
    rows = sorted(row_slot_set)

    table = {f'{k}{j}': '<td>&nbsp;</td>' for k in rows for j in columns}
    log.debug('I\\C |' + ' | '.join(columns))
    for row in rows:
        log.debug(row)

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
            LIB_PATH_KEY: LIB_PATH,
            PATH: PATH_NAV,
            LAT_LON: '0, 0',
            ZOOM: str(DEFAULT_ZOOM),
            BASE_URL_TARGET: BASE_URL,
            'NUMBER_REGIONS': str(regions),
            'TOTAL_AIRPORTS': str(total_airports),
            FOOTER_HTML_KEY: FOOTER_HTML,
            'DATA_COLS': '\n'.join(data_cols),
            'DATA_ROWS': ''.join(data_rows),
        }
        html_page = template.load_html(HTML_TEMPLATE, HTML_TEMPLATE_IS_EXTERNAL)
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)

        html_path = pathlib.Path(FS_PREFIX_PATH, 'index.html')
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

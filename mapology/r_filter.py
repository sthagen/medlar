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
import sys
from typing import Callable, Collection, Dict, Iterator, List, Tuple, Union

FeatureDict = Dict[str, Collection[str]]

ENCODING = 'utf-8'

COUNTRY_PAGE = os.getenv('GEO_COUNTRY_PAGE', '')

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
ITEM = 'ITEM'
KIND = 'KIND'
TEXT = 'TEXT'
URL = 'URL'

icao = 'icao_lower'
LAT_LON = 'LAT_LON'
cc_page = 'cc_page'
Cc_page = 'Cc_page'

ATTRIBUTION = f'{KIND} {ITEM} of '

Point = collections.namedtuple('Point', ['label', 'lat', 'lon'])

# GOOGLE_MAPS_URL = f'https://www.google.com/maps/search/?api=1&query={{lat}}%2c{{lon}}'  # Map + pin Documented
GOOGLE_MAPS_URL = 'https://maps.google.com/maps?t=k&q=loc:{{lat}}+{{lon}}'  # Sat + pin Undocumented

HTML_PAGE = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>IrealCAO / {ICAO} ({City}, {CC_HINT}) - Airport</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/navdb/_/leaflet/leaflet.css"/>
    <script src="/navdb/_/leaflet/leaflet.js"></script>
    <style>
        body {{
            margin-left: 1%;
            font-family: Verdana, serif;
        }}
        #mapid {{
            width: 98%;
            height: 600px;
            border: thin dotted;
        }}
        .leaflet-tooltip {{
            pointer-events: auto;
        }}
        html {{font-family: Verdana, Arial, sans-serif;}}
        a {{color: #0c2d82;}}
        b {{font-weight: 600;}}
        h1, h2 {{margin-left: 1rem;}}
        h1 {{font-weight: 300; text-transform: capitalize;}}
        h2 {{font-weight: 200;}}
        p {{margin-left: 2rem;}}
        .no-decor {{text-decoration: none;}}
    </style>
</head>
<body>
<main>
    <section>
        <h1>HOME <a href="https://path/" class="no-decor">NavDB</a>
            - ( <a href="https://path/icao/" class="no-decor">IrealCAO</a>
            | <a href="https://path/icao/{cc_page}.html" class="no-decor">{Cc_page}</a> )
            / <a href="https://path/icao/{icao}/" class="no-decor">{ICAO}</a>
            ({City}, {CC_HINT}) - Airport</h1>
        <div id="mapid"></div>
        <h2>Satellite Imagery &amp; More</h2>
        <p>&nbsp;Airport: ICAO <a
                href="{URL}"
                class="no-decor" target="_blank">@{LAT_LON}</a>
            - (<a href="index.json" class="no-decor" target="_blank">data</a> | <a href="index.txt" class="no-decor"
                                                                                   target="_blank">log</a> | <a
                    href="index.r.txt" class="no-decor" target="_blank">R source</a>)
        </p>
    </section>
</main>
<footer>
    <address><p>Prototype</p></address>
</footer>
<script>
    let geo = null
    async function load() {{
        let url = '{icao}-geo.json'
        try {{
            geo = await (await fetch(url)).json()
        }} catch (e) {{
            console.log('error in loading GeoJSON data')
        }}
        // console.log("Here it is")
        // console.log(geo)
        let meta = [{LAT_LON}]
        // let mymap = L.map('mapid').setView(meta, 14)
    let ggUrl = 'https://{{s}}.google.com/vt/lyrs=s,h&x={{x}}&y={{y}}&z={{z}}'
    let ggAttr = '&copy; <a href="https://www.google.com/permissions/geoguidelines/attr-guide/"
                            target="_blank">Google</a> and contributors'
    let osUrl = 'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'
    let osAttr =  '&copy; <a href="https://www.openstreetmap.org/copyright"
                             target="_blank">OpenStreetMap</a> contributors'
    let satellite = L.tileLayer(ggUrl, {{maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3'], attribution: ggAttr}})
    let streets = L.tileLayer(osUrl, {{maxZoom: 20, attribution: osAttr}})
/*    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }}).addTo(mymap)
*/
    let baseLayers = {{
          "Streets": streets,
          "Satellite": satellite,
    }}
    // let center = L.marker(meta).addTo(mymap)
    let data_points = geo
    let pointLayer = L.geoJSON(null, {{
        pointToLayer: function (feature, latlng) {{
            label = String(feature.properties.name)
            return new L.CircleMarker(latlng, {{
                radius: 1,
            }}).bindTooltip(label, {{permanent: true, opacity: 0.7}}).openTooltip()
        }}
    }})
    pointLayer.addData(data_points)
    let mymap = L.map('mapid', {{
      center: [{LAT_LON}],
      zoom: 16,
      layers: [streets, pointLayer]
    }})
    // mymap.addLayer(pointLayer)
    var overlays = {{
          "Airport": pointLayer
    }}
    L.control.layers(baseLayers, overlays).addTo(mymap);

    // enable Ctrl-Click to find coordinate at click position (hand cursor not so precise, but we can zoom)
    var popup = L.popup()
    function onMapClick(e) {{
      if (e.originalEvent.ctrlKey) {{
        popup
          .setLatLng(e.latlng)
          .setContent("You clicked the map at " + e.latlng.toString())
          .openOn(mymap)
      }}
    }}
    mymap.on('click', onMapClick)
    }}
    load()
</script>
</body>
</html>
"""

GEO_JSON_HEADER = {
    'type': 'FeatureCollection',
    'name': 'Airport - {ICAO} ({City}, {CC_HINT})',
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
        'name': "<a href='{URL}' target='_blank' title='{KIND} {ITEM} of {ICAO}({CITY}, {CC_HINT})'>{TEXT}</a>",
    },
    'geometry': {
        'type': 'Point',
        'coordinates': [],  # Note: lon, lat
    },
}

# load data like: {"prefix/00/00C/:": "ANIMAS",}
with open('prefix_airport_names_for_index.json', 'rt', encoding=ENCODING) as handle:
    airport_path_to_name = json.load(handle)


def icao_from_key_path(text: str) -> str:
    """HACK A DID ACK"""
    return text.rstrip('/:').rsplit('/', 1)[1]


# Example: {"GCFV": "FUERTEVENTURA",}
airport_name = {icao_from_key_path(k): v for k, v in airport_path_to_name}

# load data like: {"AG": "Solomon Islands",}
with open('country_prefix_to_country_name.json', 'rt', encoding=ENCODING) as handle:
    flat_prefix = json.load(handle)


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
    with open(path, 'rt', encoding='ENCODING') as handle:
        yield handle.readline()


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
    label, lat, lon = record.split(REC_SEP)
    if not seen[AIRP]:
        data[AIRP] = [Point(label, lat, lon)]
        seen[AIRP] = True
        print(data[AIRP])
        return True
    if is_runway(label):
        if RUNW not in data:
            data[RUNW] = []
        data[RUNW].append(Point(label, lat, lon))
        seen[RUNW] = True
        print(data[RUNW][-1])
        return True
    if is_frequency(label):  # ARINC424 source has airports without runways but with frequencies
        if FREQ not in data:
            data[FREQ] = []
        data[FREQ].append(Point(label, lat, lon))
        seen[FREQ] = True
        print(data[FREQ][-1])
        return True
    if seen[RUNW] and maybe_localizer(label):
        if LOCA not in data:
            data[LOCA] = []
        data[LOCA].append(Point(label, lat, lon))
        seen[LOCA] = True
        print(data[LOCA][-1])
        return True
    if seen[RUNW] and maybe_glideslope(label):
        if GLID not in data:
            data[GLID] = []
        data[GLID].append(Point(label, lat, lon))
        seen[GLID] = True
        print(data[GLID][-1])
        return True
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


def make_feature(feature_data: List[Point], kind: str, cc_hint: str, root_icao: str) -> List[FeatureDict]:
    """DRY."""
    local_features = []
    for triplet in feature_data:
        feature = copy.deepcopy(GEO_JSON_FEATURE)
        name = feature['properties']['name']  # type: ignore
        name = name.replace(ICAO, root_icao).replace(KIND, kind)
        name = name.replace(ITEM, triplet.label).replace(TEXT, triplet.label)
        name = name.replace(CITY, airport_name[root_icao])
        name = name.replace(CC_HINT, cc_hint)

        lat, lon = float(triplet.lat), float(triplet.lon)
        name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))
        feature['properties']['name'] = name  # type: ignore
        feature['geometry']['coordinates'].append(float(triplet.lon))  # type: ignore
        feature['geometry']['coordinates'].append(float(triplet.lat))  # type: ignore

        local_features.append(feature)

    return local_features


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    r_path, geojson_path = argv[:2] if len(argv) == 2 else STDIN_TOKEN, None

    reader = read_stdin if r_path == STDIN_TOKEN else functools.partial(read_file, r_path)
    seen, data = parse_data(reader)  # type: ignore

    if data and AIRP in data:
        triplet = data[AIRP]
        root_icao, root_lat, root_lon = triplet.label, float(triplet.lat), float(triplet.lon)  # type: ignore
        cc_hint = flat_prefix[root_icao[:2]]
        root_coords = (triplet.lon, triplet.lat)  # type: ignore
        geojson = copy.deepcopy(GEO_JSON_HEADER)
        name = geojson['name']
        name = name.replace(ICAO, root_icao).replace(City, airport_name[root_icao].title())  # type: ignore
        name = name.replace(CC_HINT, cc_hint)  # type: ignore
        geojson['name'] = name

        airport = copy.deepcopy(GEO_JSON_FEATURE)
        name = airport['properties']['name']  # type: ignore
        name = name.replace(ICAO, root_icao).replace(TEXT, root_icao).replace(ATTRIBUTION, '')  # type: ignore
        name = name.replace(CITY, airport_name[root_icao].title())  # type: ignore
        name = name.replace(URL, './')  # type: ignore
        name = name.replace(CC_HINT, cc_hint)  # type: ignore
        airport['properties']['name'] = name  # type: ignore
        airport['geometry']['coordinates'].append(float(triplet.lon))  # type: ignore
        airport['geometry']['coordinates'].append(float(triplet.lat))  # type: ignore

        geojson['features'].append(airport)  # type: ignore

        if RUNW in data:
            key, kind = RUNW, 'Runway'
            for triplet in data[key]:  # type: ignore
                feature = copy.deepcopy(GEO_JSON_FEATURE)
                name = feature['properties']['name']  # type: ignore
                name = name.replace(ICAO, root_icao).replace(KIND, kind)  # type: ignore
                name = name.replace(ITEM, triplet.label).replace(TEXT, triplet.label)  # type: ignore
                name = name.replace(CITY, airport_name[root_icao])  # type: ignore
                name = name.replace(CC_HINT, cc_hint)  # type: ignore

                lat, lon = float(triplet.lat), float(triplet.lon)  # type: ignore
                name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))  # type: ignore
                feature['properties']['name'] = name  # type: ignore
                feature['geometry']['coordinates'].append(lon)  # type: ignore
                feature['geometry']['coordinates'].append(lat)  # type: ignore

                geojson['features'].append(feature)  # type: ignore

        if FREQ in data:
            key, kind = FREQ, 'Frequency'
            for triplet in data[key]:  # type: ignore
                feature = copy.deepcopy(GEO_JSON_FEATURE)
                name = feature['properties']['name']  # type: ignore
                name = name.replace(ICAO, root_icao).replace(KIND, kind)  # type: ignore
                name = name.replace(ITEM, triplet.label)  # type: ignore
                name = name.replace(CITY, airport_name[root_icao])  # type: ignore
                name = name.replace(CC_HINT, cc_hint)  # type: ignore

                lat, lon = float(triplet.lat), float(triplet.lon)  # type: ignore
                freq_coords = (triplet.lon, triplet.lat)  # type: ignore
                if freq_coords != root_coords:
                    name = name.replace(TEXT, triplet.label)  # type: ignore
                    name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))  # type: ignore
                else:
                    name = name.replace(TEXT, root_icao)  # type: ignore
                    name = name.replace(URL, './')  # type: ignore

                feature['properties']['name'] = name  # type: ignore
                feature['geometry']['coordinates'].append(float(triplet.lon))  # type: ignore
                feature['geometry']['coordinates'].append(float(triplet.lat))  # type: ignore

                geojson['features'].append(feature)  # type: ignore

        if LOCA in data:
            geojson['features'].extend(make_feature(data[LOCA], 'Localizer', cc_hint, root_icao))  # type: ignore

        if GLID in data:
            geojson['features'].extend(make_feature(data[GLID], 'Glideslope', cc_hint, root_icao))  # type: ignore

        if geojson_path is None:
            geojson_path = f'{root_icao.lower()}-geo.json'
        with open(geojson_path, 'wt', encoding=ENCODING) as geojson_handle:
            json.dump(geojson, geojson_handle, indent=2)

        html_dict = {
            ICAO: root_icao,
            icao: root_icao.lower(),
            City: airport_name[root_icao].title(),
            CITY: airport_name[root_icao],
            CC_HINT: cc_hint,
            cc_page: country_page_hack(cc_hint),
            Cc_page: country_page_hack(cc_hint).title(),
            LAT_LON: f'{root_lat},{root_lon}',
            URL: GOOGLE_MAPS_URL.format(lat=root_lat, lon=root_lon),
            'IrealCAO': ICAO,
        }
        html_page = HTML_PAGE
        for key, replacement in html_dict.items():
            html_page = html_page.replace(key, replacement)
        html_path = f'{root_icao.lower()}.html'
        with open(html_path, 'wt', encoding=ENCODING) as html_handle:
            html_handle.write(html_page)

    else:
        print('WARNING: no airport found in R source.')

    return 0


sys.exit(main(sys.argv[1:]))

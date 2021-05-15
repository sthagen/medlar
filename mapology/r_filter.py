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

GEO_JSON_FEATURE = {
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


def icao_from_key_path(text):
    """HACK A DID ACK"""
    return text.rstrip('/:').rsplit('/', 1)[1]


# Example: {"GCFV": "FUERTEVENTURA",}
airport_name = {icao_from_key_path(k): v for k, v in airport_path_to_name}

# load data like: {"AG": "Solomon Islands",}
with open('country_prefix_to_country_name.json', 'rt', encoding=ENCODING) as handle:
    flat_prefix = json.load(handle)


def country_page_hack(phrase):
    """Return the first word in the hope it is meaningful."""
    if COUNTRY_PAGE:
        return COUNTRY_PAGE.lower()
    return phrase.split()[0].lower()


def read_stdin():
    """A simple stdin line based reader (generator)."""
    readline = sys.stdin.readline()
    while readline:
        yield readline
        readline = sys.stdin.readline()


def read_file(path):
    """A simple file line based reader (generator)."""
    with open(path, 'rt', encoding='ENCODING') as handle:
        yield handle.readline()


def is_runway(label):
    """Detect if label is a runway label"""
    return label.startswith('RW') and len(label) < 7


def is_frequency(label):
    """Detect if label is a frequency label"""
    return '_' in label and label.index('_') == 2 and len(label) == 10


def maybe_localizer(label):
    """Detect if label is maybe a localizer label"""
    return '_' not in label and len(label) < 7


def maybe_glideslope(label):
    """Detect if label is maybe a glideslope label"""
    return '_' in label and len(label) > 5 and any([label.endswith(t) for t in ('DME', 'ILS', 'TAC')])


def parse(record, seen, data):
    """Parse the record in a context sensitive manner (seen) into data."""
    label, lat, lon = record.split(REC_SEP)
    if not seen[AIRP]:
        data[AIRP] = Point(label, lat, lon)
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


def main(argv=None):
    """Drive the derivation."""
    argv = sys.argv[1:] if argv is None else argv
    r_path, geojson_path = argv[:2] if len(argv) == 2 else STDIN_TOKEN, None

    reader = read_stdin if r_path == STDIN_TOKEN else functools.partial(read_file, r_path)

    on = False  # The data start is within the file - not at the beginning
    seen = {k: False for k in (AIRP, RUNW, FREQ, LOCA, GLID)}
    data = {}
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

    if data and AIRP in data:
        triplet = data[AIRP]
        root_icao, root_lat, root_lon = triplet.label, float(triplet.lat), float(triplet.lon)
        cc_hint = flat_prefix[root_icao[:2]]
        root_coords = (triplet.lon, triplet.lat)
        geojson = copy.deepcopy(GEO_JSON_HEADER)
        name = geojson['name']
        name = name.replace(ICAO, root_icao).replace(City, airport_name[root_icao].title())
        name = name.replace(CC_HINT, cc_hint)
        geojson['name'] = name

        airport = copy.deepcopy(GEO_JSON_FEATURE)
        name = airport['properties']['name']
        name = name.replace(ICAO, root_icao).replace(TEXT, root_icao).replace(ATTRIBUTION, '')
        name = name.replace(CITY, airport_name[root_icao].title())
        name = name.replace(URL, './')
        name = name.replace(CC_HINT, cc_hint)
        airport['properties']['name'] = name
        airport['geometry']['coordinates'].append(float(triplet.lon))
        airport['geometry']['coordinates'].append(float(triplet.lat))

        geojson['features'].append(airport)

        if RUNW in data:
            for triplet in data[RUNW]:
                runway = copy.deepcopy(GEO_JSON_FEATURE)
                lat, lon = float(triplet.lat), float(triplet.lon)
                name = runway['properties']['name']
                name = name.replace(ICAO, root_icao).replace(KIND, 'Runway')
                name = name.replace(ITEM, triplet.label).replace(TEXT, triplet.label)
                name = name.replace(CITY, airport_name[root_icao])
                name = name.replace(CC_HINT, cc_hint)
                name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))
                runway['properties']['name'] = name
                runway['geometry']['coordinates'].append(lon)
                runway['geometry']['coordinates'].append(lat)

                geojson['features'].append(runway)

        if FREQ in data:
            for triplet in data[FREQ]:
                frequency = copy.deepcopy(GEO_JSON_FEATURE)
                lat, lon = float(triplet.lat), float(triplet.lon)
                name = frequency['properties']['name']
                name = name.replace(ICAO, root_icao).replace(KIND, 'Frequency')
                name = name.replace(ITEM, triplet.label)
                name = name.replace(CITY, airport_name[root_icao])
                name = name.replace(CC_HINT, cc_hint)
                freq_coords = (triplet.lon, triplet.lat)
                if freq_coords != root_coords:
                    name = name.replace(TEXT, triplet.label)
                    name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))
                else:
                    name = name.replace(TEXT, root_icao)
                    name = name.replace(URL, './')

                frequency['properties']['name'] = name
                frequency['geometry']['coordinates'].append(float(triplet.lon))
                frequency['geometry']['coordinates'].append(float(triplet.lat))

                geojson['features'].append(frequency)

        if LOCA in data:
            for triplet in data[LOCA]:
                localizer = copy.deepcopy(GEO_JSON_FEATURE)
                lat, lon = float(triplet.lat), float(triplet.lon)
                name = localizer['properties']['name']
                name = name.replace(ICAO, root_icao).replace(KIND, 'Localizer')
                name = name.replace(ITEM, triplet.label).replace(TEXT, triplet.label)
                name = name.replace(CITY, airport_name[root_icao])
                name = name.replace(CC_HINT, cc_hint)
                name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))
                localizer['properties']['name'] = name
                localizer['geometry']['coordinates'].append(float(triplet.lon))
                localizer['geometry']['coordinates'].append(float(triplet.lat))

                geojson['features'].append(localizer)

        if GLID in data:
            for triplet in data[GLID]:
                glideslope = copy.deepcopy(GEO_JSON_FEATURE)
                lat, lon = float(triplet.lat), float(triplet.lon)
                name = glideslope['properties']['name']
                name = name.replace(ICAO, root_icao).replace(KIND, 'Glideslope')
                name = name.replace(ITEM, triplet.label).replace(TEXT, triplet.label)
                name = name.replace(CITY, airport_name[root_icao])
                name = name.replace(CC_HINT, cc_hint)
                name = name.replace(URL, GOOGLE_MAPS_URL.format(lat=lat, lon=lon))
                glideslope['properties']['name'] = name
                glideslope['geometry']['coordinates'].append(float(triplet.lon))
                glideslope['geometry']['coordinates'].append(float(triplet.lat))

                geojson['features'].append(glideslope)

        if geojson_path is None:
            geojson_path = f'{root_icao.lower()}-geo.json'
        with open(geojson_path, 'wt', encoding=ENCODING) as handle:
            json.dump(geojson, handle, indent=2)

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
        with open(html_path, 'wt', encoding=ENCODING) as handle:
            handle.write(html_page)

    else:
        print('WARNING: no airport found in R source.')


sys.exit(main(sys.argv[1:]))

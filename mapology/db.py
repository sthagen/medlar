"""Database for the complete tree."""
import copy
import json
import pathlib
from typing import Collection, Dict, Mapping, no_type_check

from mapology import ENCODING, FS_DB_ROOT_PATH

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
PHeaderDict = Dict[str, Collection[str]]
CC_HINT = 'CC_HINT'
IC_PREFIX = 'IC_PREFIX'
GEO_JSON_PREFIX_HEADER: PHeaderDict = {
    'type': 'FeatureCollection',
    'id': f'{IC_PREFIX}',
    'name': f'Region - {IC_PREFIX} ({CC_HINT})',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'features': [],
}
JSON_PREFIX_TABLE_HEADER = {
    'type': 'x-prefix-table',
    'id': f'{IC_PREFIX}',
    'name': f'Region - {IC_PREFIX} ({CC_HINT})',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'airports': [],
}


def ensure_fs_tree() -> None:
    """Ensure the DB folder tree exists."""
    for db in DB_FOLDER_PATHS.values():
        db.mkdir(parents=True, exist_ok=True)

    for index in DB_INDEX_PATHS.values():
        if not index.exists():
            with open(index, 'wt', encoding=ENCODING) as handle:
                json.dump({}, handle, indent=2)


@no_type_check
def load_index(kind: str) -> Mapping[str, str]:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'rt', encoding=ENCODING) as handle:
        return json.load(handle)


def dump_index(kind: str, data: Mapping[str, str]) -> None:
    """DRY."""
    with open(DB_INDEX_PATHS[kind], 'wt', encoding=ENCODING) as handle:
        json.dump(data, handle, indent=2)


def hull_path(some_prefix: str) -> str:
    """DRY."""
    return str(DB_FOLDER_PATHS['hulls'] / f'{some_prefix}.json')


def add_prefix(icp: str, cc: str) -> PHeaderDict:
    """DRY."""
    geojson = copy.deepcopy(GEO_JSON_PREFIX_HEADER)
    geojson['name'] = geojson['name'].replace(IC_PREFIX, icp).replace(CC_HINT, cc)  # type: ignore
    geojson['id'] = geojson['id'].replace(IC_PREFIX, icp)  # type: ignore
    return geojson


def add_table_prefix(icp: str, cc: str) -> PHeaderDict:
    """DRY."""
    table = copy.deepcopy(JSON_PREFIX_TABLE_HEADER)
    table['name'] = table['name'].replace(IC_PREFIX, icp).replace(CC_HINT, cc)  # type: ignore
    table['id'] = table['id'].replace(IC_PREFIX, icp)  # type: ignore
    return table


@no_type_check
def update_aspect(index_db: Mapping[str, object], a_prefix: str, a_cc: str, kind: str) -> Mapping[str, object]:
    """Process the kinds' index and ensure prefix aspect db is present"""
    if a_prefix not in index_db:
        index_db[a_prefix] = str(DB_FOLDER_PATHS[kind] / f'{a_prefix}.json')  # noqa
        # Create initial kinds' store data entry for ICAO prefix
        factory = add_prefix if kind == 'store' else add_table_prefix
        with open(index_db[a_prefix], 'wt', encoding=ENCODING) as handle:  # noqa
            json.dump(factory(a_prefix, a_cc), handle)
    with open(index_db[a_prefix], 'rt', encoding=ENCODING) as handle:  # noqa
        return json.load(handle)

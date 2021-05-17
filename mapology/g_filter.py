# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
"""Generate geojson data based leaflet driven web app from flat data files."""
import os
import sys
from typing import List, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Point

DEBUG_VAR = 'MAPOLOGY_DEBUG'
DEBUG = os.getenv(DEBUG_VAR)

ENCODING = 'utf-8'
ENCODING_ERRORS_POLICY = 'ignore'


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the derivation."""
    argv = argv if argv else sys.argv[1:]
    if not argv:
        print('ERROR arguments expected.', file=sys.stderr)
        return 2
    obj = Point(coordinates=(3.1415, 42))
    if not obj:
        return 1
    if DEBUG:
        print('Point:', obj)
    my_feature = Feature(
        geometry=Point(coordinates=(1.6432, -19.123)), properties={'name': "<a href='abc' target='_blank'>abc</a>"}
    )
    if DEBUG:
        print('Feature:', my_feature)
    my_other_feature = Feature(
        geometry=Point(coordinates=(-80.234, -22.532)), properties={'name': "<a href='def' target='_blank'>def</a>"}
    )
    if DEBUG:
        print('Feature (other):', my_feature)
    feature_collection = FeatureCollection(
        features=[my_feature, my_other_feature],
        name='test-points-link-labels',
        crs={'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}},
    )
    if not feature_collection:
        return 1
    if DEBUG:
        print(feature_collection)
    return 0

# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
""""Generate geojson data based leaflet driven web app from flat data files."""
import os
import sys

from geojson import Feature, Point, FeatureCollection

DEBUG_VAR = "LIAISON_DEBUG"
DEBUG = os.getenv(DEBUG_VAR)

ENCODING = "utf-8"
ENCODING_ERRORS_POLICY = "ignore"


def main(argv=None):
    """Drive the derivation."""
    argv = argv if argv else sys.argv[1:]
    if not argv:
        print("ERROR arguments expected.", file=sys.stderr)
        return 2
    obj = Point((3.1415, 42))
    if not obj.is_valid:
        return 1
    my_feature = Feature(geometry=Point((1.6432, -19.123)))
    my_other_feature = Feature(geometry=Point((-80.234, -22.532)))
    feature_collection = FeatureCollection([my_feature, my_other_feature])
    if not feature_collection
        return 1
    if feature_collection.errors():
        return 1
    assert all([feature_collection[0] == feature_collection['features'][0], feature_collection[1] == my_other_feature]) is True
    return 0

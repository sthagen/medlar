# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
""""Generate geojson data based leaflet driven web app from flat data files."""
import os
import sys

import geojson

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
    obj = geojson.Point((3.1415, 42))
    if not obj.is_valid:
        return 1
    return 0

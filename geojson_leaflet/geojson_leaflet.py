# -*- coding: utf-8 -*-
# pylint: disable=expression-not-assigned,line-too-long
""""Generate geojson data based leaflet driven web app from flat data files."""
import datetime as dti
import os
import pathlib
import sys
import time

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

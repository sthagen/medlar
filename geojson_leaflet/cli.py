#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
""""Generate geojson data based leaflet driven web app from flat data files."""
import os
import sys

import geojson_leaflet.geojson_leaflet as liaison


# pylint: disable=expression-not-assigned
def main(argv=None):
    """Process the files separately per folder."""
    argv = sys.argv[1:] if argv is None else argv
    liaison.main(argv)

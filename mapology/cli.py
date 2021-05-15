#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""Generate geojson data based leaflet driven web app from flat data files."""
import sys

import mapology.g_filter as liaison


# pylint: disable=expression-not-assigned
def main(argv=None):
    """Delegate processing to functional module."""
    argv = sys.argv[1:] if argv is None else argv
    liaison.main(argv)

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""Generate geojson data based leaflet driven web app from flat data files."""
import sys
from typing import List, Union

import mapology.icao as icao


# pylint: disable=expression-not-assigned
def main(argv: Union[List[str], None] = None) -> int:
    """Delegate processing to functional module."""
    argv = sys.argv[1:] if argv is None else argv
    return icao.main(argv)

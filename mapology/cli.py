# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""Generate geojson data based leaflet driven web app from flat data files."""
import sys
from typing import List, Union

import mapology.countries_razor as razor
import mapology.icao as icao
import mapology.indexer as indexer
import mapology.prefixes as prefixer
import mapology.template_loader as template

USAGE = """\
Synopsis:
=========
- render airports per ICAO:
    mapology icao path/to/airborne/r/[IC/[ICAO/]]
- render prefix pages ICAO prefix:
    mapology prefix
- render index page collecting prefixes:
    mapology index
- render airport, prefix, and index page tree completely:
    mapology tree
- shave off some properties from the natural earth country data set:
    mapology shave
- eject the templates into the folder given (default EJECTED) and create the folder if it does not exist:
    mapology eject [into]
- this usage info:
    mapology [-h,--help]
"""


# pylint: disable=expression-not-assigned
def main(argv: Union[List[str], None] = None) -> int:
    """Delegate processing to functional module."""
    argv = sys.argv[1:] if argv is None else argv
    usage = any(p in ('-h', '--help') for p in argv) or not argv
    command, call, vector = '', None, []
    if not usage and argv:
        command = argv[0]
        vector = argv[1:]
        if command == 'icao':
            call = icao.main
        elif command == 'prefix':
            call = prefixer.main
        elif command == 'index':
            call = indexer.main
        elif command == 'tree':
            call = ((icao.main, vector), (prefixer.main, []), (indexer.main, []))  # type: ignore
        elif command == 'shave':
            call = razor.main
        elif command == 'eject':
            call = template.eject

    if usage or not call:
        print(USAGE)
        return 0 if usage else 2

    if not isinstance(call, tuple):
        return call(vector)

    code = 0
    for cmd, vec in call:
        code = cmd(vec)
        if code:
            return code

    return code

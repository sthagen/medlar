#! /usr/bin/env python
"""Fill the known ICAO prefix map to avoid gaps."""
import json
import pathlib
import sys
from typing import List, Union

ENCODING = 'utf-8'


def main(argv: Union[List[str], None] = None) -> int:
    """Drive the completion of ICAO prefix mappings to regions."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 0:
        print("Usage: prefix_filler")
        return 2

    # load data like: {"AG": "Solomon Islands",}
    with open(pathlib.Path('icao_prefix_to_country_name_gaps.json'), 'rt', encoding=ENCODING) as handle:
        flat_prefix = json.load(handle)

    alphabet = tuple('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    for k in alphabet:
        for j in alphabet:
            key = f'{k}{j}'
            if key not in flat_prefix:
                flat_prefix[key] = 'Unmapped Region'

        gapless_icao_map_path = pathlib.Path('icao_prefix_to_country_name.json')
        with open(gapless_icao_map_path, 'wt', encoding=ENCODING) as out_handle:
            out_handle.write(flat_prefix)

    return 0


sys.exit(main(sys.argv[1:]))

"""Determine hull curves from point sets."""
import functools
from typing import no_type_check

THE_HULLS = {
    'type': 'FeatureCollection',
    'name': 'Prefix Region Convex Hulls',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'urn:ogc:def:crs:OGC:1.3:CRS84',
        },
    },
    'features': [],
}
HULL_TEMPLATE = {
    'type': 'Feature',
    'id': '',
    'properties': {'name': ''},
    'geometry': {'type': 'Polygon', 'coordinates': []},
}


@no_type_check
def convex(coords):
    """Executes scan to return points in counter-clockwise order that are on the convex hull (Graham)."""
    turn_left, turn_right, turn_none = 1, -1, 0  # noqa

    def compare(a, b):
        return float(a > b) - float(a < b)

    def turn(p, q, r):
        return compare((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1]), 0)

    def keep_left(hull, r):
        while len(hull) > 1 and turn(hull[-2], hull[-1], r) != turn_left:
            hull.pop()
        if not len(hull) or hull[-1] != r:
            hull.append(r)
        return hull

    points = sorted(coords)
    lower_hull = functools.reduce(keep_left, points, [])
    upper_hull = functools.reduce(keep_left, reversed(points), [])
    return lower_hull.extend(upper_hull[i] for i in range(1, len(upper_hull) - 1)) or lower_hull

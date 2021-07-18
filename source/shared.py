import math
import pathlib
import os
from geometry import Vector, Box, mirrors

ASSETS_DIR = pathlib.Path(os.path.dirname(__file__)) / 'assets'
IMAGES_DIR = ASSETS_DIR / 'images'

M = 100  # a meter in [pixel] units
S = 50  # a second in [step] units
D = math.pi / 180  # a degree in [rad] units

MS = M / S  # meter per second
MS2 = M / S ** 2  # meter per second squared
DS = D / S  # degree per second
DS2 = D / S ** 2  # degree per second squared


class FIELD:
    outline = Box(Vector(8.08 * M, 4.48 * M))
    spawn_center = Vector(3.54 * M, 1.74 * M)

    low_barriers = [  # B2, B8, B5
        *mirrors(Box(Vector(0.8 * M, 0.2 * M), Vector(-2.14 * M, 0))),
        Box(Vector(0.354 * M, 0.354 * M))
    ]
    high_barriers = [  # B1, B6, B3, B7, B4, B9
        *mirrors(Box(Vector(1 * M, 0.2 * M), Vector(-3.54 * M, 1.14 * M))),
        *mirrors(Box(Vector(0.2 * M, 1 * M), Vector(-2.44 * M, -1.74 * M))),
        *mirrors(Box(Vector(1 * M, 0.2 * M), Vector(0, 1.205 * M)))
    ]


def limit_magnitude(value, top_value):
    return math.copysign(min(abs(value), top_value), value)

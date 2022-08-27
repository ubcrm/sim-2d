import math
import pathlib
import os
import enum
import pygame
from geometry import Vector, Box, mirrors

ASSETS_DIR = pathlib.Path(os.path.dirname(__file__)) / 'assets'
IMAGES_DIR = ASSETS_DIR / 'images'


class ZoneType(enum.Enum):
    blue_hp_buff = 0
    red_hp_buff = 1
    blue_ammo_buff = 2
    red_ammo_buff = 3
    move_debuff = 4
    shoot_debuff = 5


class Winner(enum.Enum):
    blue = 0
    red = 1
    tied = 2
    tbd = 3  # to be determined - game still in progress


class UNITS:
    m = 100  # a meter in [pixel] units
    s = 50  # a second in [step] units
    d = math.pi / 180  # a degree in [rad] units

    ms = m / s  # meters per second
    ms2 = m / s ** 2  # meters per second squared
    ds = d / s  # degrees per second
    ds2 = d / s ** 2  # degrees per second squared


class FIELD:
    outline = Box(Vector(8.08 * UNITS.m, 4.48 * UNITS.m))
    spawn_center = Vector(3.54 * UNITS.m, 1.74 * UNITS.m)

    low_barriers = [  # B2, B8, B5
        *mirrors(Box(Vector(0.8 * UNITS.m, 0.2 * UNITS.m), Vector(-2.14 * UNITS.m, 0))),
        Box(Vector(0.354 * UNITS.m, 0.354 * UNITS.m))
    ]
    high_barriers = [  # B1, B6, B3, B7, B4, B9
        *mirrors(Box(Vector(1 * UNITS.m, 0.2 * UNITS.m), Vector(-3.54 * UNITS.m, 1.14 * UNITS.m))),
        *mirrors(Box(Vector(0.2 * UNITS.m, 1 * UNITS.m), Vector(-2.44 * UNITS.m, -1.74 * UNITS.m))),
        *mirrors(Box(Vector(1 * UNITS.m, 0.2 * UNITS.m), Vector(0, 1.205 * UNITS.m)))
    ]


class UI:
    font = 'arial', 11
    blue = (0, 0, 210)
    red = (210, 0, 0)
    silver = (182, 186, 187)
    black = (0, 0, 0)


class ASSETS:
    background = pygame.image.load(IMAGES_DIR / 'background.png')
    field = pygame.image.load(IMAGES_DIR / 'field.png')
    guide = pygame.image.load(IMAGES_DIR / 'guide.png')
    logo = pygame.image.load(IMAGES_DIR / 'logo.png')
    bullet = pygame.image.load(IMAGES_DIR / 'robot/bullet.png')
    blue_robot = pygame.image.load(IMAGES_DIR / 'robot/blue.png')
    red_robot = pygame.image.load(IMAGES_DIR / 'robot/red.png')
    dead_robot = pygame.image.load(IMAGES_DIR / 'robot/dead.png')
    gimbal = pygame.image.load(IMAGES_DIR / 'robot/gimbal.png')
    zone = {
        ZoneType.blue_hp_buff: pygame.image.load(IMAGES_DIR / 'zone/blue_hp_buff.png'),
        ZoneType.red_hp_buff: pygame.image.load(IMAGES_DIR / 'zone/red_hp_buff.png'),
        ZoneType.blue_ammo_buff: pygame.image.load(IMAGES_DIR / 'zone/blue_ammo_buff.png'),
        ZoneType.red_ammo_buff: pygame.image.load(IMAGES_DIR / 'zone/red_ammo_buff.png'),
        ZoneType.move_debuff: pygame.image.load(IMAGES_DIR / 'zone/move_debuff.png'),
        ZoneType.shoot_debuff: pygame.image.load(IMAGES_DIR / 'zone/shoot_debuff.png')
    }
    navigation_file = ASSETS_DIR / 'navigation.json'


def limit_magnitude(value, top_value):
    return math.copysign(min(abs(value), top_value), value)


def to_draw_coords(vector: Vector, offset=(0., 0.)):
    return FIELD.outline.dims.x / 2 + vector.x + offset[0], FIELD.outline.dims.y / 2 - vector.y + offset[1]


def from_draw_coords(coords: tuple[int, int]):
    return Vector(coords[0] - FIELD.outline.dims.x / 2, -coords[1] + FIELD.outline.dims.y / 2)

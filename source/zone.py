from __future__ import annotations
import typing
import enum
from shared import M, S
from geometry import Vector, Box, mirrors

if typing.TYPE_CHECKING:
    from robot import Robot
    from team import Team


class ZoneType(enum.Enum):
    blue_hp_buff = 0
    red_hp_buff = 1
    blue_ammo_buff = 2
    red_ammo_buff = 3
    move_debuff = 4
    shoot_debuff = 5


class ZONE:
    dims = Vector(0.54 * M, 0.48 * M)
    outlines = (  # F1, F4, F2, F5, F3, F6
        *mirrors(Box(dims, Vector(-3.54 * M, 0.55 * M))),
        *mirrors(Box(dims, Vector(-2.14 * M, -0.59 * M))),
        *mirrors(Box(dims, Vector(0, 1.795 * M)))
    )
    reset_time = 60 * S


class Zone:
    def __init__(self, type_: ZoneType):
        self.type_ = type_
        self.is_activated = False
        self.outline = None

    def apply(self, robot: Robot, teams: dict[bool, Team]):
        if not self.is_activated and self.outline.contains(robot.center):
            self.is_activated = True

            if self.type_ is ZoneType.blue_hp_buff:
                teams[True].apply_hp_buff()
            elif self.type_ is ZoneType.red_hp_buff:
                teams[False].apply_hp_buff()
            elif self.type_ is ZoneType.blue_ammo_buff:
                teams[True].apply_ammo_buff()
            elif self.type_ is ZoneType.red_ammo_buff:
                teams[False].apply_ammo_buff()
            elif self.type_ is ZoneType.move_debuff:
                robot.apply_move_debuff()
            elif self.type_ is ZoneType.shoot_debuff:
                robot.apply_shoot_debuff()

    def reset(self, index: int):
        self.is_activated = False
        self.outline = ZONE.outlines[index]

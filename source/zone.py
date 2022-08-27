from __future__ import annotations
import typing
from shared import UNITS, ZoneType
from geometry import Vector, Box, mirrors

if typing.TYPE_CHECKING:
    from robot import Robot
    from team import Team


class ZONE:
    dims = Vector(0.54 * UNITS.m, 0.48 * UNITS.m)
    outlines = (  # F1, F4, F2, F5, F3, F6
        *mirrors(Box(dims, Vector(-3.54 * UNITS.m, 0.55 * UNITS.m))),
        *mirrors(Box(dims, Vector(-2.14 * UNITS.m, -0.59 * UNITS.m))),
        *mirrors(Box(dims, Vector(0, 1.795 * UNITS.m)))
    )


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

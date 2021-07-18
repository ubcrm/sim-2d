from __future__ import annotations
import typing
import random
import time
import enum
import functools
from shared import S, FIELD
from zone import ZoneType, ZONE, Zone
from team import Team

if typing.TYPE_CHECKING:
    from bullet import Bullet
    from geometry import LineSegment
    from robot import RobotCommand, Robot


class Winner(enum.Enum):
    blue = 0
    red = 1
    tied = 2
    tbd = 3  # to be determined - game in progress


class Game:
    def __init__(self):
        self.zones = {
            ZoneType.blue_hp_buff: Zone(ZoneType.blue_hp_buff),
            ZoneType.red_hp_buff: Zone(ZoneType.red_hp_buff),
            ZoneType.blue_ammo_buff: Zone(ZoneType.blue_ammo_buff),
            ZoneType.red_ammo_buff: Zone(ZoneType.red_ammo_buff),
            ZoneType.move_debuff: Zone(ZoneType.move_debuff),
            ZoneType.shoot_debuff: Zone(ZoneType.shoot_debuff)
        }
        self.teams = {
            True: Team(True),
            False: Team(False)
        }
        self.bullets: list[Bullet] = []
        self.time_remaining = 180 * S
        self.winner = Winner.tbd
        random.seed(time.time())
        
    @functools.cached_property
    def robots(self) -> tuple[Robot, Robot, Robot, Robot]:
        return self.teams[True].robots[True], self.teams[True].robots[False], self.teams[False].robots[True], self.teams[False].robots[False]

    def step(self, blue_commands: tuple[RobotCommand, RobotCommand], red_commands: tuple[RobotCommand, RobotCommand]):
        if not self.time_remaining % ZONE.reset_time:
            self._reset_zones()
        for robot, command in zip(self.robots, (*blue_commands, *red_commands)):
            robot.control(command)
        robots = self.robots
        for robot in robots:
            robot.step(self.time_remaining, robots)
            for zone in self.zones.values():
                zone.apply(robot, self.teams)
            if (bullet := robot.shoot()) is not None:
                self.bullets.append(bullet)
        for index, bullet in reversed(list(enumerate(self.bullets))):
            if self._bullet_hits(bullet, bullet.step()):
                del self.bullets[index]
        self.time_remaining -= 1
        self._update_winner()

    def _bullet_hits(self, bullet: Bullet, trajectory: LineSegment):
        return any([
            not FIELD.outline.contains(bullet.center),
            any(b.intersects(trajectory) for b in FIELD.high_barriers),
            any(r.absorbs_bullet(trajectory) for r in self.robots if (r is not bullet.owner))
        ])

    def _update_winner(self):
        blues_dead = all(r.hp == 0 for r in self.teams[True].robots.values())
        reds_dead = all(r.hp == 0 for r in self.teams[False].robots.values())

        if reds_dead and not blues_dead:
            self.winner = Winner.blue
        elif blues_dead and not reds_dead:
            self.winner = Winner.red
        elif self.time_remaining <= 0:
            damage_difference = self.teams[False].damage_taken - self.teams[True].damage_taken
            if damage_difference > 0:
                self.winner = Winner.blue
            elif damage_difference < 0:
                self.winner = Winner.red
            else:
                self.winner = Winner.tied

    def _reset_zones(self):
        positions = random.sample([0, 2, 4], k=3)  # randomly order F1/F2/F3 (0/2/4)
        sides = random.choices([0, 1], k=3)  # randomly choose left/right (0/1) side of field
        indices = []

        for position, side in zip(positions, sides):
            indices.append(position + side)
            indices.append(position + 1 - side)
        for index, zone in zip(indices, self.zones.values()):
            zone.reset(index)

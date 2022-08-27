from __future__ import annotations
import random
import typing
from geometry import Vector, LineSegment
from shared import UNITS

if typing.TYPE_CHECKING:
    from robot import Robot


class BULLET:
    speed = 20 * UNITS.ms
    sigma_x_speed = 2 * UNITS.ms
    sigma_y_speed = 1 * UNITS.ms


class Bullet:
    def __init__(self, owner: Robot):
        self.owner = owner
        self.center = owner.center.copy()
        relative_speed = Vector(random.gauss(BULLET.speed, BULLET.sigma_x_speed), random.gauss(0, BULLET.sigma_y_speed))
        self.speed = relative_speed.transform(owner.speed, owner.rotation + owner.gimbal_yaw)

    def step(self):
        old_center = self.center.copy()
        self.center += self.speed
        return LineSegment(old_center, self.center)

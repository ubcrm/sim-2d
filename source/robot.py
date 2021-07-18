from __future__ import annotations
import functools
import dataclasses
import typing
import math
from shared import M, S, D, MS, MS2, DS, DS2, FIELD
from geometry import Vector, LineSegment, Box, x_mirrors, y_mirrors
from bullet import Bullet, BULLET

if typing.TYPE_CHECKING:
    from team import Team


@dataclasses.dataclass
class RobotCommand:
    x_speed: float = 0.
    y_speed: float = 0.
    rotation_speed: float = 0.
    gimbal_yaw_speed: float = 0.
    shoot: bool = False


@dataclasses.dataclass
class MotionConfig:
    # new_speed = current_speed + accel - sign(current_speed) * friction_decel - current_speed * friction_coeff
    # 0 = top_accel - friction_decel - top_speed * friction_coeff
    top_speed: float
    top_accel: float
    friction_decel: float

    @functools.cached_property
    def friction_coeff(self):
        return (self.top_accel - self.friction_decel) / self.top_speed


class ROBOT:
    outline = Box(Vector(0.6 * M, 0.5 * M))

    _armor_length = 0.14 * M
    armor_lines = [
        LineSegment(*y_mirrors(Vector(outline.dims.x / 2, _armor_length / 2))),
        LineSegment(*x_mirrors(Vector(_armor_length / 2, outline.dims.y / 2))),
        LineSegment(*x_mirrors(Vector(_armor_length / 2, -outline.dims.y / 2))),
        LineSegment(*y_mirrors(Vector(-outline.dims.x / 2, _armor_length / 2)))
    ]
    armor_damages = [20, 40, 40, 60]

    _drive_radius = 0.3 * M
    _factor = 1 / (math.sqrt(2) * _drive_radius)
    drive_config = MotionConfig(3 * MS, 6 * MS2, 0.1 * MS2)
    rotation_config = MotionConfig(_factor * drive_config.top_speed, _factor * drive_config.top_accel, _factor * drive_config.friction_decel)
    gimbal_yaw_config = MotionConfig(300 * DS, 1000 * DS2, 10 * DS2)

    zero_tolerance = 0.001
    rebound_coeff = 0.4
    shot_cooldown = 0.1 * S


class Robot:
    def __init__(self, is_one: bool, team: Team):
        self.is_one = is_one
        self.team = team
        
        self.center = FIELD.spawn_center.mirror(team.is_blue, team.is_blue == is_one)
        self.rotation = 0. if team.is_blue else math.pi
        self.gimbal_yaw = 0.
        self.speed = Vector(0., 0.)
        self.rotation_speed = 0.
        self.gimbal_yaw_speed = 0.

        self.ammo = 50 if is_one else 0
        self.is_shooting = False
        self.shot_cooldown = 0
        self.heat = 0
        self.hp = 2000
        self.barrier_hits = 0
        self.robot_hits = 0
        self.can_move = True
        self.can_shoot = True
        self.debuff_timeout = 0

        self._corners = [c.transform(self.center, self.rotation) for c in ROBOT.outline.corners]
        self._armor_lines = [a.transform(self.center, self.rotation) for a in ROBOT.armor_lines]

    def absorbs_bullet(self, trajectory: LineSegment):
        if self.hp:
            for armor_line, armor_damage in zip(self._armor_lines, ROBOT.armor_damages):
                if trajectory.intersects(armor_line):
                    self.hp -= armor_damage
                    self.team.take_damage(armor_damage)
                    return True
        return ROBOT.outline.intersects(trajectory.inv_transform(self.center, self.rotation))

    def hits_barrier(self, barrier: Box):
        if self.center.distance_to(barrier.center) < ROBOT.outline.radius + barrier.radius and \
                (any(barrier.contains(p) for p in self._corners) or
                 any(ROBOT.outline.contains(p.inv_transform(self.center, self.rotation)) for p in barrier.corners)):
            self.barrier_hits += 1
            return True
        return False

    def hits_robot(self, robot: Robot):
        if self.center.distance_to(robot.center) < 2 * ROBOT.outline.radius and \
                (any(ROBOT.outline.contains(p.inv_transform(robot.center, robot.rotation)) for p in self._corners) or
                 any(ROBOT.outline.contains(p.inv_transform(self.center, self.rotation)) for p in robot._corners)):
            self.robot_hits += 1
            return True
        return False

    def hits(self, robots: tuple[Robot, Robot, Robot, Robot]):
        return any([
            any(not FIELD.outline.contains(c) for c in self._corners),
            any(self.hits_barrier(b) for b in [*FIELD.low_barriers, *FIELD.high_barriers]),
            any(self.hits_robot(r) for r in robots if r != self)])

    def shoot(self):
        if all([self.is_shooting, not self.shot_cooldown, self.ammo, self.can_shoot]):
            self.ammo -= 1
            self.heat += BULLET.speed
            self.shot_cooldown = ROBOT.shot_cooldown
            return Bullet(self)

    def control(self, command: RobotCommand):
        if not (self.hp and self.can_move):
            command.x_speed = 0.
            command.y_speed = 0.
            command.rotation_speed = 0.
        if not (self.hp and self.can_shoot):
            command.gimbal_yaw_speed = 0.
            command.shoot = False

        x_accel = self._accel_required(self.speed.x, command.x_speed, ROBOT.drive_config)
        y_accel = self._accel_required(self.speed.y, command.y_speed, ROBOT.drive_config)
        rotation_accel = self._accel_required(self.rotation_speed, command.rotation_speed, ROBOT.rotation_config)
        gimbal_yaw_accel = self._accel_required(self.gimbal_yaw_speed, command.gimbal_yaw_speed, ROBOT.gimbal_yaw_config)

        # if self.team and self.is_one:
        #     print(gimbal_yaw_accel)

        x_accel, y_accel, rotation_accel = self._limit_holonomic(
            x_accel, y_accel, rotation_accel, ROBOT.drive_config.top_accel, ROBOT.drive_config.top_accel, ROBOT.rotation_config.top_accel)
        self.speed.x = self._new_speed(self.speed.x, x_accel, ROBOT.drive_config)
        self.speed.y = self._new_speed(self.speed.y, y_accel, ROBOT.drive_config)
        self.rotation_speed = self._new_speed(self.rotation_speed, rotation_accel, ROBOT.rotation_config)
        self.gimbal_yaw_speed = self._new_speed(self.gimbal_yaw_speed, gimbal_yaw_accel, ROBOT.gimbal_yaw_config)
        self.is_shooting = command.shoot

    def step(self, time_remaining: float, robots: tuple[Robot, Robot, Robot, Robot]):
        self.debuff_timeout -= min(1, self.debuff_timeout)
        self.shot_cooldown -= min(1, self.shot_cooldown)

        if not time_remaining % (0.1 * S):
            self.settle_heat()
        if not self.debuff_timeout:
            self.can_move = True
            self.can_shoot = True
        if not self.hp:
            return

        if any([self.speed.x, self.speed.y, self.rotation_speed]):
            old_center, old_rotation, old_corners = self.center.copy(), self.rotation, self._corners.copy()
            self.center += self.speed.transform(angle=old_rotation)
            self.rotation = (self.rotation + self.rotation_speed) % (360 * D)
            self._corners = [p.transform(self.center, self.rotation) for p in ROBOT.outline.corners]

            if self.hits(robots):
                self.rotation_speed *= -ROBOT.rebound_coeff
                self.speed *= -ROBOT.rebound_coeff
                self.center, self.rotation, self._corners = old_center, old_rotation, old_corners
        self.gimbal_yaw = (self.gimbal_yaw + self.gimbal_yaw_speed) % (360 * D)
        self._armor_lines = [a.transform(self.center, self.rotation) for a in ROBOT.armor_lines]

    def settle_heat(self):  # rules 4.1.2
        self.heat = max(self.heat - (12 if self.hp >= 400 else 24), 0)
        if 240 < self.heat < 360:
            self.hp -= (self.heat - 240) * 4
        elif 360 <= self.heat:
            self.hp -= (self.heat - 360) * 40
            self.heat = 360
        self.hp = max(self.hp, 0)

    def apply_hp_buff(self):
        self.hp += 200

    def apply_ammo_buff(self):
        self.ammo += 100

    def apply_move_debuff(self):
        self.can_move = False
        self.debuff_timeout = 10 * S

    def apply_shoot_debuff(self):
        self.can_shoot = False
        self.debuff_timeout = 10 * S

    @staticmethod
    def _new_speed(current_speed: float, accel: float, config: MotionConfig):
        new_speed_ideal = current_speed + accel
        new_speed_magnitude = abs(new_speed_ideal) - config.friction_decel - abs(current_speed) * config.friction_coeff
        return math.copysign(max(0., new_speed_magnitude), new_speed_ideal)

    @staticmethod
    def _accel_required(current_speed: float, desired_speed: float, config: MotionConfig):
        if math.isclose(current_speed, 0, rel_tol=ROBOT.zero_tolerance) and desired_speed == 0.:
            return 0.
        new_speed = Robot._limit_magnitude(desired_speed, config.top_speed)
        accel = new_speed - current_speed + math.copysign(config.friction_decel, current_speed) + current_speed * config.friction_coeff
        return Robot._limit_magnitude(accel, config.top_accel)

    @staticmethod
    def _limit_holonomic(x: float, y: float, z: float, x_max: float, y_max: float, z_max: float):
        magnitude = max(abs(x / x_max) + abs(y / y_max) + abs(z / z_max), 1)
        return x / magnitude, y / magnitude, z / magnitude

    @staticmethod
    def _limit_magnitude(value, top_value):
        return math.copysign(min(abs(value), top_value), value)

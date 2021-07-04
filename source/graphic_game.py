from __future__ import annotations
import typing
import pygame
from shared import IMAGES_DIR, M, S, D, MS, DS, FIELD
from game import Game
from zone import ZoneType

if typing.TYPE_CHECKING:
    from geometry import Vector
    from bullet import Bullet
    from robot import Robot


class GRAPHIC_GAME:
    window_title = 'UBC RoboMaster AI Challenge Simulator'
    font = 'arial', 11
    robot_label_offset = (-10, -35)
    state_coords = [[(72 + 41 * i, 516 + 17 * j) for i in range(18)] for j in range(4)]
    info_coords = [(195 + 4 * 41 * i, 482) for i in range(4)]

    offset = (10, 10)
    screen_dims = (828, 638)
    background = pygame.image.load(IMAGES_DIR / 'background.png')
    logo = pygame.image.load(IMAGES_DIR / 'logo.png')
    bullet = pygame.image.load(IMAGES_DIR / 'robot/bullet.png')
    blue_robot = pygame.image.load(IMAGES_DIR / 'robot/blue.png')
    red_robot = pygame.image.load(IMAGES_DIR / 'robot/red.png')
    dead_robot = pygame.image.load(IMAGES_DIR / 'robot/dead.png')
    gimbal = pygame.image.load(IMAGES_DIR / 'robot/gimbal.png')
    zones = {
        ZoneType.blue_hp_buff: pygame.image.load(IMAGES_DIR / 'zone/blue_hp_buff.png'),
        ZoneType.red_hp_buff: pygame.image.load(IMAGES_DIR / 'zone/red_hp_buff.png'),
        ZoneType.blue_ammo_buff: pygame.image.load(IMAGES_DIR / 'zone/blue_ammo_buff.png'),
        ZoneType.red_ammo_buff: pygame.image.load(IMAGES_DIR / 'zone/red_ammo_buff.png'),
        ZoneType.move_debuff: pygame.image.load(IMAGES_DIR / 'zone/move_debuff.png'),
        ZoneType.shoot_debuff: pygame.image.load(IMAGES_DIR / 'zone/shoot_debuff.png')
    }

    blue = (0, 0, 210)
    red = (210, 0, 0)
    silver = (182, 186, 187)
    black = (0, 0, 0)


class GraphicGame(Game):
    def __init__(self):
        super().__init__()
        pygame.init()
        self._screen = pygame.display.set_mode(GRAPHIC_GAME.screen_dims)
        pygame.display.set_caption(GRAPHIC_GAME.window_title)
        pygame.display.set_icon(GRAPHIC_GAME.logo)
        pygame.font.init()
        self._font = pygame.font.SysFont(*GRAPHIC_GAME.font)

    def render(self):
        self._blit()
        pygame.display.flip()

    def _blit(self):
        self._screen.blit(GRAPHIC_GAME.background, (0, 0))
        self._blit_zones()
        for robot in self.robots:
            self._blit_robot(robot)
        for bullet in self.bullets:
            self._blit_bullet(bullet)
        self._blit_text(f'{self.time_remaining / S:.1f}', GRAPHIC_GAME.info_coords[0])
        self._blit_text(self.teams[False].damage_taken, GRAPHIC_GAME.info_coords[1])
        self._blit_text(self.teams[True].damage_taken, GRAPHIC_GAME.info_coords[2])
        self._blit_text(self.winner.name, GRAPHIC_GAME.info_coords[3])

    def _blit_zones(self):
        for zone in self.zones.values():
            if zone.is_activated:
                continue
            image = GRAPHIC_GAME.zones[zone.type_]
            rect = image.get_rect()
            rect.center = self._to_tuple(zone.outline.center, offset=GRAPHIC_GAME.offset)
            self._screen.blit(image, rect)

    def _blit_robot(self, robot: Robot):
        if not robot.hp:
            chassis_image = GRAPHIC_GAME.dead_robot
        elif robot.team.is_blue:
            chassis_image = GRAPHIC_GAME.blue_robot
        else:
            chassis_image = GRAPHIC_GAME.red_robot
        chassis_image = pygame.transform.rotate(chassis_image, robot.rotation / D)
        gimbal_image = pygame.transform.rotate(GRAPHIC_GAME.gimbal, (robot.gimbal_yaw + robot.rotation) / D)
        chassis_rect = chassis_image.get_rect()
        gimbal_rect = gimbal_image.get_rect()
        chassis_rect.center = gimbal_rect.center = self._to_tuple(robot.center, offset=GRAPHIC_GAME.offset)
        self._screen.blit(chassis_image, chassis_rect)
        self._screen.blit(gimbal_image, gimbal_rect)
        self._blit_text(
            f'{(1 if robot.is_one else 2) + (0 if robot.team.is_blue else 2)} | {robot.hp}',
            self._to_tuple(robot.center, offset=GRAPHIC_GAME.robot_label_offset),
            GRAPHIC_GAME.blue if robot.team.is_blue else GRAPHIC_GAME.red)
        self._blit_robot_status(robot)

    def _blit_robot_status(self, robot: Robot):
        row_coords = GRAPHIC_GAME.state_coords[robot.is_one + 2 * robot.team.is_blue]
        self._blit_text(f'{robot.center.x / M:.2f}', row_coords[0])
        self._blit_text(f'{robot.center.y / M:.2f}', row_coords[1])
        self._blit_text(f'{robot.rotation / D:.0f}', row_coords[2])
        self._blit_text(f'{robot.gimbal_yaw / D:.0f}', row_coords[3])
        self._blit_text(f'{robot.speed.x / MS:.2f}', row_coords[4])
        self._blit_text(f'{robot.speed.y / MS:.2f}', row_coords[5])
        self._blit_text(f'{robot.rotation_speed / DS:.2f}', row_coords[6])
        self._blit_text(f'{robot.gimbal_yaw_speed / DS:.2f}', row_coords[7])
        self._blit_text(f'{robot.ammo}', row_coords[8])
        self._blit_text(f'{robot.heat}', row_coords[9])
        self._blit_text(f'{robot.hp}', row_coords[10])
        self._blit_text(f'{robot.is_shooting}', row_coords[11])
        self._blit_text(f'{robot.shot_cooldown / S:.3f}', row_coords[12])
        self._blit_text(f'{robot.barrier_hits}', row_coords[13])
        self._blit_text(f'{robot.robot_hits}', row_coords[14])
        self._blit_text(f'{robot.can_move}', row_coords[15])
        self._blit_text(f'{robot.can_shoot}', row_coords[16])
        self._blit_text(f'{robot.debuff_timeout / S:.0f}', row_coords[17])

    def _blit_bullet(self, bullet: Bullet):
        bullet_rect = GRAPHIC_GAME.bullet.get_rect()
        bullet_rect.center = self._to_tuple(bullet.center, offset=GRAPHIC_GAME.offset)
        self._screen.blit(GRAPHIC_GAME.bullet, bullet_rect)

    def _blit_text(self, text: str, position: tuple[float, float], color=GRAPHIC_GAME.black):
        label = self._font.render(str(text), True, color)
        self._screen.blit(label, position)

    @staticmethod
    def _to_tuple(vector: Vector, offset=(0., 0.)):
        return FIELD.outline.dims.x / 2 + vector.x + offset[0], FIELD.outline.dims.y / 2 - vector.y + offset[1]

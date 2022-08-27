from __future__ import annotations
import typing
import pygame
from shared import UNITS, UI, ASSETS, to_draw_coords
from game import Game

if typing.TYPE_CHECKING:
    from bullet import Bullet
    from robot import Robot


class GRAPHIC_GAME:
    window_title = 'UBC RoboMaster AI Challenge Simulator'
    robot_label_offset = (-10, -35)
    state_coords = [[(72 + 41 * i, 567 - 17 * j) for i in range(18)] for j in range(4)]
    info_coords = [(195 + 4 * 41 * i, 482) for i in range(4)]

    offset = (10, 10)
    screen_dims = (828, 638)


class GraphicGame(Game):
    def __init__(self):
        super().__init__()
        pygame.init()
        self._screen = pygame.display.set_mode(GRAPHIC_GAME.screen_dims)
        pygame.display.set_caption(GRAPHIC_GAME.window_title)
        pygame.display.set_icon(ASSETS.logo)
        pygame.font.init()
        self._font = pygame.font.SysFont(*UI.font)

    def render(self):
        self._blit()
        pygame.display.flip()

    def _blit(self):
        self._screen.blit(ASSETS.background, (0, 0))
        self._blit_zones()
        for robot in self.robots:
            self._blit_robot(robot)
        for bullet in self.bullets:
            self._blit_bullet(bullet)
        self._blit_text(f'{self.time_remaining / UNITS.s:.1f}', GRAPHIC_GAME.info_coords[0])
        self._blit_text(self.teams[False].damage_taken, GRAPHIC_GAME.info_coords[1])
        self._blit_text(self.teams[True].damage_taken, GRAPHIC_GAME.info_coords[2])
        self._blit_text(self.winner.name, GRAPHIC_GAME.info_coords[3])

    def _blit_zones(self):
        for zone in self.zones.values():
            if zone.is_activated:
                continue
            image = ASSETS.zone[zone.type_]
            rect = image.get_rect()
            rect.center = to_draw_coords(zone.outline.center, offset=GRAPHIC_GAME.offset)
            self._screen.blit(image, rect)

    def _blit_robot(self, robot: Robot):
        if not robot.hp:
            chassis_image = ASSETS.dead_robot
        elif robot.team.is_blue:
            chassis_image = ASSETS.blue_robot
        else:
            chassis_image = ASSETS.red_robot
        chassis_image = pygame.transform.rotate(chassis_image, robot.rotation / UNITS.d)
        gimbal_image = pygame.transform.rotate(ASSETS.gimbal, (robot.gimbal_yaw + robot.rotation) / UNITS.d)
        chassis_rect = chassis_image.get_rect()
        gimbal_rect = gimbal_image.get_rect()
        chassis_rect.center = gimbal_rect.center = to_draw_coords(robot.center, offset=GRAPHIC_GAME.offset)
        self._screen.blit(chassis_image, chassis_rect)
        self._screen.blit(gimbal_image, gimbal_rect)
        self._blit_text(
            f'{(1 if robot.is_one else 2) + (0 if robot.team.is_blue else 2)} | {robot.hp}',
            to_draw_coords(robot.center, offset=GRAPHIC_GAME.robot_label_offset),
            UI.blue if robot.team.is_blue else UI.red)
        self._blit_robot_status(robot)

    def _blit_robot_status(self, robot: Robot):
        row_coords = GRAPHIC_GAME.state_coords[robot.is_one + 2 * robot.team.is_blue]
        self._blit_text(f'{robot.center.x / UNITS.m:.2f}', row_coords[0])
        self._blit_text(f'{robot.center.y / UNITS.m:.2f}', row_coords[1])
        self._blit_text(f'{robot.rotation / UNITS.d:.0f}', row_coords[2])
        self._blit_text(f'{robot.gimbal_yaw / UNITS.d:.0f}', row_coords[3])
        self._blit_text(f'{robot.speed.x / UNITS.ms:.2f}', row_coords[4])
        self._blit_text(f'{robot.speed.y / UNITS.ms:.2f}', row_coords[5])
        self._blit_text(f'{robot.rotation_speed / UNITS.ds:.2f}', row_coords[6])
        self._blit_text(f'{robot.gimbal_yaw_speed / UNITS.ds:.2f}', row_coords[7])
        self._blit_text(f'{robot.ammo}', row_coords[8])
        self._blit_text(f'{robot.heat}', row_coords[9])
        self._blit_text(f'{robot.hp}', row_coords[10])
        self._blit_text(f'{robot.is_shooting}', row_coords[11])
        self._blit_text(f'{robot.shot_cooldown / UNITS.s:.3f}', row_coords[12])
        self._blit_text(f'{robot.barrier_hits}', row_coords[13])
        self._blit_text(f'{robot.robot_hits}', row_coords[14])
        self._blit_text(f'{robot.can_move}', row_coords[15])
        self._blit_text(f'{robot.can_shoot}', row_coords[16])
        self._blit_text(f'{robot.debuff_timeout / UNITS.s:.0f}', row_coords[17])

    def _blit_bullet(self, bullet: Bullet):
        bullet_rect = ASSETS.bullet.get_rect()
        bullet_rect.center = to_draw_coords(bullet.center, offset=GRAPHIC_GAME.offset)
        self._screen.blit(ASSETS.bullet, bullet_rect)

    def _blit_text(self, text: str, position: tuple[float, float], color=UI.black):
        label = self._font.render(str(text), True, color)
        self._screen.blit(label, position)

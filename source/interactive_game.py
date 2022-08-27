import pygame
from graphic_game import GraphicGame
from shared import ASSETS
from robot import RobotCommand, ROBOT


class INTERACTIVE_GAME:
    delay = 18
    short_delay = 0
    guide_coords = (134, 114)


class InteractiveGame:
    def __init__(self):
        self._game = GraphicGame()
        self._selected_index = 0
        self._speed_up = False
        self._view_guide = False
        self._run()

    def _run(self):
        while (commands := self._receive_commands()) is not None:
            self._game.step(*commands)
            self._game._blit()
            if self._view_guide:
                self._game._screen.blit(ASSETS.guide, INTERACTIVE_GAME.guide_coords)  # this is not good
            pygame.display.flip()
            pygame.time.wait(INTERACTIVE_GAME.short_delay if self._speed_up else INTERACTIVE_GAME.delay)

    def _receive_commands(self):
        pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if (event.type == pygame.QUIT) or pressed[pygame.K_ESCAPE]:
                return
        self._speed_up = pressed[pygame.K_LSHIFT]
        self._view_guide = pressed[pygame.K_TAB]

        if pressed[pygame.K_1]:
            self._selected_index = 0
        elif pressed[pygame.K_2]:
            self._selected_index = 1
        elif pressed[pygame.K_3]:
            self._selected_index = 2
        elif pressed[pygame.K_4]:
            self._selected_index = 3

        commands = [RobotCommand() for _ in range(4)]
        commands[self._selected_index] = RobotCommand(
            x_speed=(pressed[pygame.K_w] - pressed[pygame.K_s]) * ROBOT.drive_config.top_speed,
            y_speed=(pressed[pygame.K_q] - pressed[pygame.K_e]) * ROBOT.drive_config.top_speed,
            rotation_speed=(pressed[pygame.K_a] - pressed[pygame.K_d]) * ROBOT.rotation_config.top_speed,
            gimbal_yaw_speed=(pressed[pygame.K_j] - pressed[pygame.K_l]) * ROBOT.gimbal_yaw_config.top_speed,
            shoot=bool(pressed[pygame.K_k]))
        return commands[0:2], commands[2:4]

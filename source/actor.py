import numpy as np

# Indices of important robot properties in state.agents[car_num]
# from source.shared import TIME
from geometry import LineSegment
from source.game.config import FIELD
# # from modules.waypoints.navigator import NavigationGraph
# from modules.waypoints.navigator import Navigator
from source.shared import GameState, RobotState, RobotCommand

OWNER = 0
POS_X = 1
POS_Y = 2
ANGLE = 3
YAW = 4
BULLET_COUNT = 10


def det(v0, v1):
    """
    Returns the determinant of the matrix made from two 2d column vectors, det((v0 v1))
    Helper for navigate()
    """
    return v0[0] * v1[1] - v1[0] * v0[1]


class Actor:
    def __init__(self, actor_id, game_state: GameState):
        """
        Creates an Actor object to control the robot. It requires information about the acting robot's id
        and state, state of all the other robots (for their location), the
        board's buff/debuff zone location, the navigation system, the barrier vertices, all of which are
        initialised at the beginning.
        It also holds
        """

        """ID and status variables"""
        self.actor_id = actor_id
        self.state: RobotState = self.get_robot_state_from_game_state(game_state)

        """Board waypoint variables"""
        self.hp_waypoint = None
        self.no_shoot_waypoint = None
        self.no_move_waypoint = None
        self.ammo_waypoint = None
        self.centre_waypoint = None
        self.spawn_waypoint = None
        self.initialise_waypoints()

        """Navigation variables"""
        self.prev_commands = None
        self.next_waypoint = None
        self.destination = None
        # self.nav = Navigator(pathlib.Path('modules', 'waypoints', 'data.json'))
        # self.robot = robot

        """Auto-aim functionality dependent variables """
        self.barriers = FIELD.low_barriers + FIELD.high_barriers

        """Decision making status variables"""
        self.has_ammo = False
        self.not_shooting = True
        self.has_buff = False
        self.is_at_centre = False
        self.is_at_spawn_zone = False

        """Variable to hold commands that are passed onto the step function"""
        self.next_robot_command: RobotCommand = RobotCommand()

    def get_robot_state_from_game_state(self, game_state: GameState):
        """
        Returns the actor's specific robot state given using its id
        """
        if self.actor_id % 2 == 0:          # If in blue team
            if self.actor_id == 0:
                return game_state.blue_state.robot_states[0]
            else:
                return game_state.blue_state.robot_states[1]
        else:                               # If in red team
            if self.actor_id == 1:
                return game_state.red_state.robot_states[0]
            else:
                return game_state.blue_state.robot_states[1]

    def initialise_waypoints(self):
        """
        Sets up the robots waypoints based on the robot id
        :return:
        """
        # TODO finish this function
        pass

    def commands_from_state(self, state):
        """Testing method for movement and delivery of commands. To be replaced
        by take_action()."""
        self.state = state
        self.destination = self.centre_waypoint
        # x = y = rotate = yaw = shoot = 1
        #
        # destination = np.array([756, 217])
        # pos = self.nearest_waypoint(self.robot.center)
        # dest = self.nearest_waypoint(destination)
        # x, y, rotate = self.navigate(state, pos, dest, [17, 20])
        #
        # commands = [x, y, rotate, yaw, shoot]
        #
        # self.prev_commands = commands
        self.move_to(self.centre_waypoint)
        return self.next_robot_command

    def nearest_waypoint(self, pos):
        """
        TODO complete function documentation
        :param pos: should be np.array([x, y])
        :return:
        """
        return np.argmin([np.linalg.norm(node - pos) for node in self.nav.nodes])

    def get_path(self, from_waypoint, to_waypoint, avoid_nodes=None):
        path = self.nav.navigate(from_waypoint, to_waypoint, avoid_nodes)
        return self.nav.interpolate(path, 20) if path is not None else None

    def set_destination(self, dest):
        """
        Sets the destination to the nearest waypoint, stored as the waypoint number
        :param dest: should be np.array([x, y])
        """
        self.destination = self.nearest_waypoint(dest)

    def navigate(self, state, from_waypoint, to_waypoint, avoid_nodes=None):
        """
        Pathfind to the destination. Returns the x,y,rotation values
        """
        path = self.get_path(from_waypoint, to_waypoint, avoid_nodes)
        if path is None:
            return 0, 0, 0
        target = np.array([path[0][-1], path[1][-1]])
        pos_angle = state.robots[0]['rotation']
        pos_vec = np.array([np.cos(pos_angle * np.pi / 180), np.sin(pos_angle * np.pi / 180)])
        test = state.robots[0]
        test2 = state.robots[0]['x_center']
        pos = np.array([state.robots[0]['x_center'], state.robots[0]['y_center']])

        for t_x, t_y in zip(path[0], path[1]):
            if np.linalg.norm(target - np.array([t_x, t_y])) < np.linalg.norm(target - pos):
                target = np.array([t_x, t_y])
                break

        print('-------')
        print(pos)
        print(target)
        target_angle = np.arctan2(target[1] - pos[1], target[0] - pos[0])
        target_vec = np.array([np.cos(target_angle), np.sin(target_angle)])
        print(pos_vec)
        print(target_vec)

        '''
        :current navigation:
        - if target is in a 90 degree cone that extends out from the front of the robot, go forward
        - else, dont move, just turn
        - angles for kernel, positive down, negative up
        '''
        turn = np.arcsin(det(pos_vec, target_vec))
        print(turn)
        if abs(turn) < 0.12:
            turn = 0

        forward = 0
        if abs(turn / np.pi * 180) < 8:
            forward = 1

        print('-------')
        return forward, 0, np.sign(turn)

    def take_action(self, state):
        """
        Called on every frame by the Actor, it first updates the board state as stored in Actor memory
        Then it checks the current robot state to determine what the next line of action should be.
        It then accordingly modifies the next state command that is returned to kernel on every frame
        :return: The decisions to be made in the next time frame
        """
        self.state = state
        self.prev_commands = self.next_robot_command
        self.update_board_zones()
        if self.has_ammo:
            if self.is_hp_zone_active():
                if self.has_buff:
                    if self.is_at_centre:
                        self.wait()
                    else:
                        self.destination = self.centre_waypoint
                else:
                    self.destination = self.hp_waypoint
            else:
                if self.is_at_centre:
                    self.wait()
                else:
                    self.destination = self.centre_waypoint
            self.move_to()
        else:
            if self.is_ammo_zone_active():
                self.destination = self.ammo_waypoint
            else:
                self.destination = self.spawn_waypoint
            self.rush_to()

        return self.next_robot_command

    def update_board_zones(self):
        """
        Updates the Actor's brain with known values of the buff/debuff zones
        TODO Update with new kernel implementation
        """
        if self.state.time % TIME.zone_reset == 0:
            if self.robot.is_blue:
                # Team blue waypoints
                self.ammo_waypoint = self.state.zones.get_center_by_type('ammo_blue')
                self.hp_waypoint = self.state.zones.get_center_by_type('hp_blue')
            else:
                # Team red waypoints
                self.ammo_waypoint = self.state.zones.get_center_by_type('ammo_red')
                self.hp_waypoint = self.state.zones.get_center_by_type('hp_red')
        self.no_shoot_waypoint = self.state.zones.get_center_by_type('no_shoot')
        self.no_move_waypoint = self.state.zones.get_center_by_type('no_move')

    def scan_for_enemies(self):
        """
        Scans the nearby vicinity of the robot using LiDAR + Camera implementation and returns the id of the first
        robot that is visible. Returns None if no robots are visible
        """
        camera_enemies = self.get_camera_vision()
        if camera_enemies == -1:
            lidar_enemies = self.get_lidar_vision()
            if lidar_enemies == -1:
                return None
            else:
                return lidar_enemies
        else:
            return camera_enemies

    def aim_then_shoot(self, scanned_enemy):
        """
        Makes the robot chassis aim towards the robot specified. If the robot is already locked on to the enemy
        in a straight line, it modifies the next state to shoot
        :param scanned_enemy:
        :return:
        """
        theta = np.rad2deg(np.arctan(45 / 60))
        delta_x, delta_y = self.state.robots[scanned_enemy].center - self.robot.center
        relative_angle = np.angle(delta_x + delta_y * 1j, deg=True) - self.state.robots[scanned_enemy].rotation
        # Normalize angle
        if relative_angle >= 180: relative_angle -= 360
        if relative_angle <= -180: relative_angle += 360

        if -theta <= relative_angle < theta:
            armor = self.get_relative_robot_vertices(self.state.robots[scanned_enemy], 2)
        elif theta <= relative_angle < 180 - theta:
            armor = self.get_relative_robot_vertices(self.state.robots[scanned_enemy], 3)
        elif -180 + theta <= relative_angle < -theta:
            armor = self.get_relative_robot_vertices(self.state.robots[scanned_enemy], 1)
        else:
            armor = self.get_relative_robot_vertices(self.state.robots[scanned_enemy], 0)
        delta_x, delta_y = armor - self.robot.center
        adjustment_angle = np.angle(delta_x + delta_y * 1j, deg=True) - self.robot.yaw - self.robot.rotation
        if adjustment_angle >= 180: adjustment_angle -= 360
        if adjustment_angle <= -180: adjustment_angle += 360
        # TODO Debug the adjustment angle to see how it is used to aim
        pass

    def wait(self):
        """
        Scans the robot's nearby environment for enemies to shoot, does not move
        :return:
        """
        scanned_enemies = self.scan_for_enemies()
        if scanned_enemies is not None:
            self.aim_then_shoot(scanned_enemies)
        else:
            # TODO should set location and rotation delta values to zero to stop movment
            pass

    def move_to(self, waypoint=10):
        """
        Scans the robot's nearby environment for enemies to shoot and sets the robots next_state_commands
        such that it moves towards its set waypoint
        :param waypoint:
        :return:
        """
        # scanned_enemies = self.scan_for_enemies()
        # if scanned_enemies is not None:
        #     self.aim_then_shoot(scanned_enemies)
        # else:
        pos = self.nearest_waypoint(self.robot.center)
        dest = self.destination if self.destination is not None else waypoint
        # TODO: Update this function call when the new version of navigate is implemented
        x, y, rotate = self.navigate(self.state, pos, dest, [3, 10])

        yaw = shoot = 0
        self.next_robot_command = [x, y, rotate, yaw, shoot]

    def rush_to(self):
        """
        Sets robot to navigate to the destination waypoint without checking for enemies
        Does so by modifying the d
        :param waypoint:
        :return:
        """
        """
        TODO Complete implementation. Should pass in robot coordinates and/or rotation value to navigation
        system, which returns location and/or rotation delta values for the next_robot_command
        """
        pass

    def is_ammo_zone_active(self):
        """
        Checks if the supply zone is has not been activated yet from the current board zone info
        TODO Update with new kernel implementation
        """
        if self.robot.is_blue:
            return self.state.zones.is_zone_active('ammo_blue')
        else:
            return self.state.zones.is_zone_active('ammo_red')

    def is_hp_zone_active(self):
        """
        Checks if the ammo zone has not been activated yet from the current board zone info
        TODO Update with new kernel implementation
        """
        if self.robot.is_blue:
            return self.state.zones.is_zone_active('hp_blue')
        else:
            return self.state.zones.is_zone_active('hp_red')

    def get_lidar_vision(self):
        """
        Check's if the current acting robot can see other robots using camera vision, and returns id of the first
        visible robot
        Returns -1 if no robot can be seen
        TODO Update with new kernel implementation
        """
        robot_id = self.robot.id_
        robot_coordinates = self.robot.center
        for offset_index in range(len(self.state.robots - 1)):
            if robot_id % 2 == 0:
                # If the robot is in the blue team
                if self.state.robots[robot_id - offset_index - 1].id_ % 2 == 0:
                    # Only scan for red team robots and not blue team
                    continue
            else:
                # If the robot is in the red team
                if self.state.robots[robot_id - offset_index - 1].id_ % 2 == 1:
                    # Only scan for blue team robots and not red team
                    continue
            other_robot_coordinates = self.state.robots[robot_id - offset_index - 1].center
            delta_x, delta_y = other_robot_coordinates - robot_coordinates
            angle = np.angle(delta_x + delta_y * 1j, deg=True)
            if angle >= 180: angle -= 360
            if angle <= -180: angle += 360
            angle = angle - self.robot.rotation
            if angle >= 180: angle -= 360
            if angle <= -180: angle += 360
            if abs(angle) < 60:
                if self.line_intersects_barriers(robot_coordinates, other_robot_coordinates) \
                        or self.line_intersects_robots(robot_coordinates, other_robot_coordinates):
                    pass
                else:
                    return self.state.robots[robot_id - offset_index - 1].id_
            else:
                pass

        return -1

    def get_camera_vision(self):
        """
        Check's if the current acting robot can see other robots using camera vision, and returns id of the first
        visible robot
        Returns -1 if no robot can be seen
        TODO Update with new kernel implementation
        """
        robot_id = self.robot.id_
        robot_coordinates = self.robot.center
        for offset_index in range(len(self.state.robots - 1)):
            if robot_id % 2 == 0:
                # If the robot is in the blue team
                if self.state.robots[robot_id - offset_index - 1].id_ % 2 == 0:
                    # Only scan for red team robots and not blue team
                    continue
            else:
                # If the robot is in the red team
                if self.state.robots[robot_id - offset_index - 1].id_ % 2 == 1:
                    # Only scan for blue team robots and not red team
                    continue
            other_robot_coordinates = self.state.robots[robot_id - offset_index - 1].center
            delta_x, delta_y = other_robot_coordinates - robot_coordinates
            angle = np.angle(delta_x + delta_y * 1j, deg=True)
            if angle >= 180: angle -= 360
            if angle <= -180: angle += 360
            # Get relative angle
            angle = angle - self.robot.yaw - self.robot.rotation
            if angle >= 180: angle -= 360
            if angle <= -180: angle += 360
            if abs(angle) < 37.5:
                if self.line_intersects_barriers(robot_coordinates, other_robot_coordinates) \
                        or self.line_intersects_robots(robot_coordinates, other_robot_coordinates):
                    pass
                else:
                    return self.state.robots[robot_id - offset_index - 1].id_
            else:
                pass

        return -1

    """Low-level enemy scanning functions below"""

    def cross_product(self, p1, p2, p3):
        """
        Given 3 points p1, p2, p3, it calculates the cross product of p1->p2 and p1->p3 vectors.
        Hence it returns 0 if all 3 line on the same line, a non-zero value otherwise
        """
        x1 = p2[0] - p1[0]
        y1 = p2[1] - p1[1]
        x2 = p3[0] - p1[0]
        y2 = p3[1] - p1[1]
        return x1 * y2 - x2 * y1

    def get_robot_outline(self, robot):
        """
        Given a robot object, it returns the coordinates of its vertices based on the robot's rotation values
        """
        rotate_matrix = np.array([[np.cos(-np.deg2rad(robot.rotation + 90)),
                                   -np.sin(-np.deg2rad(robot.rotation + 90))],
                                  [np.sin(-np.deg2rad(robot.rotation + 90)),
                                   np.cos(-np.deg2rad(robot.rotation + 90))]])
        xs = np.array([[-22.5, -30], [22.5, 30], [-22.5, 30], [22.5, -30]])
        return [np.matmul(xs[i], rotate_matrix) + robot.center for i in range(xs.shape[0])]

    def get_relative_robot_vertices(self, robot, direction):
        """
        Helper function for aiming at another robot
        Returns transformed vertices of the other robot
        """
        rotate_matrix = np.array([[np.cos(-np.deg2rad(robot.rotation + 90)),
                                   -np.sin(-np.deg2rad(robot.rotation + 90))],
                                  [np.sin(-np.deg2rad(robot.rotation + 90)),
                                   np.cos(-np.deg2rad(robot.rotation + 90))]])
        xs = np.array([[0, -30], [18.5, 0], [0, 30], [-18.5, 0]])
        return np.matmul(xs[direction], rotate_matrix) + robot.center

    def segment(self, p1, p2, p3, p4):
        if (max(p1[0], p2[0]) >= min(p3[0], p4[0])
                and max(p3[0], p4[0]) >= min(p1[0], p2[0])
                and max(p1[1], p2[1]) >= min(p3[1], p4[1])
                and max(p3[1], p4[1]) >= min(p1[1], p2[1])):
            if (self.cross_product(p1, p2, p3) * self.cross_product(p1, p2, p4) <= 0
                    and self.cross_product(p3, p4, p1) * self.cross_product(p3, p4, p2) <= 0):
                return True
            else:
                return False
        else:
            return False

    def line_rect_check(self, l1, l2, sq):
        # this part code came from: https://www.jianshu.com/p/a5e73dbc742a
        # check if line cross rect, sq = [x_leftdown, y_leftdown, x_rightup, y_rightup]
        p1 = [sq[0], sq[1]]
        p2 = [sq[2], sq[3]]
        p3 = [sq[2], sq[1]]
        p4 = [sq[0], sq[3]]
        if self.segment(l1, l2, p1, p2) or self.segment(l1, l2, p3, p4):
            return True
        else:
            return False

    def line_intersects_barriers(self, point1, point2):
        """
        Given two points, it checks if the line created by those points intersect any map barrier
        """
        line = LineSegment(point1, point2)
        for barrier in self.barriers:
            if barrier.intersects(line):
                return True
        return False

    def line_intersects_robots(self, robot_center1, robot_center2):
        """
        Given the center coordinates of two robots, it checks if any other robots are between the straight line
        connecting them
        """
        for robot in self.state.robots:
            if (robot.center == robot_center1).all() or (robot.center == robot_center2).all():
                # Performing comparison with the current robots, so pass onto next loop
                continue
            vertex1, vertex2, vertex3, vertex4 = self.get_robot_outline(robot)
            if self.segment(robot_center1, robot_center2, vertex1, vertex2) \
                    or self.segment(robot_center1, robot_center2, vertex3, vertex4):
                return True
        return False
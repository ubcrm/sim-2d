from robot import Robot


class Team:
    def __init__(self, is_blue: bool):
        self.is_blue = is_blue
        self.damage_taken = 0
        self.robots = {
            True: Robot(True, self),
            False: Robot(False, self)
        }

    def take_damage(self, damage):
        self.damage_taken += damage

    def apply_hp_buff(self):
        self.robots[True].apply_hp_buff()
        self.robots[False].apply_hp_buff()

    def apply_ammo_buff(self):
        self.robots[True].apply_ammo_buff()
        self.robots[False].apply_ammo_buff()

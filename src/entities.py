# src/entities.py
class Player:
    def __init__(self, hp, base_attack):
        self.hp = hp
        self.base_attack = base_attack
        self.combo_count = 0

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0

    def calculate_damage(self):
        multiplier = 1.0 + (self.combo_count * 0.2)
        return int(self.base_attack * multiplier)

class Enemy:
    def __init__(self, name, max_hp, attack_power):
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack_power = attack_power

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0:
            self.current_hp = 0

    def attack_player(self, player):
        player.take_damage(self.attack_power)

class Boss(Enemy):
    def __init__(self, name, max_hp, attack_power, enrage_threshold):
        super().__init__(name, max_hp, attack_power)
        self.special_attack_charge = 0
        self.enrage_threshold = enrage_threshold

    def cast_special_skill(self, player):
        if self.special_attack_charge >= 3:
            player.take_damage(self.attack_power * 2)
            self.special_attack_charge = 0
        else:
            self.attack_player(player)
            self.special_attack_charge += 1
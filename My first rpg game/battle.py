from models import Player, Enemy
import random
import pygame

class Battle:
    def __init__(self, game, enemy):
        self.game = game            
        self.player = game.player   
        self.enemy = enemy          
        self.last_attack_time = pygame.time.get_ticks()
        self.last_enemy_attack_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        # Гравець атакує ворога
        if current_time - self.last_attack_time > 2000:
            self.enemy.health -= self.player.attack
            self.game.add_message(f"Ви нанесли {self.player.attack} шкоди ворогу. HP ворога: {max(self.enemy.health, 0)}")
            self.last_attack_time = current_time

            if self.enemy.health <= 0:
                self.game.add_message("Ворог переможений!")
                experience_gained = random.randint(10, 20)
                self.player.experience += experience_gained
                self.game.add_message(f"Ви отримали {experience_gained} досвіду.")
                self.game.check_level_up()
                self.game.random_stat_improvement()
                self.enemy.delete()
                self.game.enemies.remove(self.enemy)
                self.player.save()
                self.game.current_battle = None
                self.game.game_state = 'exploration'
                return

        # Ворог атакує гравця
        if current_time - self.last_enemy_attack_time > 3000:
            self.player.health -= self.enemy.attack
            self.game.add_message(f"Ворог наніс {self.enemy.attack} шкоди вам. Ваше HP: {max(self.player.health, 0)}")
            self.last_enemy_attack_time = current_time

            if self.player.health <= 0:
                self.game.add_message("Гравець зазнав поразки!")
                self.game.game_state = 'game_over'
                self.game.current_battle = None

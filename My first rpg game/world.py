import pygame
import os

class Renderer:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.WIDTH = game.WIDTH
        self.HEIGHT = game.HEIGHT
        self.font = game.font
        self.stats_font = game.stats_font

        images_path = os.path.join('images')
        pygame.display.flip()

        # Завантаження фону
        self.background_img = pygame.image.load(os.path.join(images_path, 'background.png')).convert()
        self.background_img = pygame.transform.scale(self.background_img, (self.WIDTH, self.HEIGHT))

        # Завантаження зображення стіни
        self.wall_img = pygame.image.load(os.path.join(images_path, 'wall.png')).convert_alpha()

        self.enemy_img = pygame.image.load(os.path.join(images_path, 'enemy.png')).convert_alpha()
        self.enemy_img = pygame.transform.scale(self.enemy_img, (40, 40)) 
        self.enemy_img.set_colorkey((255, 255, 255))  

    def draw_room(self):
        self.screen.blit(self.background_img, (0, 0))

        for wall in self.game.current_room.walls:
            wall_rect = wall.rect
            wall_image = pygame.transform.scale(self.wall_img, (wall_rect.width, wall_rect.height))
            self.screen.blit(wall_image, wall_rect)
        
        self.game.player.sprite.update_animation(self.game.player.direction)
        self.game.player.sprite.draw(self.screen, self.game.player.x, self.game.player.y)

        if self.game.game_state != 'battle':
            for enemy in self.game.enemies:
                enemy_rect = self.enemy_img.get_rect(center=(enemy.x + 20, enemy.y + 20))
                self.screen.blit(self.enemy_img, enemy_rect)

        self.draw_player_stats()
        self.display_messages()

        if self.game.game_state == 'battle' and self.game.current_battle:
            enemy_hp_text = self.stats_font.render(f"HP ворога: {self.game.current_battle.enemy.health}", True, (255, 0, 0))
            enemy_hp_rect = enemy_hp_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 - 50))
            self.screen.blit(enemy_hp_text, enemy_hp_rect)
        pygame.display.flip()

    def draw_player_stats(self):
        name_text = self.stats_font.render(f"{self.game.player.name} (Рівень {self.game.player.level})", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(self.WIDTH // 2, 10))
        self.screen.blit(name_text, name_rect)

        hp_text = self.stats_font.render(f"HP: {self.game.player.health}/{self.game.player.max_health}", True, (255, 0, 0))
        hp_rect = hp_text.get_rect(center=(self.WIDTH // 2, 40))
        self.screen.blit(hp_text, hp_rect)

    def display_messages(self):
        current_time = pygame.time.get_ticks()
        self.game.messages = [(text, timestamp) for text, timestamp in self.game.messages if current_time - timestamp < self.game.message_duration]

        max_messages_to_display = 3
        for i, (text, _) in enumerate(reversed(self.game.messages[-max_messages_to_display:])):
            message_text = self.font.render(text, True, (255, 255, 255))
            message_rect = message_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 20 - i * 30))
            self.screen.blit(message_text, message_rect)

    def draw_text_input(self, text):
        input_box = pygame.Rect(self.WIDTH // 2 - 100, self.HEIGHT // 2 - 20, 200, 40)
        pygame.draw.rect(self.screen, (255, 255, 255), input_box)
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, (0, 0, 0))
        self.screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))
        prompt_surface = font.render("Введіть ім'я персонажа:", True, (255, 255, 255))
        self.screen.blit(prompt_surface, (self.WIDTH // 2 - 150, self.HEIGHT // 2 - 60))

        
    

class PlayerSprite:
    def __init__(self, sprite_sheet_path):
        if not os.path.isfile(sprite_sheet_path):
            print(f"Помилка: Файл {sprite_sheet_path} не знайдено!")
            return
        
        self.sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        self.frame_width = self.sprite_sheet.get_width() // 4  
        self.frame_height = self.sprite_sheet.get_height() // 4  
        self.animations = self.load_sprites()
        self.current_animation = self.animations["down"]
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_delay = 150  
    def load_sprites(self):
        animations = {
            "down": [], "left": [], "right": [], "up": []
        }
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            for col in range(4): 
                frame = self.sprite_sheet.subsurface(
                    pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
                )
                animations[direction].append(frame)

        return animations

    def update_animation(self, direction):
        self.current_animation = self.animations[direction]
        current_time = pygame.time.get_ticks()

        if current_time - self.last_update > self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.current_animation)
            self.last_update = current_time

    def draw(self, screen, x, y):
        screen.blit(self.current_animation[self.frame_index], (x, y))




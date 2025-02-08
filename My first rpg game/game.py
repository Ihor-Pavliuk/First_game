import pygame
import random
from database import initialize_database
from models import Room, Player, Enemy
from battle import Battle
from end_game import EndGameHandler
from world import Renderer, PlayerSprite
from database import get_db_cursor


def experience_to_next_level(level):
    return 50 * (level ** 2)

class Game:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.input_active = True
        self.player_name = ""
        self.stats_font = pygame.font.SysFont(None, 24)
        self.messages = []  
        self.message_duration = 3000  
        self.last_message_time = 0 
        self.game_state = 'exploration'
        self.current_battle = None
        self.player_sprite = PlayerSprite("images/player.gif") 
                
        initialize_database()
        self.player = Player.load()
        self.current_room = Room.load(self.player.current_room_id)
        
        if self.player.name:
            self.input_active = False
            self.player_name = self.player.name
        else:
            self.input_active = True
            self.player_name = ""

 
        if not self.current_room:
            self.add_message(f"Помилка: кімната {self.player.current_room_id} не знайдена! Створюється базова.")
            self.current_room = Room(
                id=1,
                x=0,
                y=0,
                width=self.WIDTH,
                height=self.HEIGHT,
                up_room_id=None,
                down_room_id=None,
                left_room_id=None,
                right_room_id=2 
            )
        self.enemies = Enemy.load_all(self.player.current_room_id)

        self.player_img = pygame.Surface((40, 40))
        self.enemy_img = pygame.Surface((40, 40))
        self.room_img = pygame.Surface((40, 40))

        self.renderer = Renderer(self)
        self.end_game_handler = EndGameHandler(self)
        
        self.transitioning = False
        self.transition_direction = None

    def handle_collisions(self):
        if self.transitioning:
            return

        player_rect = pygame.Rect(self.player.x, self.player.y, 40, 40)
        transition_zones = {
            'left': pygame.Rect(0, 0, 5, self.HEIGHT),
            'right': pygame.Rect(self.WIDTH - 5, 0, 5, self.HEIGHT),
            'up': pygame.Rect(0, 0, self.WIDTH, 5),
            'down': pygame.Rect(0, self.HEIGHT - 5, self.WIDTH, 5)
        }

        for direction, zone in transition_zones.items():
            if player_rect.colliderect(zone):
                self.transitioning = True
                self.transition_direction = direction
                return

        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 40, 40)
            if player_rect.colliderect(enemy_rect):
                self.game_state = 'battle'
                self.current_battle = Battle(self, enemy)
                self.add_message(f"Битва з ворогом (HP: {enemy.health})!")
                break

            
    def add_message(self, text):
        self.messages.append((text, pygame.time.get_ticks()))

    def restart_game(self):
        self.player.level = 1
        self.player.experience = 0
        self.player.max_health = 100
        self.player.health = self.player.max_health
        self.player.attack = 10
        self.player.defense = 5
        self.player.x, self.player.y = 400, 200
        self.player.current_room_id = 1
        self.player.save()
        
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM enemies")
        
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE rooms SET visited = FALSE")
        
        self.current_room = Room.load(self.player.current_room_id)
        self.enemies = []
        self.generate_enemies_for_room(self.current_room)
        self.current_room.visited = True
        self.current_room.save()
        
        self.center_enemies()
        self.messages.clear()
        self.game_state = 'exploration'
        self.current_battle = None

    def move_player(self, dx, dy):
        new_x = self.player.x + dx * Player.MOVE_SPEED
        new_y = self.player.y + dy * Player.MOVE_SPEED

        player_rect = pygame.Rect(new_x, new_y, 40, 40)

        collision = False
        for wall in self.current_room.walls:
            if player_rect.colliderect(wall.rect):
                collision = True
                break

        if not collision:
            self.player.x = new_x
            self.player.y = new_y
            self.player.save()

    def update_room(self):
        if not self.transitioning or not self.transition_direction:
            return

        direction = self.transition_direction
        self.transition_direction = None
        self.move_to_room(direction)

    def move_to_room(self, direction):
        current_direction_id = getattr(self.current_room, f"{direction}_room_id")

        if current_direction_id in (None, -1):
            new_room = Room.create(prev_room=self.current_room, from_direction=direction)
            setattr(self.current_room, f"{direction}_room_id", new_room.id)
            self.current_room.save()
            current_direction_id = new_room.id

        self.current_room = Room.load(current_direction_id)

        transition_positions = {
            'left': (self.current_room.width - 40, self.current_room.height // 2 - 20),
            'right': (0, self.current_room.height // 2 - 20), 
            'up': (self.current_room.width // 2 - 20, self.current_room.height - 40),
            'down': (self.current_room.width // 2 - 20, 0)
        }

        self.WIDTH = self.current_room.width
        self.HEIGHT = self.current_room.height

        if not self.current_room.visited:
            self.generate_enemies_for_room(self.current_room)
            self.current_room.visited = True
            self.current_room.save()
        else:
            self.enemies = Enemy.load_all(self.current_room.id)
            self.center_enemies()

        self.player.x, self.player.y = transition_positions[direction]
        self.player.current_room_id = self.current_room.id
        self.player.save()

        self.transitioning = False



    def generate_enemies_for_room(self, room):
        self.enemies = []
        while len(self.enemies) < 1:
            enemy_x = random.randint(0, room.width - 40)
            enemy_y = random.randint(0, room.height - 40)
            
            if not room.is_wall(enemy_x, enemy_y):
                enemy = Enemy.create(x=enemy_x, y=enemy_y, health=50, attack=10, defense=5, current_room_id=room.id)
                self.enemies.append(enemy)

    def center_enemies(self):
        for enemy in self.enemies:
            max_attempts = 100
            attempts = 0
            while attempts < max_attempts:
                enemy.x = random.randint(0, self.WIDTH - 40)
                enemy.y = random.randint(0, self.HEIGHT - 40)
                enemy_rect = pygame.Rect(enemy.x, enemy.y, 40, 40)
                collision = False
                for wall in self.current_room.walls:
                    if enemy_rect.colliderect(wall.rect):
                        collision = True
                        break
                if not collision:
                    enemy.update_position()
                    break
                attempts += 1
            else:
                print("Не вдалося знайти позицію для ворога без зіткнення зі стінами.")



    def get_movement(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        return dx, dy 

    def check_level_up(self):
        next_level_exp = experience_to_next_level(self.player.level)
        while self.player.experience >= next_level_exp and self.player.level < 100:
            self.player.experience -= next_level_exp
            self.player.level += 1
            self.player.max_health += 10
            self.add_message(f"Вітаємо! Ви досягли рівня {self.player.level}.")
            self.add_message(f"Ваше максимальне HP збільшено до {self.player.max_health}.")
            self.player.health = self.player.max_health
            next_level_exp = experience_to_next_level(self.player.level)
        if self.player.level >= 100:
            self.end_game_handler.end_game() 

    def random_stat_improvement(self):
        improvements = [
            ('attack', 2, "Ви отримали +2 до атаки!"),
            ('defense', 1, "Ви отримали +1 до захисту!"),
            ('health_restore', 25, "Ви відновили 25 HP!"),
            ('max_health', 10, "Ваше максимальне HP збільшено на 10!")
        ]
        stat, value, message = random.choice(improvements)
        if stat == 'attack':
            self.player.attack += value
        elif stat == 'defense':
            self.player.defense += value
        elif stat == 'health_restore':
            self.player.health = min(self.player.health + value, self.player.max_health)
        elif stat == 'max_health':
            self.player.max_health += value
        self.add_message(message)


    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.input_active:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.player.name = self.player_name.strip()
                            if self.player.name:
                                self.input_active = False
                                self.player.save()
                                print(f"Ім'я гравця збережено: {self.player.name}")
                            else:
                                self.add_message("Ім'я не може бути порожнім!")
                        elif event.key == pygame.K_BACKSPACE:
                            self.player_name = self.player_name[:-1]
                        else:
                            self.player_name += event.unicode

            self.screen.fill((0, 0, 0)) 

            if self.input_active:
                self.renderer.draw_text_input(self.player_name) 
            else:
                if self.game_state == 'exploration':
                    self.handle_collisions()
                    self.update_room()
                    dx, dy = self.get_movement()
                    self.move_player(dx, dy)
                elif self.game_state == 'battle':
                    self.current_battle.update()
                elif self.game_state == 'game_over':
                    self.end_game_handler.game_over()
                
                self.renderer.draw_room()
                self.player_sprite.update_animation("down")
                self.player_sprite.draw(self.screen, self.player.x, self.player.y) 

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()

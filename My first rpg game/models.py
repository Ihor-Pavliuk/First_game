from database import get_db_cursor
import random
import pygame
from world import PlayerSprite

class Room:
    def __init__(self, id, x, y, width, height, up_room_id, down_room_id, left_room_id, right_room_id, visited=False):
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.up_room_id = up_room_id
        self.down_room_id = down_room_id
        self.left_room_id = left_room_id
        self.right_room_id = right_room_id
        self.visited = visited
        self.walls = self.create_walls()

    def create_walls(self):
        walls = []
        walls.append(Wall(0, 0, 300, 200))
        walls.append(Wall(self.width - 300, 0, 300, 200))
        walls.append(Wall(0, self.height - 200, 300, 200))
        walls.append(Wall(self.width - 300, self.height - 200, 300, 200))
        return walls
    
    def is_wall(self, x, y):
        for wall in self.walls:
            if wall.rect.collidepoint(x, y):
                return True
        return False

    @classmethod
    def create(cls, prev_room=None, from_direction=None):
        with get_db_cursor() as cursor:

            new_room = cls(
                id=None, 
                x=0, y=0,  
                width=800,
                height=600,
                up_room_id=None,
                down_room_id=None,
                left_room_id=None,
                right_room_id=None
            )

            cursor.execute("""
                INSERT INTO rooms 
                (x, y, width, height, up_room_id, down_room_id, left_room_id, right_room_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (new_room.x, new_room.y, new_room.width, new_room.height,
                  new_room.up_room_id, new_room.down_room_id, 
                  new_room.left_room_id, new_room.right_room_id))
            new_room.id = cursor.fetchone()[0]

            if prev_room and from_direction:
                opposite_dir = {'left': 'right', 'right': 'left', 
                               'up': 'down', 'down': 'up'}[from_direction]
                setattr(new_room, f"{opposite_dir}_room_id", prev_room.id)
                setattr(prev_room, f"{from_direction}_room_id", new_room.id)
                
                cursor.execute(f"""
                    UPDATE rooms 
                    SET {from_direction}_room_id = %s 
                    WHERE id = %s
                """, (new_room.id, prev_room.id))
            

            directions = ['up', 'down', 'left', 'right']
            if opposite_dir in directions:
                directions.remove(opposite_dir)
            new_directions = random.sample(directions, k=random.randint(1, 3))
            
            for dir in new_directions:
                setattr(new_room, f"{dir}_room_id", -1)  # Заглушка для майбутніх кімнат
            
            cursor.execute("""
                UPDATE rooms SET
                    up_room_id = %s,
                    down_room_id = %s,
                    left_room_id = %s,
                    right_room_id = %s
                WHERE id = %s
            """, (new_room.up_room_id, new_room.down_room_id,
                 new_room.left_room_id, new_room.right_room_id,
                 new_room.id))
            
            new_room.right_room_id = -1  # Заглушка для наступних кімнат
            new_room.save()
            
            return new_room
    @classmethod
    def load(cls, current_room_id):
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM rooms WHERE id = %s", (current_room_id,))
            room_data = cursor.fetchone()
            
            if room_data:
                columns = [desc[0] for desc in cursor.description]
                room_dict = dict(zip(columns, room_data))
                
                return cls(
                    id=room_dict['id'],
                    x=room_dict['x'],
                    y=room_dict['y'],
                    width=room_dict['width'],
                    height=room_dict['height'],
                    up_room_id=room_dict['up_room_id'],
                    down_room_id=room_dict['down_room_id'],
                    left_room_id=room_dict['left_room_id'],
                    right_room_id=room_dict['right_room_id'],
                    visited=room_dict['visited']
                )
            return None
    def save(self):
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE rooms SET
                    x = %s,
                    y = %s,
                    width = %s,
                    height = %s,
                    up_room_id = %s,
                    down_room_id = %s,
                    left_room_id = %s,
                    right_room_id = %s,
                    visited = %s
                WHERE id = %s
            """, (
                self.x, self.y, self.width, self.height,
                self.up_room_id, self.down_room_id,
                self.left_room_id, self.right_room_id,
                self.visited,
                self.id
            ))

    
class Player:
    MOVE_SPEED = 5

    def __init__(self, x, y, current_room_id=1, health=100, max_health=100, attack=10, defense=5, experience=0, level=1, name="", sprite_path="default_path"):
        self.x = x
        self.y = y
        self.current_room_id = current_room_id
        self.health = health
        self.max_health = max_health
        self.attack = attack
        self.defense = defense
        self.experience = experience
        self.level = level
        self.name = name
        self.direction = "down"
        self.sprite = PlayerSprite(sprite_path)

    @classmethod
    def load(cls, name=None):
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT x, y, current_room_id, health, max_health, attack, defense, experience, level, name
                FROM player WHERE id = 1
            """)
            data = cursor.fetchone()
            if data is None:
                print("Гравець не знайдений у БД. Створюємо нового...")
                player = cls(350, 200, name=name, sprite_path="images/player.gif")
                player.save()
                return player
            else:
                x, y, current_room_id, health, max_health, attack, defense, experience, level, name_from_db = data
                if not name:
                    name = name_from_db
                print(f"Дані завантажені з БД: {data}")
                return cls(x, y, current_room_id, health, max_health, attack, defense, experience, level, name, sprite_path="images/player.gif")

    def save(self, name=None):
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO player (id, x, y, health, max_health, attack, defense, experience, level, current_room_id, name)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    x = EXCLUDED.x,
                    y = EXCLUDED.y,
                    health = EXCLUDED.health,
                    max_health = EXCLUDED.max_health,
                    attack = EXCLUDED.attack,
                    defense = EXCLUDED.defense,
                    experience = EXCLUDED.experience,
                    level = EXCLUDED.level,
                    current_room_id = EXCLUDED.current_room_id,
                    name = EXCLUDED.name
            """, (self.x, self.y, self.health, self.max_health, self.attack, self.defense, self.experience, self.level, self.current_room_id, self.name))
    

class Enemy:
    def __init__(self, id, x, y, health, attack, defense, current_room_id):
        self.id = id
        self.x = x
        self.y = y
        self.health = health
        self.attack = attack
        self.defense = defense
        self.current_room_id = current_room_id
        

    @classmethod
    def load_all(cls, current_room_id):
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, x, y, health, attack, defense, current_room_id FROM enemies WHERE current_room_id = %s
            """, (current_room_id,))
            enemies_data = cursor.fetchall()
            enemies = [cls(*data) for data in enemies_data]
            return enemies

    @classmethod
    def create(cls, x, y, health, attack, defense, current_room_id):
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO enemies (x, y, health, attack, defense, current_room_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (x, y, health, attack, defense, current_room_id))
            enemy_id = cursor.fetchone()[0]

        return cls(enemy_id, x, y, health, attack, defense, current_room_id)

    def update_position(self):
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE enemies SET x = %s, y = %s WHERE id = %s
            """, (self.x, self.y, self.id))

    def delete(self):
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM enemies WHERE id = %s", (self.id,))



class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

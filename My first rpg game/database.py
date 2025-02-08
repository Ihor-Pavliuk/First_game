import psycopg2
from contextlib import contextmanager

#Не став ховати данні в .env оскільки це зайве в локальній мережі
DATABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    try:
        yield conn 
    finally:
        conn.close() 

@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback() 
            raise
        finally:
            cursor.close() 

def initialize_database():
    with get_db_cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id SERIAL PRIMARY KEY,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            up_room_id INTEGER,
            down_room_id INTEGER,
            left_room_id INTEGER,
            right_room_id INTEGER,
            visited BOOLEAN DEFAULT FALSE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id SERIAL PRIMARY KEY,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 5,
                experience INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                current_room_id INTEGER DEFAULT 1,
                name VARCHAR(50) DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enemies (
                id SERIAL PRIMARY KEY,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                health INTEGER DEFAULT 50,
                attack INTEGER DEFAULT 8,
                defense INTEGER DEFAULT 5,
                current_room_id INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO rooms 
            (x, y, width, height, right_room_id)
            VALUES (0, 0, 800, 600, -1)
            RETURNING id
        """)





#initialize_database()


def clear_database():
    with get_db_cursor() as cursor:
        cursor.execute("TRUNCATE TABLE rooms, player, enemies RESTART IDENTITY CASCADE")



#clear_database()



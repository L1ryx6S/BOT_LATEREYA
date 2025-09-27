import sqlite3
from datetime import datetime
import os
import cv2
from config import DATABASE

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def get_all_prizes(self):
        with self.connection:
            cur = self.connection.cursor()
            cur.execute("SELECT prize_id, image, used FROM prizes")  # Название таблицы и столбцов — уточните по вашей БД
            return cur.fetchall()
        
    def create_tables(self):
        with sqlite3.connect(self.database) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    user_name TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prizes (
                    prize_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image TEXT,
                    used INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    user_id INTEGER,
                    prize_id INTEGER,
                    win_time TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(prize_id) REFERENCES prizes(prize_id),
                    PRIMARY KEY(user_id, prize_id)
                )
            ''')

    def add_user(self, user_id, user_name):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()

            # Проверяем наличие пользователя, чтобы избежать ошибок из-за PRIMARY KEY
            cur.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            if cur.fetchone():
                return False  # Пользователь уже есть

            cur.execute('INSERT INTO users (user_id, user_name) VALUES (?, ?)', (user_id, user_name))
            return True

    def add_prize(self, data):
        # data - список кортежей с именами файлов [('img1.jpg',), ('img2.png',), ...]
        with sqlite3.connect(self.database) as conn:
            conn.executemany('INSERT INTO prizes (image) VALUES (?)', data)

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            # Проверяем, выигрывал ли уже пользователь этот приз
            cur.execute("SELECT 1 FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchone():
                return 0  # Уже выиграл

            cur.execute("INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)", (user_id, prize_id, win_time))
            return 1

    def mark_prize_used(self, prize_id):
        with sqlite3.connect(self.database) as conn:
            conn.execute("UPDATE prizes SET used = 1 WHERE prize_id = ?", (prize_id,))

    def get_users(self):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users")
            rows = cur.fetchall()
            return [row[0] for row in rows]

    def get_prize_img(self, prize_id):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT image FROM prizes WHERE prize_id = ?", (prize_id,))
            res = cur.fetchone()
            if res:
                return res[0]
            return None
        
    def get_all_prizes(self):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT prize_id, image, used FROM prizes")  # Название таблицы и столбцов — уточните по вашей БД
            return cur.fetchall()
        
    def get_random_prize(self):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT prize_id, image, used FROM prizes WHERE used = 0 ORDER BY RANDOM() LIMIT 1")
            res = cur.fetchone()
            # Возвращаем None если нет доступных призов
            return res if res else None

    def get_winners_count(self, prize_id):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM winners WHERE prize_id = ?", (prize_id,))
            res = cur.fetchone()
            return res[0] if res else 0

    def get_rating(self):
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT users.user_name, COUNT(winners.prize_id) as count_prize
                FROM winners
                INNER JOIN users ON users.user_id = winners.user_id
                GROUP BY winners.user_id
                ORDER BY count_prize DESC
                LIMIT 10
            ''')
            return cur.fetchall()
        

        
def hide_img(img_name):
    img_path = f'img/{img_name}'
    hidden_path = f'hidden_img/{img_name}'

    if not os.path.exists(img_path):
        print(f"Изображение {img_path} не найдено.")
        return

    image = cv2.imread(img_path)
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(hidden_path, pixelated_image)

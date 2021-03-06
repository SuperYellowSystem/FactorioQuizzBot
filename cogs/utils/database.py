# ======================================================================
# imports
# ======================================================================
import sqlite3
import os

from language.i18n import I18N

import logging
logger = logging.getLogger(__name__)


# ======================================================================
class Database:
    def __init__(self):
        # Retrieve database path
        path = os.path.dirname(os.path.abspath(__file__))
        if os.name == 'nt':
            index = path.find("\\cogs")
        else:
            index = path.find("/cogs")
        new_path = f'{path[:index]}/data'
        os.makedirs(new_path, exist_ok=True)

        # Path to database
        self.guildDB = f'{new_path}/guilds.db'

        # Cache data
        self.configs = []
        self.scores = []
        self.faqs = []

    # Create tables ====================================================
    @staticmethod
    def _create_config_table(cursor):
        cursor.execute("""CREATE TABLE IF NOT EXISTS guild_config (
                            guild_id INTEGER NOT NULL PRIMARY KEY,
                            prefix TEXT,
                            language TEXT,
                            delete_msg INTEGER)
                       """)

    @staticmethod
    def _create_score_table(cursor):
        cursor.execute("""CREATE TABLE IF NOT EXISTS score (
                            guild_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            score INTEGER,
                            PRIMARY KEY (guild_id, user_id))
                       """)

    @staticmethod
    def _create_faq_table(cursor):
        cursor.execute("""CREATE TABLE IF NOT EXISTS faq (
                            guild_id INTEGER NOT NULL,
                            tag TEXT,
                            content TEXT,
                            image TEXT,
                            timestamp TEXT,
                            creator INTEGER NOT NULL,
                            PRIMARY KEY (guild_id, tag))
                       """)

    def create_tables(self):
        # Create Tables if needed
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self._create_config_table(c)
            self._create_score_table(c)
            self._create_faq_table(c)
        finally:
            conn.commit()
            conn.close()

    # Inputs data ======================================================
    @staticmethod
    def _insert_new_config(cursor, data: dict):
        cursor.execute(" INSERT INTO guild_config(guild_id, prefix, language, delete_msg) VALUES(?, ?, ?, ?)",
                       (data["guild_id"], data["prefix"], data["language"].get_language(), data["delete_msg"],))

    @staticmethod
    def _insert_new_score(cursor, data: dict):
        cursor.execute("""
            INSERT INTO score(guild_id, user_id, score)
            VALUES(:guild_id, :user_id, :score)""", data)

    @staticmethod
    def _insert_new_faq(cursor, data: dict):
        cursor.execute("""
            INSERT INTO faq(guild_id, tag, content, image, timestamp, creator)
            VALUES(:guild_id, :tag, :content, :image, :timestamp, :creator)""", data)

    @staticmethod
    def _update_config(cursor, target: str, new_value, guild_id):
        cursor.execute(f'UPDATE guild_config SET {target} = ? WHERE guild_id = ?', (new_value, guild_id))

    @staticmethod
    def _update_score(cursor, data: dict):
        cursor.execute(f'UPDATE score SET score = ? WHERE guild_id = ? and user_id = ?',
                       (data["score"], data["guild_id"], data["user_id"],))

    @staticmethod
    def _update_faq(cursor, data: dict):
        cursor.execute(f'UPDATE faq SET content = ?, image = ?, timestamp = ? WHERE guild_id = ? AND tag = ?',
                       (data["content"], data["image"], data["timestamp"], data["guild_id"], data["tag"],))

    @staticmethod
    def _is_score_entry_exist(cursor, data: dict):
        cursor.execute("SELECT * FROM score WHERE guild_id = ? and user_id = ?",
                       (data["guild_id"], data["user_id"],))
        return cursor.fetchone() is not None

    def add_new_config(self, data: dict):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self._insert_new_config(c, data)
            conn.commit()
        except Exception as e:
            logger.error("Insert new config failed", e)
        finally:
            conn.close()

    def edit_config(self, target: str, new_value, guild_id):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self._update_config(c, target, new_value, guild_id)
            conn.commit()
        except Exception as e:
            logger.error("Update config failed", e)
        finally:
            conn.close()

    def save_score(self, data: dict):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            if self._is_score_entry_exist(c, data):
                self._update_score(c, data)
            else:
                self._insert_new_score(c, data)
            conn.commit()
        except sqlite3.ProgrammingError:
            logger.error("Programming Error: check syntax and/or number of param specified")
        except Exception as e:
            logger.error("Insert score failed", e)
        finally:
            conn.close()

    def save_faq(self, data: dict):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self._insert_new_faq(c, data)
            conn.commit()
        except Exception as e:
            logger.error("Insert new faq failed", e)
        finally:
            conn.close()

    def edit_faq(self, data: dict):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self._update_faq(c, data)
            conn.commit()
        except Exception as e:
            logger.error("Update faq failed", e)
        finally:
            conn.close()

    # Outputs data =====================================================
    @staticmethod
    def create_config(guild_id, prefix, language, delete_msg):
        return {
            "guild_id": guild_id,
            "prefix": prefix,
            "language": I18N(language),
            "delete_msg": delete_msg,
            "isQuizStarted": False,
            "questions": None
        }

    @staticmethod
    def create_score(guild_id, user_id, score):
        return {
            "guild_id": guild_id,
            "user_id": user_id,
            "score": score,
            "isQuizStarted": False,
            "questions": None
        }

    @staticmethod
    def create_faq(guild_id, tag, content, image, timestamp, creator):
        return {
            "guild_id": guild_id,
            "tag": tag,
            "content": content,
            "image": image,
            "timestamp": timestamp,
            "creator": creator
        }

    def _load_configs(self, cursor):
        config_list = list()
        cursor.execute("SELECT * FROM guild_config")
        for row in cursor:
            config_list.append(self.create_config(row[0], row[1], row[2], True if row[3] == 1 else False))
        return config_list

    def _load_scores(self, cursor):
        score_list = list()
        cursor.execute("SELECT * FROM score")
        for row in cursor:
            score_list.append(self.create_score(row[0], row[1], row[2]))
        return score_list

    def _load_faqs(self, cursor):
        faq_list = list()
        cursor.execute("SELECT * FROM faq")
        for row in cursor:
            faq_list.append(self.create_faq(row[0], row[1], row[2], row[3], row[4], row[5]))
        return faq_list

    def load_data(self):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            self.configs = self._load_configs(c)
            self.scores = self._load_scores(c)
            self.faqs = self._load_faqs(c)
        except Exception as e:
            logger.error("Failed to load data", e)
        finally:
            conn.close()

    # delete data ======================================================
    def delete_config(self, guild_id):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM guild_config WHERE guild_id = ?", (guild_id,))
            conn.commit()
        except Exception as e:
            logger.error("Failed to delete config", e)
        finally:
            conn.close()

    def delete_score(self, guild_id, user_id):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM score WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            conn.commit()
        except Exception as e:
            logger.error("Failed to delete score", e)
        finally:
            conn.close()

    def delete_faq(self, guild_id, tag=None):
        conn = sqlite3.connect(self.guildDB)
        c = conn.cursor()
        try:
            if tag:
                c.execute("DELETE FROM faq WHERE guild_id = ? AND tag = ?", (guild_id, tag,))
            else:
                c.execute("DELETE FROM faq WHERE guild_id = ?", (guild_id,))
            conn.commit()
        except Exception as e:
            logger.error("Failed to delete config", e)
        finally:
            conn.close()


# ======================================================================
# Database simple tests
# ======================================================================
if __name__ == '__main__':
    config_dict = {
        "guild_id": 1234567,
        "prefix": "-",
        "language": "fr",
        "delete_msg": True
    }
    score_dict = {
        "guild_id": 1234567,
        "user_id": 987654,
        "score": 10
    }
    scoreBis_dict = {
        "guild_id": 1234567,
        "user_id": 987654,
        "score": 25
    }

    # set up logging
    logger = logging.getLogger('discord')
    logger.setLevel(3)
    path_to_dir = os.getcwd() + "/logs"
    if not os.path.exists(path_to_dir):
        os.makedirs(path_to_dir)
    handler = logging.FileHandler(filename='logs/db.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    try:
        # Get database
        db = Database()
        db.create_tables()

        # FILL DATABASE ========
        # Insert new config
        db.add_new_config(config_dict)
        # Update new config
        db.edit_config("prefix", "--", config_dict["guild_id"])

        # Insert new score
        db.save_score(score_dict)
        # Update new score
        db.save_score(scoreBis_dict)

        # RETRIEVE DATA ========
        db.load_data()

        for cfg in db.configs:
            print(f'------------------------\n'
                  f'guild: {cfg["guild_id"]}\n'
                  f'prefix: {cfg["prefix"]}\n'
                  f'language: {cfg["language"]}\n'
                  f'delete_msg: {cfg["delete_msg"]}')

        print("\n")

        for s in db.scores:
            print(f'------------------------\n'
                  f'guild: {s["guild_id"]}\n'
                  f'user: {s["user_id"]}\n'
                  f'score: {s["score"]}')

    except Exception as error:
        print("Error", error)

    finally:
        os.remove("../../data/guilds.db")

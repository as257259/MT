import os, random, atexit, pytz, base64
from pathlib import Path
from sqlitedict import SqliteDict
from datetime import datetime
from logger import logger

class Preferences:
    _instance = None
    _db_path = ""

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if db_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(current_dir, "prefs.sqlite")
            else:
                root, ext = os.path.splitext(db_path)
                if ext.lower() != '.sqlite':
                    db_path = root + '.sqlite'
                if not os.path.isabs(db_path):
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    db_path = os.path.join(current_dir, db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            cls._instance._db_path = db_path
            cls._instance._init_or_recreate_db()
            atexit.register(cls._instance.close)
        return cls._instance

    def _init_or_recreate_db(self):
        db_path = self._db_path
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.db = SqliteDict(db_path, autocommit=True)
        except:
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.save()
            except:
                pass
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.db = SqliteDict(db_path, autocommit=True)
            except:
                raise
        try:
            key = f"{self.getTimes()}_{random.uniform(0, 100)}"
            self.put("cs", key)
        except:
            pass

    def get(self, key, default=None):
        try:
            return self.d(self.db.get(self.e(key), self.e(default)))
        except:
            return default

    def put(self, key, value):
        try:
            self.db[self.e(key)] = self.e(value)
            self.db.commit()
        except:
            pass

    def remove(self, key):
        try:
            if self.e(key) in self.db:
                del self.db[self.e(key)]
                self.db.commit()
        except:
            pass

    def clear(self):
        try:
            self.db.clear()
            self.db.commit()
        except:
            pass

    def contains(self, key):
        try:
            return self.e(key) in self.db
        except:
            return None

    def close(self):
        try:
            if hasattr(self, 'db'):
                self.db.close()
            self.__class__._instance = None
        except:
            pass

    def get_db_path(self):
        return self._db_path

    def getTime(self):
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        formatted_date = now.strftime('%Y-%m-%d')
        return formatted_date

    def getTimes(self):
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date

    def e(self, text):
        return base64.b64encode(text.encode()).decode()

    def d(self, encoded_text):
        return base64.b64decode(encoded_text.encode()).decode()

    def save(self):
        db_path = self.get_db_path()
        try:
            os.system('git config --local user.name "github-actions[bot]" >/dev/null 2>&1')
            os.system('git config --local user.email "github-actions[bot]@users.noreply.github.com" >/dev/null 2>&1')
            if os.system(f'git add {db_path} >/dev/null 2>&1') == 0:
                os.system('git commit -m "更新" >/dev/null 2>&1')
                os.system('git pull --quiet --rebase')
                os.system('git push --quiet --force-with-lease')
                logger.info("数据库已更新")
        except:
            pass

prefs = Preferences()
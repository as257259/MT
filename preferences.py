import os, random, atexit, pytz, base64
from pathlib import Path
from sqlitedict import SqliteDict
from datetime import datetime

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
            toDB = SqliteDict(db_path, autocommit=True)
            if toDB:
                self.db = toDB
        except:
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.save()
            except:
                pass
            try:
                toDB = SqliteDict(db_path, autocommit=True)
                if toDB:
                    self.db = toDB
            except:
                raise
        key = f"{self.getTimes()}_{random.uniform(0, 100)}"
        print("测试push", key)
        self.put("cs", key)

    def get(self, key, default=None):
        try:
            return self.d(self.db.get(self.e(key), self.e(default)))
        except:
            return default

    def put(self, key, value):
        try:
            self.db[self.e(key)] = self.e(value)
            self.db.commit()
            self.save()
        except:
            pass

    def remove(self, key):
        try:
            if self.e(key) in self.db:
                del self.db[self.e(key)]
                self.db.commit()
                self.save()
        except:
            pass

    def clear(self):
        try:
            self.db.clear()
            self.db.commit()
            self.save()
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
            os.system(f'git add {db_path} >/dev/null 2>&1')
            if os.system('git diff --cached --quiet') == 0:
                os.system('git commit -m "更新" >/dev/null 2>&1')
                os.system('git pull --quiet origin main >/dev/null 2>&1')
                os.system('git push --quiet origin main >/dev/null 2>&1')
        except:
            pass

prefs = Preferences()
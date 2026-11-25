import sqlite3
from config import DATA
from domain.models import StudyPlan,Event
class Repository:
    def __init__(self,path=None):
        self.path=path or DATA/'study.sqlite3'
        with self.connect() as c:
            c.executescript('CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, payload TEXT); CREATE TABLE IF NOT EXISTS reminders(id TEXT PRIMARY KEY, due TEXT, message TEXT, delivered INTEGER DEFAULT 0);')
    def connect(self): return sqlite3.connect(self.path,timeout=15)
    def save(self,id,plan):
        from datetime import timezone
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO plans VALUES (?,?)',(id,plan.model_dump_json()))
            c.executemany('INSERT OR IGNORE INTO reminders(id,due,message) VALUES (?,?,?)',[(r.id,r.remind_at.astimezone(timezone.utc).isoformat(),r.message) for r in plan.reminders])
    def events(self):
        with self.connect() as c: rows=c.execute('SELECT payload FROM plans').fetchall()
        return [e for row in rows for e in StudyPlan.model_validate_json(row[0]).events]
    def due(self,now):
        with self.connect() as c: return c.execute('SELECT id,message FROM reminders WHERE delivered=0 AND due<=? ORDER BY due',(now,)).fetchall()
    def delivered(self,id):
        with self.connect() as c: c.execute('UPDATE reminders SET delivered=1 WHERE id=?',(id,))

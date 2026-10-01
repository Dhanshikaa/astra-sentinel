import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "sentinel.db"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, date TEXT, source TEXT,
            url TEXT, content TEXT, category TEXT, summary TEXT, keywords TEXT,
            topics TEXT, entities TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        con.commit()

def upsert_article(a):
    with connect() as con:
        con.execute("""INSERT OR REPLACE INTO articles
        (id,title,date,source,url,content,category,summary,keywords,topics,entities)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", tuple(a.get(k, "") for k in
        ["id","title","date","source","url","content","category","summary","keywords","topics","entities"]))
        con.commit()

def get_articles():
    with connect() as con:
        return con.execute("SELECT * FROM articles ORDER BY date DESC, created_at DESC").fetchall()

def get_article(article_id):
    with connect() as con:
        return con.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()

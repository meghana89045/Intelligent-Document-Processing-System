import sqlite3
from .config import DB_PATH

def conn():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, stored_path TEXT,
        document_type TEXT, upload_time TEXT, page_count INTEGER,
        extracted_text TEXT, fields_json TEXT, validation_json TEXT)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_type ON documents(document_type)')
        c.commit()

def insert(r):
    with conn() as c:
        cur=c.execute('''INSERT INTO documents(filename,stored_path,document_type,upload_time,page_count,extracted_text,fields_json,validation_json)
        VALUES(?,?,?,?,?,?,?,?)''', tuple(r[k] for k in ['filename','stored_path','document_type','upload_time','page_count','extracted_text','fields_json','validation_json']))
        c.commit(); return cur.lastrowid

def search(q='', typ='All'):
    sql='SELECT * FROM documents WHERE 1=1'; p=[]
    if q.strip():
        sql += ' AND (filename LIKE ? OR extracted_text LIKE ? OR document_type LIKE ? OR fields_json LIKE ?)'
        x='%'+q.strip()+'%'; p += [x,x,x,x]
    if typ!='All': sql += ' AND document_type=?'; p.append(typ)
    sql += ' ORDER BY id DESC'
    with conn() as c: return c.execute(sql,p).fetchall()

def get(i):
    with conn() as c: return c.execute('SELECT * FROM documents WHERE id=?',(i,)).fetchone()

def stats():
    with conn() as c:
        total=c.execute('SELECT COUNT(*) n FROM documents').fetchone()['n']
        types=c.execute('SELECT document_type,COUNT(*) n FROM documents GROUP BY document_type').fetchall()
    return total,types

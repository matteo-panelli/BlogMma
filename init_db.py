import sqlite3

DATABASE = 'mma.db'

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# Creazione della tabella dei post
c.execute('''
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL
)
''')

# Creazione della tabella dei commenti
c.execute('''
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts (id)
)
''')

conn.commit()
conn.close()

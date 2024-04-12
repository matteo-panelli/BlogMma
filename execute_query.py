import sqlite3

DATABASE = 'mma.db'

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

with open("ciao.sql") as f:
    # Creazione della tabella dei post
    c.executescript(f.read())


conn.commit()
conn.close()

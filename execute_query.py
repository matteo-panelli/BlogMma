import sqlite3
import sys
DATABASE = 'mma.db'

SCRIPT_NAME= sys.argv[1]

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

with open(SCRIPT_NAME) as f:
    # Creazione della tabella dei post
    c.executescript(f.read())


conn.commit()
conn.close()

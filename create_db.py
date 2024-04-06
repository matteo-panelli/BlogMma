import sqlite3 as sq

#create a database form db.sql

#connect to the database
conn = sq.connect('blog.sqlite3')

with open('db.sql') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
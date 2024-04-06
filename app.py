from flask import Flask, render_template
import sqlite3 as sq


app = Flask(__name__)

def get_db():
    conn = sq.connect('blog.sqlite3')
    conn.row_factory = sq.Row
    return conn


@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Post')
    rows = cur.fetchall()
    conn.close
    

    return render_template('index.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
    



from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tua_chiave_segreta'  # Sostituisci con una chiave segreta reale
DATABASE = 'mma.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    conn = get_db()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    comments = conn.execute('SELECT * FROM comments WHERE post_id = ?', (post_id,)).fetchall()
    return render_template('post.html', post=post, comments=comments)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if not session.get('logged_in'):
        flash('Devi essere loggato per creare un post.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        conn = get_db()
        conn.execute('INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)',
                     (title, content, session['user_id']))
        conn.commit()
        
        return redirect(url_for('index'))
    return render_template('add_post.html')

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if not session.get('logged_in'):
        flash('Devi essere loggato per aggiungere un commento.')
        return redirect(url_for('login'))

    comment = request.form['comment']
    
    conn = get_db()
    conn.execute('INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)',
                 (post_id, comment, session['user_id']))
    conn.commit()
    
    return redirect(url_for('post', post_id=post_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, hashed_password) VALUES (?, ?)',
                         (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Username già in uso.')
            return render_template('register.html')
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/edit_post/<int:post_id>', methods=['GET'])
def edit_post_form(post_id):
    if 'user_id' in session:
        conn = get_db()
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if post and post['user_id'] == session['user_id']:
            return render_template('edit_post.html', post=post)
        else:
            flash('You do not have permission to edit this post.')
    else:
        flash('Please log in to edit posts.')
    return redirect(url_for('index'))

@app.route('/edit_post/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    if 'user_id' in session and request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = get_db()
        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))
        conn.commit()
        flash('Post updated successfully.')
        return redirect(url_for('post', post_id=post_id))
    else:
        flash('Invalid request or not logged in.')
        return redirect(url_for('index'))


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' in session:
        conn = get_db()
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        if post and post['user_id'] == session['user_id']:
            conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
            conn.commit()
            flash('Post deleted successfully.')
        else:
            flash('You do not have permission to delete this post.')
    else:
        flash('Please log in to delete posts.')
    return redirect(url_for('index'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['hashed_password'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('index'))
        flash('Username o password non validi.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Assicurati che le altre funzioni dell'app siano al di sotto di questa linea...

if __name__ == '__main__':
    app.run(debug=True)

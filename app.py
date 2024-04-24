from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tua_chiave_segreta'  # Sostituisci con una chiave segreta reale
DATABASE = 'mma.db'
app.config['UPLOAD_FOLDER'] = './static/uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

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
    # Join the posts table with the users table to get the username along with the post details
    posts = conn.execute('''
    SELECT *
    FROM posts
    JOIN users ON posts.user_id = users.id
    ORDER BY posts.id DESC
    ''').fetchall()
    return render_template('index.html', posts=posts)



@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    comments = conn.execute('SELECT * FROM comments WHERE post_id = ?', (post_id,)).fetchall()
    return render_template('post.html', post=post, comments=comments)



@app.route('/classifica')
def news():
    
    return render_template('classifica.html')



@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if not session.get('logged_in'):
        flash('Devi essere loggato per creare un post.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('profile_image')  # Use .get() to avoid KeyError if 'profile_image' is not in the form
        image_path_db = None

        if image and allowed_file(image.filename):
            # Fix the path concatenation issue
            image_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            image_filename = title + '_' + image.filename
            image_path = os.path.join(image_folder, image_filename)
            image.save(image_path)
            # Assuming you want to save the image as a PNG file
            image_path_db = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)  # Relative path for the database

        try:
            conn = get_db()
            conn.execute('INSERT INTO posts (title, content, user_id, image_path) VALUES (?, ?, ?, ?)',
                         (title, content, session['user_id'], image_path_db))
            conn.commit()
        except Exception as e:
            # Handle any exceptions, rollback changes if necessary
            conn.rollback()
            flash('Errore durante l\'inserimento del post.')
            print("Error occurred:", e)
        finally:
            # Close the database connection
            conn.close()

        flash_message = 'Post aggiunto con successo.'
        if image_path_db:
            flash_message = 'Post con immagine aggiunto con successo.'
        flash(flash_message)
        return redirect(url_for('index'))
    return render_template('add_post.html')



@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if not session.get('logged_in'):
        flash('Devi essere loggato per aggiungere un commento.')
        return redirect(url_for('login'))

    comment_content = request.form['comment']
    user_id = session['user_id']  # Assumendo che l'ID dell'utente sia salvato in sessione quando si effettua il login

    try:
        conn = get_db()
        conn.execute('INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)',
                     (post_id, comment_content, user_id))
        conn.commit()
        flash('Commento aggiunto con successo.')
    except Exception as e:
        conn.rollback()
        flash('Errore durante l\'inserimento del commento.')
        print("Error occurred:", e)
    finally:
        conn.close()

    return redirect(url_for('post', post_id=post_id))



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
        user = conn.execute('SELECT ruolo FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
            if post:
                # Check if user is admin or the owner of the post
                if user['ruolo'] == 'admin' or post['user_id'] == session['user_id']:
                    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
                    conn.commit()
                    flash('Post deleted successfully.')
                else:
                    flash('You do not have permission to delete this post.')
            else:
                flash('Post not found.')
        else:
            flash('User not found.')
    else:
        flash('Please log in to delete posts.')
    return redirect(url_for('index'))



@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['POST'])
def delete_comment(post_id, comment_id):
    if 'user_id' in session:
        conn = get_db()
        user_role = conn.execute('SELECT ruolo FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        comment = conn.execute('SELECT * FROM comments WHERE id = ? AND post_id = ?', (comment_id, post_id)).fetchone()
        if comment:
            # Check if user is admin or the owner of the comment
            if user_role['ruolo'] == 'admin' or comment['user_id'] == session['user_id']:
                conn.execute('DELETE FROM comments WHERE id = ? AND post_id = ?', (comment_id, post_id))
                conn.commit()
                flash('Commento eliminato con successo.')
            else:
                flash('Non hai i permessi per eliminare questo commento.')
        else:
            flash('Commento non trovato.')
        conn.close()
    else:
        flash('Effettua il login per eliminare i commenti.')
    return redirect(url_for('post', post_id=post_id))



@app.route('/edit_comment/<int:post_id>/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(post_id, comment_id):
    if 'user_id' not in session:
        flash('Effettua il login per modificare i commenti.')
        return redirect(url_for('login'))

    conn = get_db()
    comment = conn.execute('SELECT * FROM comments WHERE id = ? AND post_id = ?', (comment_id, post_id)).fetchone()

    if comment is None:
        flash('Commento non trovato.')
        return redirect(url_for('post', post_id=post_id))

    user_role = conn.execute('SELECT ruolo FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    is_authorized = comment['user_id'] == session['user_id'] or user_role['ruolo'] == 'admin'

    if request.method == 'GET':
        if is_authorized:
            return render_template('edit_comment.html', comment=comment, post_id=post_id)
        else:
            flash('Non hai i permessi per modificare questo commento.')
            return redirect(url_for('post', post_id=post_id))

    elif request.method == 'POST':
        if is_authorized:
            content = request.form['content']
            conn.execute('UPDATE comments SET content = ? WHERE id = ? AND post_id = ?', (content, comment_id, post_id))
            conn.commit()
            flash('Commento aggiornato con successo.')
            return redirect(url_for('post', post_id=post_id))
        else:
            flash('Non hai i permessi per modificare questo commento.')
            return redirect(url_for('post', post_id=post_id))
    conn.close()






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
            
            # Verifica se l'utente è l'amministratore
            if username == 'admin' and password == 'admin':
                session['role'] = 'admin'
                
            return redirect(url_for('index'))
        
        flash('Username o password non validi.')

    return render_template('login.html')



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


if __name__ == '__main__':
    app.run(debug=True)

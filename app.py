from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tua_chiave_segreta'
DATABASE = 'mma.db'
app.config['UPLOAD_FOLDER'] = './static/uploads'

# Funzione per verificare se il tipo di file è consentito
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Ottiene un collegamento al database, creando una connessione se non esiste
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Chiude la connessione al database alla fine della richiesta/applicazione
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Pagina principale che mostra tutti i post
@app.route('/')
def index():
    conn = get_db()
    posts = conn.execute('''
    SELECT *
    FROM posts
    JOIN users ON posts.user_id = users.id
    ORDER BY posts.id DESC
    ''').fetchall()
    return render_template('index.html', posts=posts)

# Mostra un post specifico e i suoi commenti
@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    comments = conn.execute('SELECT * FROM comments WHERE post_id = ?', (post_id,)).fetchall()
    return render_template('post.html', post=post, comments=comments)

# Visualizza la pagina della classifica
@app.route('/classifica')
def news():
    return render_template('classifica.html')

# Permette l'aggiunta di un nuovo post
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if not session.get('logged_in'):
        flash('Devi essere loggato per creare un post.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('profile_image')  
        image_path_db = None

        if image and allowed_file(image.filename):
            image_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            image_filename = title + '_' + image.filename
            image_path = os.path.join(image_folder, image_filename)
            image.save(image_path)
            image_path_db = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)  

        try:
            conn = get_db()
            conn.execute('INSERT INTO posts (title, content, user_id, image_path) VALUES (?, ?, ?, ?)',
                         (title, content, session['user_id'], image_path_db))
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash('Errore durante l\'inserimento del post.')
            print("Error occurred:", e)
        finally:
            conn.close()

        flash_message = 'Post aggiunto con successo.'
        if image_path_db:
            flash_message += ' con immagine'
        flash(flash_message)
        return redirect(url_for('index'))
    return render_template('add_post.html')

# Permette di aggiungere un commento a un post
@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if not session.get('logged_in'):
        flash('Devi essere loggato per aggiungere un commento.')
        return redirect(url_for('login'))

    comment_content = request.form['comment']
    user_id = session['user_id']  

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

# Permette di modificare un post esistente
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        flash('Effettua l\'accesso per modificare il post.')
        return redirect(url_for('login'))

    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post or post['user_id'] != session['user_id']:
        flash('Non hai i permessi per modificare questo post o il post non esiste.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))
        conn.commit()
        flash('Post aggiornato con successo.')
        return redirect(url_for('index'))  # Redirect to index after successful update

    return render_template('edit_post.html', post=post)

# Permette di eliminare un post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT ruolo FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
            if post:
                if user['ruolo'] == 'admin' or post['user_id'] == session['user_id']:
                    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
                    conn.commit()
                    flash('Post eliminato con successo.')
                else:
                    flash('Non hai i permessi per eliminare questo post.')
            else:
                flash('Post non trovato.')
        else:
            flash('Utente non trovato.')
    else:
        flash('Effettua il login per eliminare i post.')
    return redirect(url_for('index'))

# Permette di eliminare un commento
@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['POST'])
def delete_comment(post_id, comment_id):
    if 'user_id' in session:
        conn = get_db()
        user_role = conn.execute('SELECT ruolo FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        comment = conn.execute('SELECT * FROM comments WHERE id = ? AND post_id = ?', (comment_id, post_id)).fetchone()
        if comment:
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

# Gestisce il login degli utenti
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

# Gestisce la registrazione degli utenti
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

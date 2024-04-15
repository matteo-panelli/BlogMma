-- Aggiungi una colonna user_id alla tabella posts
ALTER TABLE posts
ADD COLUMN user_id INTEGER;

-- Aggiungi una chiave esterna a posts che fa riferimento a users
ALTER TABLE posts
ADD CONSTRAINT fk_posts_users
FOREIGN KEY (user_id)
REFERENCES users (id);

-- Aggiungi una colonna user_id alla tabella comments
ALTER TABLE comments
ADD COLUMN user_id INTEGER;

-- Aggiungi una chiave esterna a comments che fa riferimento a users
ALTER TABLE comments
ADD CONSTRAINT fk_comments_users
FOREIGN KEY (user_id)
REFERENCES users (id);

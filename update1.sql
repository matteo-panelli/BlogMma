
ALTER TABLE posts
ADD COLUMN created DATETIME ;


UPDATE posts SET created=CURRENT_TIMESTAMP;




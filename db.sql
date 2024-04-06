CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testo TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES User(id)
);

INSERT INTO User (nome, cognome, username) VALUES ('Mario', 'Rossi', 'mrossi');
INSERT INTO User (nome, cognome, username) VALUES ('Luigi', 'Bianchi', 'lbianchi');


INSERT INTO Post (testo, user_id) VALUES ('Questo è il mio primo post!', 1);
INSERT INTO Post (testo, user_id) VALUES ('Oggi è una bella giornata.', 2);
INSERT INTO Post (testo, user_id) VALUES ('Ho appena finito di leggere un libro fantastico!', 1);


CREATE TABLE IF NOT EXISTS clients (
    client_id INT PRIMARY KEY,
    client_name VARCHAR(255),
    email VARCHAR(255)
);

INSERT INTO clients (client_id, client_name, email) VALUES
(1, 'Prothetic One',   'prothetic1@example.com'),
(2, 'Prothetic Two',   'prothetic2@example.com'),
(3, 'Prothetic Three', 'prothetic3@example.com'),
(4, 'Admin One',       'admin1@example.com'),
(5, 'User One',        'user1@example.com');

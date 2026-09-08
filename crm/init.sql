CREATE TABLE clients (
    client_id INT PRIMARY KEY,
    client_name VARCHAR(255),
    email VARCHAR(255)
);

INSERT INTO clients (client_id, client_name, email) VALUES
(1, 'Ivan Ivanov', 'ivan@example.com'),
(2, 'Maria Petrova', 'maria@example.com'),
(3, 'Dmitry Sidorov', 'dmitry@example.com'),
(4, 'Elena Smirnova', 'elena@example.com'),
(5, 'Andrey Volkov', 'andrey@example.com');

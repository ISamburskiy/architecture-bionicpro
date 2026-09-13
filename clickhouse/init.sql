-- 1. Создаем базу данных (если еще не создана)
CREATE DATABASE IF NOT EXISTS reports;
USE reports;

-- 2. Таблица пользователей (для проверки прав доступа)
-- Именно по полю email бэкенд будет искать client_id
CREATE TABLE IF NOT EXISTS users_auth
(
    client_id      UInt32,
    client_name    String,
    email          String,
    role           String
)
ENGINE = MergeTree()
ORDER BY email;

INSERT INTO users_auth (client_id, client_name, email, role) VALUES (1, 'Prothetic One', 'prothetic1@example.com', 'prothetic_user');
INSERT INTO users_auth (client_id, client_name, email, role) VALUES (2, 'Prothetic Two', 'prothetic2@example.com', 'prothetic_user');
INSERT INTO users_auth (client_id, client_name, email, role) VALUES (3, 'Prothetic Three', 'prothetic3@example.com', 'prothetic_user');
INSERT INTO users_auth (client_id, client_name, email, role) VALUES (4, 'Admin One', 'admin1@example.com', 'administrator');
INSERT INTO users_auth (client_id, client_name, email, role) VALUES (5, 'User One', 'user1@example.com', 'user');



-- 3. Таблица с данными отчетов (витрина)
CREATE TABLE IF NOT EXISTS client_telemetry_report
(
    client_id      UInt32,
    client_name    String,
    client_email   String,
    event_type     String,
    event_count    UInt32,
    total_value    Float64
)
ENGINE = MergeTree()
ORDER BY (client_id, event_type);


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
    password_hash  String, -- В реальном проекте тут должен быть хеш, здесь заглушка
    role           String
)
ENGINE = MergeTree()
ORDER BY email;

-- 3. Таблица с данными отчетов (витрина)
CREATE TABLE IF NOT EXISTS client_telemetry_report
(
    client_id      UInt32,
    client_name    String,
    client_email   String,
    event_type     String,
    event_count    UInt32,
    total_value    Float64,
    first_event_date DateTime,
    last_event_date  DateTime
)
ENGINE = MergeTree()
ORDER BY (client_id, event_type);

-- ============================================================
-- ДАННЫЕ (Синхронизация с realm-export.json)
-- ============================================================

-- --- Пользователи из Keycloak (для таблицы users_auth) ---

-- Пользователь user1 (роль user)
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (1001, 'User One', 'user1@example.com', 'hashed_password_placeholder', 'user');

-- Пользователь user2 (роль user)
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (1002, 'User Two', 'user2@example.com', 'hashed_password_placeholder', 'user');

-- Пользователь admin1 (роль administrator)
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (2001, 'Admin One', 'admin1@example.com', 'hashed_password_placeholder', 'administrator');

-- Пользователи prothetic (роль prothetic_user)
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (3001, 'Prothetic One', 'prothetic1@example.com', 'hashed_password_placeholder', 'prothetic_user');
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (3002, 'Prothetic Two', 'prothetic2@example.com', 'hashed_password_placeholder', 'prothetic_user');
INSERT INTO users_auth (client_id, client_name, email, password_hash, role)
VALUES (3003, 'Prothetic Three', 'prothetic3@example.com', 'hashed_password_placeholder', 'prothetic_user');


-- --- Тестовые данные отчетов (для таблицы client_telemetry_report) ---
-- Эти данные будут видны в UI после успешного логина

-- Данные для user1
INSERT INTO client_telemetry_report (client_id, client_name, client_email, event_type, event_count, total_value, first_event_date, last_event_date)
VALUES 
(1001, 'User One', 'user1@example.com', 'click', 150, 120.50, now() - INTERVAL 5 DAY, now()),
(1001, 'User One', 'user1@example.com', 'purchase', 12, 5400.00, now() - INTERVAL 3 DAY, now() - INTERVAL 1 DAY);

-- Данные для user2
INSERT INTO client_telemetry_report (client_id, client_name, client_email, event_type, event_count, total_value, first_event_date, last_event_date)
VALUES 
(1002, 'User Two', 'user2@example.com', 'click', 80, 65.20, now() - INTERVAL 4 DAY, now()),
(1002, 'User Two', 'user2@example.com', 'view', 300, 0.00, now() - INTERVAL 2 DAY, now());

-- Данные для admin1 (админ видит свои данные, но логика бэкенда отдаст только то, что привязано к его email)
INSERT INTO client_telemetry_report (client_id, client_name, client_email, event_type, event_count, total_value, first_event_date, last_event_date)
VALUES 
(2001, 'Admin One', 'admin1@example.com', 'system_log', 5, 0.00, now() - INTERVAL 1 DAY, now());

-- Данные для prothetic пользователей
INSERT INTO client_telemetry_report (client_id, client_name, client_email, event_type, event_count, total_value, first_event_date, last_event_date)
VALUES 
(3001, 'Prothetic One', 'prothetic1@example.com', 'impression', 1000, 200.00, now() - INTERVAL 7 DAY, now()),
(3002, 'Prothetic Two', 'prothetic2@example.com', 'impression', 1200, 240.00, now() - INTERVAL 7 DAY, now()),
(3003, 'Prothetic Three', 'prothetic3@example.com', 'impression', 950, 190.00, now() - INTERVAL 7 DAY, now());

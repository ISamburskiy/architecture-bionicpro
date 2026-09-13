CREATE TABLE telemetry (
    event_id SERIAL PRIMARY KEY,
    client_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    value NUMERIC(10,2) DEFAULT 0,
    event_time TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Генерируем немного данных
INSERT INTO telemetry (client_id, event_type, value, event_time)
SELECT
    (random() * 4 + 1)::int AS client_id,
    (array['login','purchase','view_page','click_ad'])[floor(random()*4+1)::int] AS event_type,
    CASE
        WHEN (array['login','view_page','click_ad'])[floor(random()*3+1)::int] = 'purchase' THEN (random()*5000+100)::numeric(10,2)
        ELSE 0
    END AS value,
    NOW() - (random() * INTERVAL '7 days') AS event_time
FROM generate_series(1, 18);

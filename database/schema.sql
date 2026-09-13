-- Esquema Base de Datos SQLite - Bio-E-Nose SCADA System
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    mq2 INTEGER NOT NULL,
    mq4 INTEGER NOT NULL,
    mq135 INTEGER NOT NULL,
    mq3 INTEGER NOT NULL,
    mq7 INTEGER NOT NULL,
    mq9 INTEGER NOT NULL,
    temp_cam REAL NOT NULL,
    humedad_cam REAL NOT NULL,
    temp_reactor REAL NOT NULL,
    calidad_predicha TEXT,
    confianza REAL
);

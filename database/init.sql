-- =============================================================================
-- LABORATORIO DEVOPS - ESQUEMA INICIAL DE BASE DE DATOS (POSTGRESQL)
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_info (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    mq2 NUMERIC(10, 2) NOT NULL,
    mq4 NUMERIC(10, 2) NOT NULL,
    mq135 NUMERIC(10, 2) NOT NULL,
    mq3 NUMERIC(10, 2) NOT NULL,
    mq7 NUMERIC(10, 2) NOT NULL,
    mq9 NUMERIC(10, 2) NOT NULL,
    temp_cam NUMERIC(6, 2) NOT NULL,
    humedad_cam NUMERIC(6, 2) NOT NULL,
    temp_reactor NUMERIC(6, 2) NOT NULL,
    calidad_predicha VARCHAR(50),
    confianza NUMERIC(5, 4)
);

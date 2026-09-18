-- =============================================================================
-- LABORATORIO DEVOPS - DATOS SEMILLA DE PRUEBA Y AUTENTICACIÓN
-- =============================================================================

INSERT INTO system_info (key, value)
VALUES ('app_name', 'Bio-E-Nose Biofuel Quality Control')
ON CONFLICT (key) DO NOTHING;

-- Usuario administrador por defecto para inicio de sesión SCADA (Contraseña: admin123)
INSERT INTO users (username, name, email, password_hash, is_active, is_superuser)
VALUES ('admin', 'Administrador SCADA', 'admin@bioenose.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW', TRUE, TRUE)
ON CONFLICT (username) DO NOTHING;

INSERT INTO sensor_readings (mq2, mq4, mq135, mq3, mq7, mq9, temp_cam, humedad_cam, temp_reactor, calidad_predicha, confianza)
VALUES (23231.72, 17268.26, 12320.02, 8474.87, 7553.57, 15570.25, 22.51, 59.04, 425.00, 'ALTA', 0.9850);

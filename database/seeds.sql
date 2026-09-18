-- =============================================================================
-- LABORATORIO DEVOPS - DATOS SEMILLA DE PRUEBA
-- =============================================================================

INSERT INTO system_info (key, value)
VALUES ('app_name', 'Bio-E-Nose Biofuel Quality Control')
ON CONFLICT (key) DO NOTHING;

INSERT INTO sensor_readings (mq2, mq4, mq135, mq3, mq7, mq9, temp_cam, humedad_cam, temp_reactor, calidad_predicha, confianza)
VALUES (23231.72, 17268.26, 12320.02, 8474.87, 7553.57, 15570.25, 22.51, 59.04, 425.00, 'ALTA', 0.9850);

-- =============================================================================
-- PROYECTO   : Cloud Data Analytics Suite (CDAS)
-- ARCHIVO    : sql/views/01_vw_productividad.sql
-- DESCRIPCIÓN: Vista analítica para medir la capacidad operativa global
-- =============================================================================

CREATE OR REPLACE VIEW raw.vw_crm_productividad AS
SELECT 
    -- Dimensiones temporales
    DATE_TRUNC('month', date_create)::DATE AS mes,
    
    -- KPIs Operativos y Volúmenes
    COUNT(id) AS total_expedientes,
    COUNT(CASE WHEN is_closed = TRUE THEN 1 END) AS total_informes_emitidos,
    
    -- Tiempos y SLAs
    ROUND(AVG(resolution_days)::NUMERIC, 2) AS tiempo_medio_resolucion_dias,
    ROUND(AVG(days_to_visit)::NUMERIC, 2) AS tiempo_medio_encargo_visita_dias,
    
    -- Porcentaje de SLA (% en plazo)
    ROUND(
        (COUNT(CASE WHEN on_time = TRUE THEN 1 END)::NUMERIC / NULLIF(COUNT(CASE WHEN is_closed = TRUE THEN 1 END), 0)) * 100, 
        2
    ) AS pct_en_plazo,
    
    -- Logística y Presupuestos
    COALESCE(SUM(km), 0) AS km_totales_mes,
    ROUND(
        (COUNT(CASE WHEN budget_accepted = TRUE THEN 1 END)::NUMERIC / NULLIF(COUNT(id), 0)) * 100, 
        2
    ) AS ratio_aceptacion_presupuestos
    
FROM raw.crm_productividad_deals
GROUP BY DATE_TRUNC('month', date_create)::DATE
ORDER BY mes DESC;
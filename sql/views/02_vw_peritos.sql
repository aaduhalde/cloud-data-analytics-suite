-- =============================================================================
-- PROYECTO   : Cloud Data Analytics Suite (CDAS)
-- ARCHIVO    : sql/views/02_vw_peritos.sql
-- DESCRIPCIÓN: Vista analítica para evaluar el desempeño y rentabilidad por perito
-- =============================================================================

CREATE OR REPLACE VIEW raw.vw_crm_peritos AS
SELECT 
    assigned_by_id AS perito_id,
    DATE_TRUNC('month', date_create)::DATE AS mes,
    
    -- Volúmenes de carga de trabajo
    COUNT(id) AS total_expedientes_asignados,
    COUNT(CASE WHEN is_closed = TRUE THEN 1 END) AS informes_emitidos,
    
    -- Métricas de rendimiento individual
    ROUND(AVG(resolution_days)::NUMERIC, 2) AS tiempo_medio_resolucion_dias,
    ROUND(
        (COUNT(CASE WHEN on_time = TRUE THEN 1 END)::NUMERIC / NULLIF(COUNT(CASE WHEN is_closed = TRUE THEN 1 END), 0)) * 100, 
        2
    ) AS pct_en_plazo,
    
    -- Calidad Técnica y Desplazamientos
    COALESCE(SUM(reopen_count), 0) AS total_reaperturas_correcciones,
    COALESCE(SUM(km), 0) AS km_totales,
    ROUND(AVG(km)::NUMERIC, 2) AS km_promedio_por_informe,
    
    -- Rentabilidad y Métricas Financieras
    COALESCE(SUM(revenue), 0) AS facturacion_total,
    COALESCE(SUM(cost), 0) AS coste_total,
    COALESCE(SUM(profit), 0) AS beneficio_neto_total,
    ROUND(AVG(profit)::NUMERIC, 2) AS rentabilidad_promedio_por_informe

FROM raw.crm_peritos_deals
GROUP BY assigned_by_id, DATE_TRUNC('month', date_create)::DATE
ORDER BY mes DESC, perito_id;
-- =============================================================================
-- PROYECTO   : Cloud Data Analytics Suite (CDAS)
-- ARCHIVO    : sql/views/03_vw_marketing.sql
-- DESCRIPCIÓN: Vista analítica consolidada para embudo comercial y captación
-- =============================================================================

CREATE OR REPLACE VIEW raw.vw_crm_marketing_ventas AS
WITH leads_agg AS (
    SELECT 
        DATE_TRUNC('month', date_create)::DATE AS mes,
        COALESCE(lead_channel, 'Sin Canal / Directo') AS canal_captacion,
        COUNT(id) AS total_leads,
        COUNT(CASE WHEN is_converted = TRUE THEN 1 END) AS leads_convertidos,
        COALESCE(SUM(ad_cost), 0) AS inversion_publicitaria
    FROM raw.crm_marketing_leads
    GROUP BY DATE_TRUNC('month', date_create)::DATE, COALESCE(lead_channel, 'Sin Canal / Directo')
),
deals_agg AS (
    SELECT 
        DATE_TRUNC('month', closedate)::DATE AS mes,
        COUNT(DISTINCT customer_id) AS total_clientes,
        COUNT(CASE WHEN is_new_customer = TRUE THEN 1 END) AS nuevos_clientes,
        COUNT(CASE WHEN is_recurrent = TRUE THEN 1 END) AS clientes_recurrentes,
        COALESCE(SUM(revenue), 0) AS facturacion_total
    FROM raw.crm_marketing_deals
    WHERE is_won = TRUE
    GROUP BY DATE_TRUNC('month', closedate)::DATE
)
SELECT 
    l.mes,
    l.canal_captacion,
    l.total_leads,
    l.leads_convertidos,
    
    -- Tasa de Conversión (%)
    ROUND(
        (l.leads_convertidos::NUMERIC / NULLIF(l.total_leads, 0)) * 100, 
        2
    ) AS tasa_conexion_pct,
    
    -- Inversión y Coste de Adquisición (CAC Estimado)
    l.inversion_publicitaria,
    ROUND(
        l.inversion_publicitaria / NULLIF(d.nuevos_clientes, 0), 
        2
    ) AS cac_estimado,
    
    -- Retención y Facturación
    COALESCE(d.nuevos_clientes, 0) AS nuevos_clientes_ganados,
    COALESCE(d.facturacion_total, 0) AS facturacion_total_mes,
    ROUND(
        d.facturacion_total / NULLIF(d.nuevos_clientes, 0), 
        2
    ) AS facturacion_media_nuevo_cliente,
    
    ROUND(
        (d.clientes_recurrentes::NUMERIC / NULLIF(d.total_clientes, 0)) * 100, 
        2
    ) AS pct_clientes_recurrentes

FROM leads_agg l
LEFT JOIN deals_agg d ON l.mes = d.mes
ORDER BY l.mes DESC, l.canal_captacion;
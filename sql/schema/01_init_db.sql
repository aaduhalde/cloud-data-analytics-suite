-- =============================================================================
-- PROYECTO   : Cloud Data Analytics Suite (CDAS)
-- ARCHIVO    : sql/schema/01_init_db.sql
-- DESCRIPCIÓN: Creación de esquema y tablas base para Bitrix24
-- AUTOR      : Alejandro Adrián Duhalde
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ESQUEMA
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS raw;

-- Setear el search_path por defecto
SET search_path TO raw, public;

-- -----------------------------------------------------------------------------
-- 2. TABLA: PRODUCTIVIDAD DEALS (crm_productividad_deals_1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.crm_productividad_deals (
    id                      BIGINT PRIMARY KEY,
    title                   VARCHAR(255),
    date_create             TIMESTAMP WITH TIME ZONE,
    closedate               TIMESTAMP WITH TIME ZONE,
    stage_id                VARCHAR(50),
    assigned_by_id          BIGINT,
    opportunity             NUMERIC(15, 2) DEFAULT 0.00,
    uf_crm_1715249307354    NUMERIC(10, 2), -- Km recorridos
    uf_crm_1715249711       TIMESTAMP WITH TIME ZONE, -- Fecha de visita
    uf_crm_deadline         TIMESTAMP WITH TIME ZONE, -- Fecha objetivo / SLA
    is_closed               BOOLEAN,
    resolution_days         INTEGER,
    days_to_visit           INTEGER,
    km                      NUMERIC(10, 2),
    on_time                 BOOLEAN,
    budget_accepted         BOOLEAN,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_prod_deals_date_create ON raw.crm_productividad_deals(date_create);
CREATE INDEX IF NOT EXISTS idx_prod_deals_assigned ON raw.crm_productividad_deals(assigned_by_id);

-- -----------------------------------------------------------------------------
-- 3. TABLA: PERITOS DEALS (crm_peritos_deals_2)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.crm_peritos_deals (
    id                      BIGINT PRIMARY KEY,
    title                   VARCHAR(255),
    date_create             TIMESTAMP WITH TIME ZONE,
    closedate               TIMESTAMP WITH TIME ZONE,
    stage_id                VARCHAR(50),
    assigned_by_id          BIGINT, -- Id del perito
    opportunity             NUMERIC(15, 2) DEFAULT 0.00, -- Ingreso
    uf_crm_1715249307354    NUMERIC(10, 2), -- Km
    uf_crm_1715249711       TIMESTAMP WITH TIME ZONE, -- Fecha visita
    uf_crm_deadline         TIMESTAMP WITH TIME ZONE, -- Fecha objetivo (SLA)
    uf_crm_reopen_count     INTEGER DEFAULT 0, -- Reaperturas / correcciones
    uf_crm_cost             NUMERIC(15, 2) DEFAULT 0.00, -- Coste por informe
    is_closed               BOOLEAN,
    resolution_days         INTEGER,
    on_time                 BOOLEAN,
    km                      NUMERIC(10, 2),
    reopen_count            INTEGER DEFAULT 0,
    cost                    NUMERIC(15, 2),
    revenue                 NUMERIC(15, 2),
    profit                  NUMERIC(15, 2),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_peritos_deals_assigned ON raw.crm_peritos_deals(assigned_by_id);
CREATE INDEX IF NOT EXISTS idx_peritos_deals_closedate ON raw.crm_peritos_deals(closedate);

-- -----------------------------------------------------------------------------
-- 4. TABLA: MARKETING LEADS (crm_marketing_leads_3)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.crm_marketing_leads (
    id                      BIGINT PRIMARY KEY,
    date_create             TIMESTAMP WITH TIME ZONE,
    status_id               VARCHAR(50),
    source_id               VARCHAR(50),
    utm_source              VARCHAR(100),
    utm_medium              VARCHAR(100),
    contact_id              BIGINT,
    company_id              BIGINT,
    opportunity             NUMERIC(15, 2) DEFAULT 0.00,
    is_converted            BOOLEAN,
    lead_channel            VARCHAR(100),
    ad_cost                 NUMERIC(15, 2),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_leads_date_create ON raw.crm_marketing_leads(date_create);
CREATE INDEX IF NOT EXISTS idx_leads_channel ON raw.crm_marketing_leads(lead_channel);

-- -----------------------------------------------------------------------------
-- 5. TABLA: MARKETING DEALS (crm_marketing_deals_3)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.crm_marketing_deals (
    id                      BIGINT PRIMARY KEY,
    date_create             TIMESTAMP WITH TIME ZONE,
    closedate               TIMESTAMP WITH TIME ZONE,
    stage_id                VARCHAR(50),
    opportunity             NUMERIC(15, 2) DEFAULT 0.00,
    contact_id              BIGINT,
    company_id              BIGINT,
    is_won                  BOOLEAN,
    revenue                 NUMERIC(15, 2),
    customer_id             BIGINT,
    is_new_customer         BOOLEAN,
    deal_count              INTEGER,
    is_recurrent            BOOLEAN,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_mkt_deals_customer ON raw.crm_marketing_deals(customer_id);
CREATE INDEX IF NOT EXISTS idx_mkt_deals_closedate ON raw.crm_marketing_deals(closedate);
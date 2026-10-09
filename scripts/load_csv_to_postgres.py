import sys
import csv
from pathlib import Path

# =============================================================================
# RESOLUCIÓN ABSOLUTA DE RUTAS (ANCLAJE DIRECTO AL REPOSITORIO)
# =============================================================================
# SCRIPT_DIR = .../cloud-data-analytics-suite/scripts
SCRIPT_DIR = Path(__file__).resolve().parent

# REPO_ROOT = .../cloud-data-analytics-suite
REPO_ROOT = SCRIPT_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from auth.driver_postgres import get_db_connection

# Ruta garantizada al directorio de datos procesados
DATA_DIR = REPO_ROOT / "data" / "processed"

CSV_MAPPING = {
    "crm_productividad_deals_1.csv": "raw.crm_productividad_deals",
    "crm_peritos_deals_2.csv": "raw.crm_peritos_deals",
    "crm_marketing_leads_3.csv": "raw.crm_marketing_leads",
    "crm_marketing_deals_3.csv": "raw.crm_marketing_deals"
}

# =============================================================================
# PARSER Y LIMPIEZA DE DATOS
# =============================================================================

def parse_val(val, target_type):
    """Convierte cadenas del CSV a tipos compatibles con PostgreSQL."""
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("none", "null", "nan"):
        return None

    if target_type == "int":
        try:
            return int(float(val_str))
        except ValueError:
            return None
    elif target_type == "float":
        try:
            return float(val_str)
        except ValueError:
            return None
    elif target_type == "bool":
        return val_str.lower() in ("true", "1", "t", "yes")
    return val_str

# =============================================================================
# SENTENCIAS UPSERT (ON CONFLICT DO UPDATE)
# =============================================================================

UPSERT_QUERIES = {
    "raw.crm_productividad_deals": """
        INSERT INTO raw.crm_productividad_deals (
            id, title, date_create, closedate, stage_id, assigned_by_id, 
            opportunity, uf_crm_1715249307354, uf_crm_1715249711, 
            is_closed, resolution_days, days_to_visit, km, on_time, budget_accepted
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            closedate = EXCLUDED.closedate,
            stage_id = EXCLUDED.stage_id,
            assigned_by_id = EXCLUDED.assigned_by_id,
            opportunity = EXCLUDED.opportunity,
            uf_crm_1715249307354 = EXCLUDED.uf_crm_1715249307354,
            uf_crm_1715249711 = EXCLUDED.uf_crm_1715249711,
            is_closed = EXCLUDED.is_closed,
            resolution_days = EXCLUDED.resolution_days,
            days_to_visit = EXCLUDED.days_to_visit,
            km = EXCLUDED.km,
            on_time = EXCLUDED.on_time,
            budget_accepted = EXCLUDED.budget_accepted;
    """,
    "raw.crm_peritos_deals": """
        INSERT INTO raw.crm_peritos_deals (
            id, title, date_create, closedate, stage_id, assigned_by_id, 
            opportunity, uf_crm_1715249307354, uf_crm_1715249711, 
            is_closed, resolution_days, on_time, km, reopen_count, profit
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            closedate = EXCLUDED.closedate,
            stage_id = EXCLUDED.stage_id,
            assigned_by_id = EXCLUDED.assigned_by_id,
            opportunity = EXCLUDED.opportunity,
            is_closed = EXCLUDED.is_closed,
            resolution_days = EXCLUDED.resolution_days,
            on_time = EXCLUDED.on_time,
            km = EXCLUDED.km,
            reopen_count = EXCLUDED.reopen_count,
            profit = EXCLUDED.profit;
    """,
    "raw.crm_marketing_leads": """
        INSERT INTO raw.crm_marketing_leads (
            id, date_create, status_id, source_id, utm_source, utm_medium, 
            contact_id, company_id, opportunity, is_converted, lead_channel, ad_cost
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            status_id = EXCLUDED.status_id,
            source_id = EXCLUDED.source_id,
            is_converted = EXCLUDED.is_converted,
            opportunity = EXCLUDED.opportunity,
            ad_cost = EXCLUDED.ad_cost;
    """,
    "raw.crm_marketing_deals": """
        INSERT INTO raw.crm_marketing_deals (
            id, date_create, closedate, stage_id, opportunity, contact_id, 
            company_id, is_won, revenue, customer_id, is_new_customer, 
            deal_count, is_recurrent
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            closedate = EXCLUDED.closedate,
            stage_id = EXCLUDED.stage_id,
            opportunity = EXCLUDED.opportunity,
            is_won = EXCLUDED.is_won,
            revenue = EXCLUDED.revenue,
            is_new_customer = EXCLUDED.is_new_customer,
            deal_count = EXCLUDED.deal_count,
            is_recurrent = EXCLUDED.is_recurrent;
    """
}

# =============================================================================
# PROCESAMIENTO CSV CON FORMATO DE LOGS SOLICITADO
# =============================================================================

def process_and_load_csv(file_name, table_name, cursor):
    csv_path = DATA_DIR / file_name
    print(f"🚀 Cargando {file_name} en {table_name}...")
    
    if not csv_path.exists():
        print(f"⚠️ El archivo {csv_path} no existe. Omitiendo.")
        print("✅ (0 filas procesadas)\n")
        return 0

    records = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        # Detectar delimitador (\t o ,)
        sample = f.read(2048)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            clean_row = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
            
            row_id = parse_val(clean_row.get("id"), "int")
            if row_id is None:
                continue

            if table_name == "raw.crm_productividad_deals":
                records.append((
                    row_id,
                    parse_val(clean_row.get("title"), "str"),
                    parse_val(clean_row.get("date_create"), "str"),
                    parse_val(clean_row.get("closedate"), "str"),
                    parse_val(clean_row.get("stage_id"), "str"),
                    parse_val(clean_row.get("assigned_by_id"), "int"),
                    parse_val(clean_row.get("opportunity"), "float"),
                    parse_val(clean_row.get("uf_crm_1715249307354"), "float"),
                    parse_val(clean_row.get("uf_crm_1715249711"), "str"),
                    parse_val(clean_row.get("is_closed"), "bool"),
                    parse_val(clean_row.get("resolution_days"), "int"),
                    parse_val(clean_row.get("days_to_visit"), "int"),
                    parse_val(clean_row.get("km"), "float"),
                    parse_val(clean_row.get("on_time"), "bool"),
                    parse_val(clean_row.get("budget_accepted"), "bool")
                ))
            elif table_name == "raw.crm_peritos_deals":
                records.append((
                    row_id,
                    parse_val(clean_row.get("title"), "str"),
                    parse_val(clean_row.get("date_create"), "str"),
                    parse_val(clean_row.get("closedate"), "str"),
                    parse_val(clean_row.get("stage_id"), "str"),
                    parse_val(clean_row.get("assigned_by_id"), "int"),
                    parse_val(clean_row.get("opportunity"), "float"),
                    parse_val(clean_row.get("uf_crm_1715249307354"), "float"),
                    parse_val(clean_row.get("uf_crm_1715249711"), "str"),
                    parse_val(clean_row.get("is_closed"), "bool"),
                    parse_val(clean_row.get("resolution_days"), "int"),
                    parse_val(clean_row.get("on_time"), "bool"),
                    parse_val(clean_row.get("km"), "float"),
                    parse_val(clean_row.get("reopen_count"), "int"),
                    parse_val(clean_row.get("profit"), "float")
                ))
            elif table_name == "raw.crm_marketing_leads":
                records.append((
                    row_id,
                    parse_val(clean_row.get("date_create"), "str"),
                    parse_val(clean_row.get("status_id"), "str"),
                    parse_val(clean_row.get("source_id"), "str"),
                    parse_val(clean_row.get("utm_source"), "str"),
                    parse_val(clean_row.get("utm_medium"), "str"),
                    parse_val(clean_row.get("contact_id"), "int"),
                    parse_val(clean_row.get("company_id"), "int"),
                    parse_val(clean_row.get("opportunity"), "float"),
                    parse_val(clean_row.get("is_converted"), "bool"),
                    parse_val(clean_row.get("lead_channel"), "str"),
                    parse_val(clean_row.get("ad_cost"), "float")
                ))
            elif table_name == "raw.crm_marketing_deals":
                records.append((
                    row_id,
                    parse_val(clean_row.get("date_create"), "str"),
                    parse_val(clean_row.get("closedate"), "str"),
                    parse_val(clean_row.get("stage_id"), "str"),
                    parse_val(clean_row.get("opportunity"), "float"),
                    parse_val(clean_row.get("contact_id"), "int"),
                    parse_val(clean_row.get("company_id"), "int"),
                    parse_val(clean_row.get("is_won"), "bool"),
                    parse_val(clean_row.get("revenue"), "float"),
                    parse_val(clean_row.get("customer_id"), "int"),
                    parse_val(clean_row.get("is_new_customer"), "bool"),
                    parse_val(clean_row.get("deal_count"), "int"),
                    parse_val(clean_row.get("is_recurrent"), "bool")
                ))

    if records:
        query = UPSERT_QUERIES[table_name]
        cursor.executemany(query, records)
        print(f"✅ ({len(records)} filas procesadas)\n")
    else:
        print("⚠️ No se encontraron registros válidos para procesar.")
        print("✅ (0 filas procesadas)\n")
        
    return len(records)

# =============================================================================
# PRUEBAS DE INTEGRIDAD
# =============================================================================

def validate_data(cursor):
    print("=" * 60)
    print("📋 PRUEBAS DE INTEGRIDAD Y VALIDACIÓN DE CARGA")
    print("=" * 60)

    for table_name in CSV_MAPPING.values():
        print(f"\n📌 Tabla: {table_name}")
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_rows = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT COUNT(id) 
            FROM (
                SELECT id FROM {table_name} GROUP BY id HAVING COUNT(id) > 1
            ) sub;
        """)
        duplicate_ids = cursor.fetchone()[0]

        cursor.execute(f"SELECT id, date_create FROM {table_name} ORDER BY id DESC LIMIT 2;")
        sample_records = cursor.fetchall()

        print(f"   • Total registros insertados : {total_rows}")
        print(f"   • Duplicados detectados      : {duplicate_ids} {'✅ [OK]' if duplicate_ids == 0 else '❌ [DUPLICADOS]'}")
        print(f"   • Muestra de IDs recientes   : {sample_records}")

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for file_name, table_name in CSV_MAPPING.items():
                process_and_load_csv(file_name, table_name, cursor)

            conn.commit()
            print("💾 Transacción confirmada exitosamente en PostgreSQL.\n")
            validate_data(cursor)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error en la carga: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
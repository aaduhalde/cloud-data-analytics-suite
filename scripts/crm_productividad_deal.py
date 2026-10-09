import sys
from pathlib import Path
import requests
import pandas as pd

# =============================================================================
# RESOLUCIÓN ABSOLUTA DE RUTAS DE REPOSITORIO
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from auth.bitrix_config import BITRIX_WEBHOOK_URL

# =============================================================================
# PATHS PORTABLES Y SALIDA
# =============================================================================
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "crm_productividad_deals_1.csv"
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CAMPOS CUSTOM BITRIX
# =============================================================================
FIELD_KM = "UF_CRM_1715249307354"         # Km recorridos
FIELD_VISIT_DATE = "UF_CRM_1715249711"   # Fecha de visita
FIELD_DEADLINE = "UF_CRM_DEADLINE"       # Fecha objetivo / SLA

# =============================================================================
# HELPER INCREMENTAL
# =============================================================================

def get_last_id(csv_path):
    """Obtiene el último ID registrado en el CSV soportando comas y tabulaciones."""
    if not csv_path.exists():
        return None
    try:
        # Detectar el delimitador leyendo las primeras líneas
        with open(csv_path, "r", encoding="utf-8") as f:
            sample = f.read(2048)
            delimiter = "\t" if "\t" in sample else ","

        df_ids = pd.read_csv(csv_path, sep=delimiter, usecols=lambda col: col.strip().upper() == "ID")
        if not df_ids.empty:
            id_col = df_ids.columns[0]
            return int(pd.to_numeric(df_ids[id_col], errors="coerce").max())
    except Exception as e:
        print(f"⚠️ No se pudo leer el CSV existente ({e}). Se realizará una extracción completa.")
    return None

# =============================================================================
# FUNCIÓN GENÉRICA DE PAGINACIÓN BITRIX24
# =============================================================================

def fetch_all(method, params=None):
    all_items = []
    start = 0

    while True:
        payload = params.copy() if params else {}
        payload["start"] = start

        response = requests.post(
            BITRIX_WEBHOOK_URL + method,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("result", [])
        all_items.extend(items)

        if data.get("next") is not None:
            start = data["next"]
        else:
            break

    return all_items

# =============================================================================
# EXTRACCIÓN DE DEALS
# =============================================================================

def extract_deals(last_id=None):
    fields = [
        "ID",
        "TITLE",
        "DATE_CREATE",
        "CLOSEDATE",
        "STAGE_ID",
        "ASSIGNED_BY_ID",
        "OPPORTUNITY",
        FIELD_KM,
        FIELD_VISIT_DATE,
        FIELD_DEADLINE
    ]

    params = {"select": fields}

    if last_id is not None:
        params["filter"] = {">ID": last_id}

    deals = fetch_all(
        method="crm.deal.list",
        params=params
    )

    return pd.DataFrame(deals)

# =============================================================================
# TRANSFORMACIONES PRODUCTIVIDAD
# =============================================================================

def transform_deals(df):
    if df.empty:
        return df

    # -----------------------------
    # Normalización de fechas a UTC y tz-naive (resuelve el error de zonas horarias)
    # -----------------------------
    date_cols = ["DATE_CREATE", "CLOSEDATE", FIELD_VISIT_DATE, FIELD_DEADLINE]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_localize(None)

    # -----------------------------
    # Informe emitido
    # -----------------------------
    df["is_closed"] = df["CLOSEDATE"].notna()

    # -----------------------------
    # Tiempo medio de resolución (días)
    # -----------------------------
    df["resolution_days"] = (
        df["CLOSEDATE"] - df["DATE_CREATE"]
    ).dt.days

    # -----------------------------
    # Tiempo encargo -> visita
    # -----------------------------
    if FIELD_VISIT_DATE in df.columns:
        df["days_to_visit"] = (
            df[FIELD_VISIT_DATE] - df["DATE_CREATE"]
        ).dt.days
    else:
        df["days_to_visit"] = None

    # -----------------------------
    # Km recorridos
    # -----------------------------
    if FIELD_KM in df.columns:
        df["km"] = pd.to_numeric(
            df[FIELD_KM], errors="coerce"
        )
    else:
        df["km"] = None

    # -----------------------------
    # % en plazo (si existe deadline)
    # -----------------------------
    if FIELD_DEADLINE in df.columns:
        df["on_time"] = df["CLOSEDATE"] <= df[FIELD_DEADLINE]
    else:
        df["on_time"] = None

    # -----------------------------
    # Ratio aceptación de presupuestos
    # -----------------------------
    df["budget_accepted"] = (
        pd.to_numeric(df["OPPORTUNITY"], errors="coerce").fillna(0) > 0
    )

    return df

# =============================================================================
# MAIN
# =============================================================================

def main():
    last_id = get_last_id(OUTPUT_CSV)
    if last_id is not None:
        print(f"🔄 Modo incremental activo. Buscando deals con ID > {last_id}")
    else:
        print("📥 Realizando extracción completa...")

    df_new = extract_deals(last_id=last_id)
    print(f"📊 Nuevos registros extraídos desde Bitrix24: {len(df_new)}")

    if df_new.empty:
        print("✅ El CSV está al día. No hay registros nuevos.")
        return

    print("⚙️ Transformando nuevos datos...")
    df_new = transform_deals(df_new)

    print("💾 Actualizando archivo CSV procesado...")
    file_exists = OUTPUT_CSV.exists()

    # Detectar el delimitador del archivo existente
    delimiter = "\t"
    if file_exists:
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            sample = f.read(2048)
            delimiter = "\t" if "\t" in sample else ","

    df_new.to_csv(
        OUTPUT_CSV,
        mode="a" if file_exists else "w",
        sep=delimiter,
        header=not file_exists,
        index=False,
        encoding="utf-8"
    )

    print(f"🎉 CSV actualizado correctamente en: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
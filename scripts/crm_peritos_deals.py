from pathlib import Path
import requests
import pandas as pd
import sys

# =====================================
# CONFIGURACIÓN
# =====================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from auth.bitrix_config import BITRIX_WEBHOOK_URL

# =====================================
# PATHS PORTABLES
# =====================================

OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "crm_peritos_deals_2.csv"
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# =====================================
# HELPER INCREMENTAL
# =====================================

def get_last_id(csv_path):
    """Obtiene el último ID registrado en el CSV de manera eficiente."""
    if not csv_path.exists():
        return None
    try:
        # Lee únicamente la columna ID para optimizar memoria
        df_ids = pd.read_csv(csv_path, usecols=["ID"])
        if not df_ids.empty:
            return int(df_ids["ID"].max())
    except Exception as e:
        print(f"No se pudo leer el CSV existente ({e}). Se realizara una carga completa.")
    return None

# =====================================
# FUNCIÓN GENÉRICA DE PAGINACIÓN
# =====================================

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

# =====================================
# EXTRACCIÓN DE DEALS
# =====================================

def extract_deals(last_id=None):
    fields = [
        "ID",
        "TITLE",
        "DATE_CREATE",
        "CLOSEDATE",
        "STAGE_ID",
        "ASSIGNED_BY_ID",          # Perito
        "OPPORTUNITY",             # Ingreso
        "UF_CRM_1715249307354",    # KM
        "UF_CRM_1715249711",       # Fecha visita
        "UF_CRM_DEADLINE",         # Fecha objetivo (SLA) - si existe
        "UF_CRM_REOPEN_COUNT",     # Reaperturas / correcciones - si existe
        "UF_CRM_COST"              # Coste por informe - si existe
    ]

    params = {"select": fields}

    # Aplicar filtro incremental si existe un ID previo
    if last_id is not None:
        params["filter"] = {">ID": last_id}

    deals = fetch_all(
        method="crm.deal.list",
        params=params
    )

    return pd.DataFrame(deals)

# =====================================
# TRANSFORMACIONES
# =====================================

def transform_deals(df):
    if df.empty:
        return df

    # Fechas
    date_cols = [
        "DATE_CREATE",
        "CLOSEDATE",
        "UF_CRM_1715249711",
        "UF_CRM_DEADLINE"
    ]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Informe emitido
    df["is_closed"] = df["CLOSEDATE"].notna()

    # Tiempo medio por expediente (días)
    df["resolution_days"] = (
        df["CLOSEDATE"] - df["DATE_CREATE"]
    ).dt.days

    # Dentro de plazo (si existe deadline)
    if "UF_CRM_DEADLINE" in df.columns:
        df["on_time"] = df["CLOSEDATE"] <= df["UF_CRM_DEADLINE"]
    else:
        df["on_time"] = None

    # Km por informe
    if "UF_CRM_1715249307354" in df.columns:
        df["km"] = pd.to_numeric(
            df["UF_CRM_1715249307354"], errors="coerce"
        )
    else:
        df["km"] = None

    # Correcciones / reaperturas
    if "UF_CRM_REOPEN_COUNT" in df.columns:
        df["reopen_count"] = pd.to_numeric(
            df["UF_CRM_REOPEN_COUNT"], errors="coerce"
        ).fillna(0)
    else:
        df["reopen_count"] = 0

    # Rentabilidad por informe (si hay coste)
    if "UF_CRM_COST" in df.columns:
        df["cost"] = pd.to_numeric(
            df["UF_CRM_COST"], errors="coerce"
        )
        df["revenue"] = pd.to_numeric(
            df["OPPORTUNITY"], errors="coerce"
        ).fillna(0)
        df["profit"] = df["revenue"] - df["cost"]
    else:
        df["profit"] = None

    return df

# =====================================
# MAIN
# =====================================

def main():
    last_id = get_last_id(OUTPUT_CSV)
    if last_id is not None:
        print(f"Modo incremental activo. Buscando deals con ID > {last_id}")
    else:
        print("Realizando extraccion completa...")

    df_new = extract_deals(last_id=last_id)
    print(f"Nuevos registros extraidos: {len(df_new)}")

    if df_new.empty:
        print("El CSV esta al dia. No hay registros nuevos.")
        return

    print("Transformando nuevos datos...")
    df_new = transform_deals(df_new)

    print("Actualizando archivo CSV...")
    file_exists = OUTPUT_CSV.exists()

    df_new.to_csv(
        OUTPUT_CSV,
        mode="a" if file_exists else "w",
        header=not file_exists,
        index=False,
        encoding="utf-8"
    )

    print(f"CSV actualizado correctamente en: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
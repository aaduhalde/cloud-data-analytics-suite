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

DATA_DIR = PROJECT_ROOT / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEADS_CSV = DATA_DIR / "crm_marketing_leads_3.csv"
DEALS_CSV = DATA_DIR / "crm_marketing_deals_3.csv"

# =====================================
# CAMPOS CUSTOM / ESPERADOS
# =====================================

FIELD_LEAD_SOURCE = "SOURCE_ID"
FIELD_UTM_SOURCE = "UTM_SOURCE"
FIELD_UTM_MEDIUM = "UTM_MEDIUM"
FIELD_AD_COST = "UF_CRM_AD_COST"   # inversión marketing (si existe)

# =====================================
# HELPER INCREMENTAL
# =====================================

def get_last_id(csv_path):
    """Obtiene el último ID registrado en un CSV de manera eficiente."""
    if not csv_path.exists():
        return None
    try:
        df_ids = pd.read_csv(csv_path, usecols=["ID"])
        if not df_ids.empty:
            return int(df_ids["ID"].max())
    except Exception as e:
        print(f"No se pudo leer {csv_path.name} ({e}). Carga completa.")
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
# EXTRACCIÓN LEADS
# =====================================

def extract_leads(last_id=None):
    fields = [
        "ID",
        "DATE_CREATE",
        "STATUS_ID",
        FIELD_LEAD_SOURCE,
        FIELD_UTM_SOURCE,
        FIELD_UTM_MEDIUM,
        "CONTACT_ID",
        "COMPANY_ID",
        "OPPORTUNITY"
    ]

    params = {"select": fields}
    if last_id is not None:
        params["filter"] = {">ID": last_id}

    leads = fetch_all(
        method="crm.lead.list",
        params=params
    )

    return pd.DataFrame(leads)

# =====================================
# EXTRACCIÓN DEALS
# =====================================

def extract_deals(last_id=None):
    fields = [
        "ID",
        "DATE_CREATE",
        "CLOSEDATE",
        "STAGE_ID",
        "OPPORTUNITY",
        "CONTACT_ID",
        "COMPANY_ID"
    ]

    params = {"select": fields}
    if last_id is not None:
        params["filter"] = {">ID": last_id}

    deals = fetch_all(
        method="crm.deal.list",
        params=params
    )

    return pd.DataFrame(deals)

# =====================================
# TRANSFORMACIONES MARKETING & VENTAS
# =====================================

def transform(leads_df, deals_df):
    # -----------------------------
    # Normalización fechas
    # -----------------------------
    for df in [leads_df, deals_df]:
        if not df.empty:
            for col in df.columns:
                if "DATE" in col:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

    # -----------------------------
    # LEADS
    # -----------------------------
    if not leads_df.empty:
        leads_df["is_converted"] = leads_df["STATUS_ID"].astype(str).str.contains(
            "CONVERT", case=False, na=False
        )

        leads_df["lead_channel"] = (
            leads_df[FIELD_UTM_SOURCE]
            .fillna(leads_df[FIELD_LEAD_SOURCE])
            .fillna("UNKNOWN")
        )

        leads_df["ad_cost"] = None  # preparado para futura integración

    # -----------------------------
    # DEALS
    # -----------------------------
    if not deals_df.empty:
        deals_df["is_won"] = deals_df["CLOSEDATE"].notna()

        deals_df["revenue"] = pd.to_numeric(
            deals_df["OPPORTUNITY"], errors="coerce"
        ).fillna(0)

        # FACTURACIÓN MEDIA NUEVO CLIENTE (proxy)
        deals_df["customer_id"] = (
            deals_df["COMPANY_ID"]
            .fillna(deals_df["CONTACT_ID"])
        )

        first_deal = (
            deals_df
            .sort_values("DATE_CREATE")
            .drop_duplicates("customer_id")
        )

        first_deal["is_new_customer"] = True

        deals_df = deals_df.merge(
            first_deal[["ID", "is_new_customer"]],
            on="ID",
            how="left"
        )

        # CLIENTES RECURRENTES
        deal_counts = (
            deals_df.groupby("customer_id")
            .size()
            .reset_index(name="deal_count")
        )

        deals_df = deals_df.merge(
            deal_counts,
            on="customer_id",
            how="left"
        )

        deals_df["is_recurrent"] = deals_df["deal_count"] > 1

    return leads_df, deals_df

# =====================================
# HELPER DE GUARDADO ACCUMULATIVO
# =====================================

def save_incremental(df, csv_path):
    if df.empty:
        print(f"Sin nuevos datos para {csv_path.name}.")
        return

    file_exists = csv_path.exists()
    df.to_csv(
        csv_path,
        mode="a" if file_exists else "w",
        header=not file_exists,
        index=False,
        encoding="utf-8"
    )
    print(f"Se agregaron {len(df)} filas a: {csv_path.name}")

# =====================================
# MAIN
# =====================================

def main():
    last_lead_id = get_last_id(LEADS_CSV)
    last_deal_id = get_last_id(DEALS_CSV)

    print(f"Buscando Leads nuevos (ID > {last_lead_id})...")
    leads_df = extract_leads(last_id=last_lead_id)

    print(f"Buscando Deals nuevos (ID > {last_deal_id})...")
    deals_df = extract_deals(last_id=last_deal_id)

    if leads_df.empty and deals_df.empty:
        print("Ambos archivos CSV están al día.")
        return

    print("Transformando datos nuevos...")
    leads_df, deals_df = transform(leads_df, deals_df)

    print("Actualizando archivos CSV...")
    save_incremental(leads_df, LEADS_CSV)
    save_incremental(deals_df, DEALS_CSV)

    print("Proceso completado.")

if __name__ == "__main__":
    main()
from pathlib import Path
import requests
import sys

# =====================================
# CONFIGURACIÓN
# =====================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from auth.bitrix_config import BITRIX_WEBHOOK_URL

# =====================================
# =====================================

def get_total(method, params=None):
    url = f"{BITRIX_WEBHOOK_URL}{method}.json"
    params = params or {}

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Bitrix devuelve total en diferentes niveles
    if "total" in data:
        return data["total"]

    result = data.get("result", {})
    if isinstance(result, dict) and "total" in result:
        return result["total"]

    return 0

def audit_record_counts():
    print("\n=== AUDITORÍA DE VOLUMEN DE DATOS BITRIX24 ===\n", flush=True)

    counts = {
        "Leads (crm.lead)": get_total("crm.lead.list"),
        "Deals (crm.deal)": get_total("crm.deal.list"),
        "Contactos (crm.contact)": get_total("crm.contact.list"),
        "Empresas (crm.company)": get_total("crm.company.list"),
        "Tareas (tasks.task)": get_total("tasks.task.list"),
    }

    for entity, total in counts.items():
        print(f"{entity}: {total:,} registros", flush=True)

if __name__ == "__main__":
    audit_record_counts()

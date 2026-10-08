from pathlib import Path
import requests
import sys


# Resolver root del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralizado
from auth.bitrix_config import BITRIX_WEBHOOK_URL


def get_user_profile():
    url = f"{BITRIX_WEBHOOK_URL}profile"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json().get("result", {})

def get_user_access():
    url = f"{BITRIX_WEBHOOK_URL}user.access"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json().get("result")

def main():
    try:
        print("Consultando Bitrix24...\n")

        profile = get_user_profile()
        access = get_user_access()

        first_name = profile.get("NAME", "")
        last_name = profile.get("LAST_NAME", "")
        user_id = profile.get("ID", "")
        is_admin = profile.get("ADMIN", False)

        print("Conexión exitosa con Bitrix24\n")
        print("Usuario autenticado")
        #print(f"ID       : {user_id}")
        #print(f"Nombre   : {first_name} {last_name}")
        print(f"Admin    : {'Sí' if is_admin else 'No'}\n")

        print("Permisos por módulo:")

        # CASO ADMIN
        if access is True:
            print("✔ Usuario administrador")
            print("✔ Acceso total a todos los módulos (CRM, tareas, usuarios, etc.)")
            return

        # CASO NO ADMIN
        if isinstance(access, dict):
            for module, permissions in access.items():
                print(f"\n📦 Módulo: {module}")
                if isinstance(permissions, dict):
                    for perm, value in permissions.items():
                        print(f"   - {perm}: {value}")
                else:
                    print(f"   - Permiso: {permissions}")
        else:
            print("⚠️ Formato de permisos inesperado:", access)

    except requests.exceptions.RequestException as e:
        print("❌ Error de conexión con Bitrix24")
        print(str(e))

if __name__ == "__main__":
    main()

import sys
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN DE RUTAS Y DRIVER
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from auth.driver_postgres import get_db_connection

VIEWS_DIR = PROJECT_ROOT / "sql" / "views"

# =============================================================================
# EJECUTOR DE VISTAS ANALÍTICAS
# =============================================================================

def execute_view_files():
    """Busca y ejecuta los archivos .sql en /sql/views/."""
    if not VIEWS_DIR.exists():
        print(f"⚠️ El directorio {VIEWS_DIR} no existe.")
        return

    sql_files = sorted(list(VIEWS_DIR.glob("*.sql")))

    if not sql_files:
        print(f"ℹ️ No se encontraron archivos .sql en {VIEWS_DIR}")
        return

    print(f"📊 Creando/Actualizando Vistas Analíticas ({len(sql_files)} archivos en sql/views/):\n")

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            for file_path in sql_files:
                relative_path = file_path.relative_to(PROJECT_ROOT)
                print(f"▶️ Ejecutando: {relative_path} ...", end=" ")

                with open(file_path, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                if not sql_content.strip():
                    print("⏩ [OMITIDO - Archivo vacío]")
                    continue

                cursor.execute(sql_content)
                print("✅ [OK]")

        conn.commit()
        print("\n🎉 Todas las vistas analíticas se crearon/actualizaron correctamente.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR durante la creación de las vistas SQL. Se realizó ROLLBACK.")
        print(f"Detalle del error: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    execute_view_files()
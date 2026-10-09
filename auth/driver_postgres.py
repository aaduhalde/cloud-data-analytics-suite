import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Ruta raíz del proyecto (cloud-data-analytics-suite/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el .env en la raíz
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Lectura estricta de credenciales desde el .env
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Validación para asegurar que el .env contenga las variables necesarias
REQUIRED_VARS = {
    "POSTGRES_HOST": POSTGRES_HOST,
    "POSTGRES_USER": POSTGRES_USER,
    "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
    "POSTGRES_DB": POSTGRES_DB,
    "POSTGRES_PORT": POSTGRES_PORT
}

missing_vars = [var for var, value in REQUIRED_VARS.items() if not value]

if missing_vars:
    raise ValueError(
        f"❌ Faltan las siguientes variables de entorno en el archivo .env: {', '.join(missing_vars)}"
    )


def ensure_database_exists():
    """Verifica si la base de datos configurada en .env existe en PostgreSQL. Si no existe, la crea."""
    try:
        # Conexión a la base de datos de mantenimiento 'postgres'
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname="postgres",
            port=POSTGRES_PORT
        )
        # Modo autocommit obligatorio para ejecutar CREATE DATABASE en PostgreSQL
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            # Consultar catálogo interno de bases de datos
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (POSTGRES_DB,))
            exists = cursor.fetchone()

            if not exists:
                print(f"⚠️ La base de datos '{POSTGRES_DB}' no existe. Creándola...")
                # Uso de sql.Identifier para escapar correctamente el nombre de la BD
                query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(POSTGRES_DB))
                cursor.execute(query)
                print(f"✅ Base de datos '{POSTGRES_DB}' creada exitosamente.")
            else:
                print(f"ℹ️ Base de datos '{POSTGRES_DB}' verificada en el servidor.")

        conn.close()
    except Exception as e:
        print(f"❌ Error al verificar/crear la base de datos '{POSTGRES_DB}': {e}")
        raise e


def get_db_connection():
    """Garantiza la existencia de la base de datos y retorna una conexión activa a la misma."""
    ensure_database_exists()

    try:
        connection = psycopg2.connect(
            host=POSTGRES_HOST,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
            port=POSTGRES_PORT
        )
        return connection
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}): {e}")
        raise e


if __name__ == "__main__":
    # Permite ejecutar 'python auth/driver_postgres.py' independientemente para testear la BD
    ensure_database_exists()
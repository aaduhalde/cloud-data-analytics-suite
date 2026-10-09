import os
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# =====================================
# METADATA PROYECTO
# =====================================

PROJECT_NAME = "Bitrix24 Cloud Data Analytics Suite"
AUTHOR = "Alejandro Adrian Duhalde"
CONTACT_EMAIL = "aaduhalde@outlook.es"

# =====================================
# CONFIGURACIÓN Y CARGA DE ENTORNO
# =====================================

BASE_DIR = Path(__file__).resolve().parent

# Carga del .env ubicado en la raíz del proyecto
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

LOG_FILE = BASE_DIR / "output" / "run.log"

SCRIPTS = [
    BASE_DIR / "auth" / "driver_postgres.py",
    BASE_DIR / "auth" / "bitrix24_auth.py",
    BASE_DIR / "scripts" / "volumen_datos.py",  # Auditar volumen de datos
    BASE_DIR / "scripts" / "crm_productividad_deal.py",
    BASE_DIR / "scripts" / "crm_peritos_deals.py",
    BASE_DIR / "scripts" / "crm_marketing_ventas.py",
    BASE_DIR / "scripts" / "01_run_schema.py",
    BASE_DIR / "scripts" / "load_csv_to_postgres.py",
    BASE_DIR / "scripts" / "02_run_views.py",
    ]

# =====================================
# HELPERS
# =====================================

def print_header(start_time, log):
    header = f"""
========================================================
 PROYECTO : {PROJECT_NAME}
 AUTOR    : {AUTHOR}
 CONTACTO : {CONTACT_EMAIL}

 INICIO   : {start_time}
========================================================
"""
    print(header)
    log.write(header)


def print_footer(end_time, elapsed, log):
    footer = f"""
========================================================
 FIN PIPELINE : {end_time}
 DURACIÓN     : {elapsed}
 ESTADO       : FINALIZADO
========================================================
"""
    print(footer)
    log.write(footer)

# =====================================
# PIPELINE
# =====================================

def run_scripts(log):
    for script in SCRIPTS:
        header = f"\n===== Ejecutando: {script.name} =====\n"
        print(header)
        log.write(header)

        process = subprocess.Popen(
            ["python", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()  # Hereda las variables del .env cargadas a los subprocesos
        )

        stdout, stderr = process.communicate()

        if stdout:
            print(stdout)
            log.write(stdout)

        if stderr:
            print("❌ ERROR:")
            print(stderr)
            log.write("\nERROR:\n")
            log.write(stderr)

        footer = (
            f"===== Fin: {script.name} "
            f"| exit code {process.returncode} =====\n"
        )
        print(footer)
        log.write(footer)

        if process.returncode != 0:
            error_msg = (
                f"Script fallido : {script.name}\n"
                f"Exit code      : {process.returncode}\n"
                f"Detalle error  : {stderr.strip() or 'Sin detalle en stderr'}"
            )
            raise RuntimeError(error_msg)

# =====================================
# MAIN
# =====================================

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(exist_ok=True)

    start_time = datetime.now()

    with LOG_FILE.open("a", encoding="utf-8") as log:
        print_header(start_time, log)

        try:
            run_scripts(log)
            status = "OK"
        except Exception as e:
            status = f"ERROR\n{e}"
            print(f"⛔ {status}")
            log.write(f"\n{status}\n")
            raise SystemExit(1)

        end_time = datetime.now()
        elapsed = end_time - start_time

        print_footer(end_time, elapsed, log)
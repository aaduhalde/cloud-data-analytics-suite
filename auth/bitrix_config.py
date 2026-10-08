import os
from pathlib import Path

# Raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Webhook Bitrix24 desde variable de entorno
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
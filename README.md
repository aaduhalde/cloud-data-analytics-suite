# Cloud Data Analytics Suite

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)
![Automation](https://img.shields.io/badge/automation-GitHub%20Actions-orange.svg)

**Solución integral de Business Intelligence** diseñada para transformar datos operativos de **Bitrix24** en decisiones estratégicas visualizadas en **Notion**.

---

## Descripción del Sistema
Este proyecto implementa un pipeline **ETL (Extract, Transform, Load)** automatizado que centraliza la dispersión de datos. Extrae información de ventas, tareas, peritos y marketing, procesa KPIs críticos mediante Python y los disponibiliza en dashboards dinámicos de Looker Studio embebidos en el espacio de trabajo del cliente.

## Arquitectura Técnica
El flujo de datos sigue una arquitectura serverless de bajo costo:
* **Source:** Bitrix24 API (REST Webhook).
* **Engine:** Python 3.9 (Pandas para normalización y cálculo de KPIs).
* **Orquestación:** GitHub Actions (Cron job diario 02:00 AM).
* **Storage:** Google Drive (CSV) + Google Sheets API.
* **Visualización:** Looker Studio (Dashboards) embebido en Notion.

---

## Configuración e Instalación

### 1. Requisitos Previos
* **Bitrix24:** Webhook con permisos para `crm`, `tasks` y `user`.
* **Google Cloud:** Service Account con acceso de edición a Drive y Sheets.
* **GitHub:** Repositorio activo para configurar Actions.

### 2. Variables de Entorno (Secrets)
Configura los siguientes secretos en tu repositorio (`Settings > Secrets > Actions`):
| Secret | Descripción |
| :--- | :--- |
| `BITRIX_WEBHOOK_URL` | URL completa del Webhook de Bitrix24. |
| `GCP_SERVICE_ACCOUNT` | Contenido del archivo JSON de la cuenta de servicio. |
| `SPREADSHEET_ID` | ID de la hoja de Google Sheets de destino. |

---

## Despliegue y Automatización
El sistema se despliega automáticamente mediante **GitHub Actions**. El pipeline realiza:
1.  **Extracción:** Conexión vía API a Bitrix24.
2.  **Limpieza:** Unificación de zonas, tipos y limpieza de fechas.
3.  **KPIs:** Cálculo de rentabilidad, tiempos de resolución y tasas de conversión.
4.  **Carga:** Actualización de Google Sheets para alimentar Looker Studio.

---

## Estructura de Dashboards Entregados
1.  **Financiero:** Ingresos, beneficio neto, facturación y morosidad.
2.  **Productividad:** Informes emitidos, % en plazo y tiempos de respuesta.
3.  **Peritos:** Rendimiento por persona, km recorridos y rentabilidad.
4.  **Marketing & Ventas:** Leads por canal, tasa de conversión y CAC.

---

## Comandos Útiles (Desarrollo)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el pipeline completo manualmente
python run.py --all

# Validar conexión con Bitrix24
python auth/bitrix24_auth.py --test
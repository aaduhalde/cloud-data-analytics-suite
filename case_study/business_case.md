# Business Case: Suite de Analytics & Dashboards BI
**Proyecto:** Bitrix24 Cloud Data Analytics Suite  
**Arquitectura:** Bitrix24 API REST $\rightarrow$ ETL Python (Carga Incremental) $\rightarrow$ Vistas SQL (PostgreSQL) $\rightarrow$ Archivos CSV Processed $\rightarrow$ Dashboards BI Embebidos en Notion  
**Autor / Especialista:** Alejandro Adrián Duhalde  

---

## 1. Resumen Ejecutivo (Executive Summary)

Las empresas de servicios técnicos y periciales sufren habitualmente de **opacidad operativa y toma de decisiones a ciegas**. Aunque Bitrix24 registra datos operacionales diariamente (deals, tiempos, tareas, estados, expedientes), la falta de un modelo analítico estructurado impide evaluar la eficiencia operativa, la rentabilidad real de los peritos y el rendimiento de las acciones de marketing.

### La Solución Implementada
Se desarrolló un **pipeline de datos local, híbrido y eficiente** que extrae los datos del CRM de Bitrix24 mediante scripts en Python, aplicando lógica de **carga incremental** (`>ID`) para optimizar el consumo de la API REST y evitar transferencias duplicadas de datos. 

Los datos se persisten y modelan mediante **Vistas Analíticas en PostgreSQL**, las cuales consolidan y transforman las métricas clave (KPIs) para exportarlas a archivos CSV livianos dentro del repositorio del proyecto. Estos CSV alimentan **dashboards interactivos embebidos centralizadamente en Notion**.

---

## 2. Definición del Problema vs. Solución de Negocio

| Situación Sin Analytics (Antes) | Solución con PostgreSQL & Dashboards (Ahora) | Impacto / Beneficio |
| :--- | :--- | :--- |
| **Cuellos de botella invisibles:** Desconocimiento del tiempo medio entre el encargo y la visita pericial. | **Monitor de Productividad:** Control estricto del SLA y tiempos de respuesta por fase. | Reducción del ciclo de vida del expediente y mayor satisfacción del cliente. |
| **Incertidumbre en la rentabilidad:** Incapacidad de correlacionar honorarios, coste e hitos periciales. | **KPIs por Perito:** Análisis individualizado de margen, reaperturas/correcciones y km recorridos. | Identificación de peritos de alto rendimiento y corrección de desviaciones operativas. |
| **Gasto ciego en captación:** Desconocimiento del origen real de los leads convertidos. | **Atribución de Marketing & Ventas:** Seguimiento de leads por canal, recurrencia de clientes y tasa de conversión. | Optimización del presupuesto de marketing enfocando recursos en canales rentables. |
| **Dependencia de la infraestructura en la nube:** Costes fijos recurrentes de SaaS ETL o connectors. | **Arquitectura Local/SQL Autónoma:** Pipeline en Python + Vistas PostgreSQL + Exportación CSV. | **Cero costes fijos mensuales** de infraestructura o conectores de terceros. |

---

## 3. Modelo de Datos Analítico: Vistas PostgreSQL

Para garantizar el máximo rendimiento y mantenibilidad, la lógica de negocio y las agregaciones de KPIs se estructuran en **3 Vistas Analíticas Principales** dentro del motor PostgreSQL, listas para consumo de BI:

### Vista 1: `vw_crm_productividad`
* **Propósito:** Medir la capacidad operativa global, tiempos de atención y eficiencia logística.
* **Métricas & KPIs agregados:**
  * **Total de Informes Emitidos:** Conteo de expedientes cerrados (`is_closed`).
  * **Tiempo Medio de Resolución:** Diferencia en días entre fecha de creación (`DATE_CREATE`) y fecha de cierre (`CLOSEDATE`).
  * **% Cumplimiento de Plazo (SLA):** Porcentaje de informes cuya `CLOSEDATE` $\le$ `UF_CRM_DEADLINE`.
  * **Tiempo Medio Encargo $\rightarrow$ Visita:** Días entre creación y `UF_CRM_VISIT_DATE`.
  * **Kilómetros Totales:** Sumatoria mensual del campo `UF_CRM_1715249307354`.
  * **Ratio Aceptación de Presupuestos:** Porcentaje de presupuestos aprobados con `OPPORTUNITY > 0`.

### Vista 2: `vw_crm_peritos`
* **Propósito:** Evaluar el desempeño individual, calidad técnica y margen de contribución por perito.
* **Métricas & KPIs agregados:**
  * **Volumen por Perito:** Asignación de cargas de trabajo por `ASSIGNED_BY_ID`.
  * **Tiempo Medio por Expediente:** Días de resolución promedio por profesional.
  * **Índice de Correcciones / Reaperturas:** Frecuencia del campo `UF_CRM_REOPEN_COUNT`.
  * **Kilómetros por Informe:** Control de desplazamientos y costes de viáticos por profesional.
  * **Rentabilidad por Informe:** Cálculo del margen de beneficio: $\text{Profit} = \text{Revenue} - \text{Cost}$ (usando `OPPORTUNITY` y `UF_CRM_COST`).

### Vista 3: `vw_crm_marketing_ventas`
* **Propósito:** Rastrear el embudo comercial desde el lead hasta la retención de clientes.
* **Métricas & KPIs agregados:**
  * **Atribución de Leads:** Clasificación por origen y canal (`UTM_SOURCE` / `SOURCE_ID`).
  * **Tasa de Conversión (Lead $\rightarrow$ Cliente):** % de leads con estado `CONVERTED`.
  * **Facturación Media por Nuevo Cliente:** Promedio de valor de cierre (`revenue`) en el primer contrato del cliente (`is_new_customer`).
  * **Ratio de Clientes Recurrentes:** % de clientes con más de un expediente registrado (`deal_count > 1`).
  * **Coste de Adquisición (CAC Estimado):** Preparado para integrar costes publicitarios (`ad_cost`).

---

## 4. Arquitectura del Flujo de Datos

```text
┌─────────────────┐      HTTP POST      ┌─────────────────────────┐
│  Bitrix24 CRM   │ ──────────────────> │   ETL Script (Python)   │
│  (REST API)     │   (Filtro >ID)      │  (auth/bitrix_config)   │
└─────────────────┘                     └────────────┬────────────┘
                                                     │
                                                     ▼
┌─────────────────┐      Export CSV     ┌─────────────────────────┐
│ Dashboards BI   │ <────────────────── │ Vistas Analíticas SQL   │
│ (Looker/Notion) │   (data/processed)  │ (PostgreSQL DB)         │
└─────────────────┘                     └─────────────────────────┘
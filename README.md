# LeadSniper Backend

Backend worker autónomo para el sistema LeadSniper. Scrapeea sitios web para extraer emails de contacto y envía emails de outreach usando Resend.

**🚀 Para deployment en producción (Railway), ver sección "Deployment" al final.**

## Arquitectura

```
leadsniper_backend/
├── src/
│   ├── domain/           # Modelos Pydantic
│   ├── infrastructure/   # Repositorio Supabase
│   ├── services/         # Scraper y Mailer
│   └── utils/            # Logger con Rich
├── sql/                  # Esquema SQL para Supabase
├── main.py               # Entry point
├── requirements.txt
└── .env.example
```

## Requisitos

- Python 3.10+
- Cuenta de Supabase
- Cuenta de Resend con dominio verificado

## Instalación

1. **Clonar y crear entorno virtual:**
```bash
cd leadsniper_backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Instalar navegador para Playwright:**
```bash
playwright install chromium
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

5. **Crear tablas en Supabase:**
   - Ir a tu proyecto en Supabase
   - Abrir el SQL Editor
   - Ejecutar el contenido de `sql/schema.sql`

## Uso

```bash
python main.py
```

El worker correrá indefinidamente, procesando:
1. Dominios pendientes de scraping
2. Emails en cola para envío

## Estados de un Lead

| Estado | Descripción |
|--------|-------------|
| `pending` | Esperando ser scrapeado |
| `scraping` | En proceso de scraping |
| `scraped` | Scrapeado sin email encontrado |
| `queued_for_send` | Email encontrado, listo para enviar |
| `sending` | Email siendo enviado |
| `sent` | Email enviado exitosamente |
| `failed` | Error en algún paso |

## Variables de Entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `SUPABASE_URL` | Sí | URL de tu proyecto Supabase |
| `SUPABASE_KEY` | Sí | API key de Supabase |
| `RESEND_API_KEY` | Sí | API key de Resend |
| `FROM_EMAIL` | Sí | Email remitente (dominio verificado) |
| `FROM_NAME` | No | Nombre del remitente |
| `CALENDAR_LINK` | No | Link para agendar demos |

## Agregar Dominios para Scraping

Insertar directamente en Supabase:

```sql
INSERT INTO leads (domain) VALUES 
  ('empresa1.com'),
  ('startup-tech.io'),
  ('negocio.es');
```

O mediante el Dashboard de Supabase.

---

## 🎯 Domain Hunter - Conseguir miles de dominios automáticamente

Para facilitar la obtención masiva de dominios, incluimos `domain_hunter.py`: un script que busca en Google 24/7 con delays largos para evitar bloqueos.

### Uso rápido

1. **Editar configuración:**
   ```bash
   # Abrir domain_hunter_config.py y configurar:
   NICHO = "inmobiliarias"  # Tu nicho
   CIUDADES = ["Rosario", "Buenos Aires", "Córdoba"]
   USER_ID = None  # Tu user_id para guardar en Supabase automáticamente
   ```

2. **Ejecutar:**
   ```bash
   python domain_hunter.py
   ```

3. **Dejar corriendo:** El script hace búsquedas cada 30-90 segundos, puede correr durante horas/días acumulando miles de dominios.

4. **Resultado:** Genera `domains_[nicho]_[fecha].txt` con todos los dominios encontrados.

**Estimación:** Corriendo 8 horas → 2000-5000 dominios

---

## 🚀 Deployment en Producción (Railway)

Para que los usuarios de Botslode NO tengan que ejecutar Python localmente, deployá el worker en un servidor que corra 24/7.

### Pre-requisitos

- Cuenta de GitHub
- Cuenta de Railway ([railway.app](https://railway.app) - gratis)
- Supabase con tablas creadas

### Paso 1: Subir a GitHub

```bash
git init
git add .
git commit -m "Hunter Bot worker"
git remote add origin https://github.com/TU_USUARIO/hunter-bot-worker.git
git branch -M main
git push -u origin main
```

### Paso 2: Deployar en Railway

1. **Crear proyecto:**
   - [railway.app](https://railway.app) → "New Project"
   - "Deploy from GitHub repo"
   - Seleccionar tu repo

2. **Configurar variables:**
   
   En Railway → Variables:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJ... (service_role key)
   ```
   
   ⚠️ **IMPORTANTE:** Usar la **service_role key** (no la anon key).
   
   Ubicación: Supabase Dashboard → Settings → API → service_role

3. **Deploy automático:**
   - Railway detecta `Dockerfile` y `railway.json`
   - Build: instala deps + Playwright + Chromium
   - Start: ejecuta `python start_workers.py` (lanza 2 workers en paralelo)
     - **Domain Hunter Worker**: Busca dominios en Google 24/7
     - **LeadSniper Worker**: Procesa leads y envía emails

### Paso 3: Verificar en Logs de Railway

Deberías ver algo como:

```
🤖 HUNTERBOT - WORKER MANAGER
======================================================================
🚀 Iniciando DOMAIN-HUNTER...
🚀 Iniciando LEADSNIPER...
✅ Ambos workers iniciados correctamente

[DOMAIN-HUNTER] 👥 1 usuario(s) con bot activo
[DOMAIN-HUNTER] 🎯 Usuario: xxx... | Nicho: inmobiliarias
[DOMAIN-HUNTER] 🔍 Buscando: "inmobiliarias en Rosario Argentina"
[DOMAIN-HUNTER] 💾 5 dominios guardados en Supabase

[LEADSNIPER] 🔍 Procesando 5 dominios pendientes
[LEADSNIPER] ✉️ Email encontrado: info@ejemplo.com
[LEADSNIPER] 📧 Email enviado exitosamente
```

### ✅ Resultado

Los usuarios de Botslode:
- ✅ Solo usan la app (no instalan nada)
- ✅ **Prenden el bot** desde Botslode
- ✅ El Domain Hunter busca dominios automáticamente en Google
- ✅ El LeadSniper procesa los dominios y envía emails
- ✅ Ven logs en tiempo real de ambos workers

**Ambos workers** procesan la cola de todos los usuarios 24/7 en segundo plano.

### 💰 Costos

Railway: ~$5-10/mes (500 horas gratis, luego por uso)

### 🔧 Troubleshooting

**Los dominios quedan en PENDIENTE:**
- Verificar que `SUPABASE_KEY` sea la service_role key
- Ejecutar `sql/fix_rls_policies.sql` en Supabase

**Logs no aparecen en Botslode:**
- Supabase → Database → Replication
- Activar Realtime para `hunter_logs` y `leads`

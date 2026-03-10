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
| `FROM_EMAIL` | Sí | Email remitente (ej: `manuel@getbotlode.com`, dominio verificado en Resend) |
| `FROM_NAME` | No | Nombre del remitente (ej: `Manuel de Botlode`) |
| `CALENDAR_LINK` | No | Link para agendar demos |
| `METALWAILERS_EMAIL_IMAGE_URL` | No | URL pública del flyer para emails Metalwailers (si no se setea, el correo se envía solo texto). Ver sección "Metalwailers" más abajo. |

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

**Domain Hunter no busca dominios en deploy (logs: "Sin usuarios activos" o sin actividad):**
- **Tras un reset de tablas:** `hunter_configs` y `domain_search_tracking` quedan vacíos. El Domain Hunter solo actúa para usuarios con `bot_enabled = true`. En Supabase: crear o actualizar al menos una fila en `hunter_configs` con tu `user_id` y `bot_enabled = true` (p. ej. `UPDATE hunter_configs SET bot_enabled = true WHERE user_id = 'tu-uuid';` o insertar una fila si no existe).
- **Variables en el servicio correcto:** Las variables (`SERPAPI_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) deben estar configuradas en el **servicio hunter-bot-worker** en Railway. Si solo están en otro servicio (p. ej. seeder-bot), el Domain Hunter no las ve.
- **Revisar logs:** "SERPAPI_KEY no configurada" → añadir la key en Railway. "Sin usuarios activos" → asegurar que exista al menos un usuario con `bot_enabled = true` en `hunter_configs`.

**Logs no aparecen en Botslode:**
- Supabase → Database → Replication
- Activar Realtime para `hunter_logs` y `leads`

---

## Metalwailers: imagen en el email y entregabilidad

### Imagen en el correo Metalwailers

El flyer ya está configurado por defecto con la URL pública en **Supabase Storage** (bucket `metalwailersmail`). En **Railway** no hace falta configurar nada; los correos incluyen la imagen. Para usar otra imagen, definí `METALWAILERS_EMAIL_IMAGE_URL` en Railway.



### Cómo intentar que llegue a Principal y no a Promociones (dominio nuevo)

Con un **dominio nuevo** (`metalwailersinfo.com`) Gmail suele clasificar el primer outreach como **Promociones**. No hay garantía, pero podés mejorar las chances:

1. **DNS (Resend):** En Resend, verificá el dominio `metalwailersinfo.com` y asegurate de tener **SPF, DKIM y DMARC** bien configurados. Resend te da los registros; eso mejora la reputación del remitente.

2. **Warmup:** Enviar poco al principio (p. ej. 10–20 correos/día), aumentar de a poco. Algunos servicios hacen “warmup” automático (inbox reach, etc.); no es obligatorio pero ayuda.

3. **Asunto y contenido más “conversacionales”:**
   - Evitá asuntos muy de marketing (“Potenciemos tu negocio juntos” suena a promoción). Podés probar algo más neutro, por ejemplo: “Consulta – [nombre empresa]” o “¿Te sirve si te paso info?” (y que el cuerpo sea breve y personal).
   - En el cuerpo: una línea corta, pregunta o CTA a **responder** (ej. “¿Te mando más datos por mail?”) suele ayudar a que Gmail lo vea como conversación.

4. **Tiempo:** A medida que el dominio envíe más y reciba respuestas/opens, Gmail puede ir moviendo correos a Principal. No es inmediato; con dominio nuevo puede llevar semanas.

En resumen: **imagen** → ya por defecto (Supabase); para otra imagen usá `METALWAILERS_EMAIL_IMAGE_URL`. **Promociones** → DNS correcto, warmup, asunto/cuerpo más personales y paciencia con el dominio nuevo.

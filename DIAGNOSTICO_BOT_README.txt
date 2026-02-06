================================================================================
🔍 DIAGNÓSTICO: BOT NO RECOPILA DOMINIOS
================================================================================

📋 RESUMEN DEL PROBLEMA
================================================================================

Tu bot 'domain_hunter_worker.py' debería estar recopilando dominios 
automáticamente de Google usando SerpAPI, pero no lo está haciendo. 
Este documento explica las causas más probables y cómo solucionarlas.

================================================================================
🎯 CÓMO FUNCIONA EL SISTEMA (Arquitectura)
================================================================================

Tu sistema tiene 2 BOTS trabajando juntos:

1. DOMAIN HUNTER WORKER (domain_hunter_worker.py)
   - Función: Busca dominios en Google usando SerpAPI
   - Qué hace:
     * Consulta 'hunter_configs' para ver usuarios con 'bot_enabled = true'
     * Usa un sistema de ROTACIÓN INTELIGENTE con:
       - 50+ nichos
       - 17 países latinoamericanos
       - 100+ ciudades
     * Guarda los dominios encontrados en la tabla 'leads' con status 'pending'
     * Trackea el progreso en 'domain_search_tracking'
   - Configuración: Necesita SERPAPI_KEY en .env

2. LEADSNIPER WORKER (main.py)
   - Función: Procesa los dominios que Domain Hunter agregó
   - Qué hace:
     1. Toma dominios con status 'pending'
     2. Los scrapea para extraer emails
     3. Envía emails a los que tienen email usando Resend
   - Configuración: Necesita SUPABASE_URL, SUPABASE_KEY

================================================================================
🚨 CAUSAS MÁS PROBABLES (en orden de frecuencia)
================================================================================

CAUSA #1: Bot NO está habilitado en la base de datos
────────────────────────────────────────────────────

Síntoma: No hay usuarios con 'bot_enabled = true' en 'hunter_configs'

Verificar:
  SELECT user_id, bot_enabled, nicho, ciudades, pais 
  FROM hunter_configs 
  WHERE bot_enabled = true;

Si esta query NO devuelve filas, el bot está apagado.

Solución:
  -- Reemplazar 'TU_USER_ID' con tu user_id real
  UPDATE hunter_configs 
  SET bot_enabled = true,
      nicho = 'inmobiliarias',
      ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario'],
      pais = 'Argentina'
  WHERE user_id = 'TU_USER_ID';


CAUSA #2: Falta SERPAPI_KEY en .env
────────────────────────────────────

Síntoma: El bot se inicia pero no puede hacer búsquedas

Verificar: Revisar tu archivo .env (está en .cursorignore)

Debe contener:
  SERPAPI_KEY=tu_serpapi_key_aqui
  SUPABASE_URL=https://tu-proyecto.supabase.co
  SUPABASE_KEY=tu_service_role_key

Cómo conseguir SERPAPI_KEY:
  1. Ir a https://serpapi.com/
  2. Crear cuenta (tiene plan gratuito con 100 búsquedas/mes)
  3. Copiar tu API Key
  4. Agregarla al .env

SIN SERPAPI_KEY, EL BOT NO PUEDE BUSCAR EN GOOGLE.


CAUSA #3: Worker NO está corriendo
───────────────────────────────────

Síntoma: Bot configurado correctamente pero no se agregan dominios

Verificar:
  - ¿Está corriendo domain_hunter_worker.py?
  - ¿O solo está corriendo main.py?

LOS 2 DEBEN ESTAR CORRIENDO:

Terminal 1: Domain Hunter (recopila dominios)
  python domain_hunter_worker.py

Terminal 2: LeadSniper (procesa dominios)
  python main.py

Nota: Si solo corre main.py, va a procesar dominios pero NO va a agregar nuevos.


CAUSA #4: Sistema de Tracking agotado
──────────────────────────────────────

Síntoma: El bot busca pero dice "Combinación agotada"

Verificar:
  SELECT 
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
      COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas
  FROM domain_search_tracking
  WHERE user_id = 'TU_USER_ID';

Si todas las combinaciones están agotadas, el bot debería resetear 
automáticamente, pero puedes forzarlo:

Solución:
  -- Opción 1: Resetear tracking
  UPDATE domain_search_tracking 
  SET is_exhausted = false, current_page = 0
  WHERE user_id = 'TU_USER_ID';

  -- Opción 2: Eliminar todo (el bot creará nuevas combinaciones)
  DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID';


CAUSA #5: Nicho/País muy saturado
──────────────────────────────────

Síntoma: Bot busca pero encuentra 0 dominios en cada búsqueda

El sistema tiene ROTACIÓN AUTOMÁTICA, pero si tu configuración manual 
está muy específica, puede que no encuentre nada.

Solución: Cambiar a otro nicho o país

  UPDATE hunter_configs 
  SET 
      nicho = 'agencias de marketing',  -- Cambiar nicho
      pais = 'México',                  -- Cambiar país
      ciudades = ARRAY['Ciudad de México', 'Guadalajara', 'Monterrey']
  WHERE user_id = 'TU_USER_ID';

  -- Resetear tracking
  DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID';

Nichos disponibles (están hardcodeados en el worker):
  - inmobiliarias, estudios contables, agencias de marketing
  - gimnasios, restaurantes, cafeterías, clínicas dentales
  - hoteles, agencias de turismo, fotógrafos
  - 50+ opciones más (ver domain_hunter_worker.py líneas 68-98)


CAUSA #6: SerpAPI sin créditos
───────────────────────────────

Síntoma: El bot corre pero todas las búsquedas fallan

SerpAPI tiene límite de búsquedas:
  - Plan gratuito: 100 búsquedas/mes
  - Plan pagado: más búsquedas

Verificar: Ir a https://serpapi.com/dashboard y revisar tus créditos


CAUSA #7: No existe registro en hunter_configs
───────────────────────────────────────────────

Síntoma: Tabla hunter_configs está vacía o no tiene tu user_id

Verificar:
  SELECT * FROM hunter_configs WHERE user_id = 'TU_USER_ID';

Solución: Crear el registro
  INSERT INTO hunter_configs (
      user_id, bot_enabled, nicho, ciudades, pais
  ) VALUES (
      'TU_USER_ID',
      true,
      'inmobiliarias',
      ARRAY['Buenos Aires', 'Córdoba', 'Rosario'],
      'Argentina'
  );

================================================================================
🛠️ PROCESO DE DIAGNÓSTICO PASO A PASO
================================================================================

PASO 1: Ejecutar diagnóstico completo
--------------------------------------
  1. Abrir Supabase SQL Editor
  2. Copiar todo el contenido de 'diagnostico_bot.sql'
  3. Pegar y ejecutar

Esto te va a mostrar:
  - ✅ Usuarios con bot activo
  - 📊 Estado del tracking
  - 📋 Dominios en la base de datos
  - 📝 Logs del bot
  - 📈 Estadísticas globales

PASO 2: Revisar resultados críticos
------------------------------------

Pregunta 1: ¿Hay usuarios con 'bot_enabled = true'?
  ❌ NO  → Solución: Activar bot (ver Causa #1)
  ✅ SÍ  → Continuar

Pregunta 2: ¿Hay dominios agregados recientemente (últimas 24hs)?
  ❌ NO  → El bot NO está funcionando
  ✅ SÍ  → El bot SÍ está funcionando

Pregunta 3: ¿Hay combinaciones activas en 'domain_search_tracking'?
  ❌ NO  → Resetear tracking (ver Causa #4)
  ✅ SÍ  → Continuar

Pregunta 4: ¿Hay logs del bot en las últimas horas?
  ❌ NO  → El worker NO está corriendo (ver Causa #3)
  ✅ SÍ  → Revisar mensajes de error en logs

PASO 3: Verificar archivo .env
-------------------------------
Debe contener:
  SERPAPI_KEY=tu_key_aqui
  SUPABASE_URL=https://...
  SUPABASE_KEY=eyJ...

PASO 4: Verificar que el worker esté corriendo
-----------------------------------------------
¿Está corriendo domain_hunter_worker.py?
Debe mostrar algo como:

  🔍 DOMAIN HUNTER WORKER - Iniciando
  ✅ SerpAPI configurada
  👥 1 usuario(s) con bot activo
  🎯 Usuario: 12345678... | Rotación automática activada
  🔍 Query SerpAPI: "inmobiliarias en Buenos Aires Argentina"
  ✅ Encontrados 15 dominios válidos

================================================================================
📊 CÓMO MONITOREAR EL BOT EN TIEMPO REAL
================================================================================

Ver logs del bot:
-----------------
  SELECT 
      created_at,
      level,
      action,
      domain,
      message
  FROM hunter_logs
  WHERE user_id = 'TU_USER_ID'
  ORDER BY created_at DESC
  LIMIT 50;

Ver últimos dominios agregados:
--------------------------------
  SELECT 
      domain,
      status,
      created_at
  FROM leads
  WHERE user_id = 'TU_USER_ID'
  ORDER BY created_at DESC
  LIMIT 20;

Ver estadísticas en vivo:
--------------------------
  SELECT 
      status,
      COUNT(*) as cantidad
  FROM leads
  WHERE user_id = 'TU_USER_ID'
  GROUP BY status;

================================================================================
🎯 SOLUCIÓN RÁPIDA (99% de los casos)
================================================================================

Si no quieres leer todo, ejecuta esto:

  -- 1. Activar bot
  UPDATE hunter_configs 
  SET bot_enabled = true
  WHERE user_id = 'TU_USER_ID';

  -- 2. Resetear tracking
  DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID';

  -- 3. Verificar
  SELECT 
      (SELECT bot_enabled FROM hunter_configs WHERE user_id = 'TU_USER_ID') as bot_activo,
      (SELECT COUNT(*) FROM leads WHERE user_id = 'TU_USER_ID') as total_leads;

LUEGO:
  1. Revisar que .env tenga SERPAPI_KEY
  2. Correr: python domain_hunter_worker.py
  3. Esperar 1-2 minutos
  4. Verificar que se agreguen dominios

================================================================================
🆘 CÓMO OBTENER TU USER_ID
================================================================================

Si no sabes tu user_id, ejecuta esto en Supabase:

  SELECT 
      id as user_id,
      email,
      created_at
  FROM auth.users
  ORDER BY created_at DESC;

Tu user_id es el campo 'id' de tu usuario.

================================================================================
📁 ARCHIVOS INCLUIDOS
================================================================================

1. diagnostico_bot.sql - SQL completo para ver toda la información
2. soluciones_bot.sql - Comandos SQL para solucionar problemas
3. DIAGNOSTICO_BOT_README.txt - Este archivo (explicación completa)

================================================================================
🚀 PRÓXIMOS PASOS
================================================================================

1. EJECUTAR 'diagnostico_bot.sql' en Supabase
2. IDENTIFICAR cuál de las 7 causas aplica a tu caso
3. EJECUTAR la solución correspondiente de 'soluciones_bot.sql'
4. VERIFICAR que el worker esté corriendo
5. MONITOREAR con las queries de tiempo real

================================================================================
🔧 CONFIGURACIÓN ÓPTIMA DEL BOT
================================================================================

Delays (en domain_hunter_worker.py):
  - MIN_DELAY_BETWEEN_SEARCHES = 3s (reducido con SerpAPI)
  - MAX_DELAY_BETWEEN_SEARCHES = 10s
  - CHECK_USERS_INTERVAL = 60s (cada minuto chequea usuarios)
  - DOMAIN_BATCH_SIZE = 20 (dominios por búsqueda)

Sistema de Rotación:
  - 50+ nichos disponibles
  - 17 países latinoamericanos
  - 100+ ciudades en total
  - Rotación inteligente: ciudad → país → nicho
  - Auto-reset: cuando todas las combinaciones se agotan

================================================================================
❓ PREGUNTAS FRECUENTES
================================================================================

P: ¿Cuántos dominios debería estar agregando el bot por día?
R: Depende de SerpAPI, pero con el plan gratuito (100 búsquedas/mes), 
   aproximadamente 60-120 dominios/mes.

P: ¿Puedo cambiar el nicho desde la base de datos?
R: Sí, pero el bot tiene ROTACIÓN AUTOMÁTICA. La config de hunter_configs 
   ya no se usa para elegir nicho (ver líneas 277-288 de domain_hunter_worker.py). 
   El sistema rota automáticamente entre todos los nichos.

P: ¿Por qué algunos dominios no tienen email?
R: Normal. El Domain Hunter solo agrega dominios (status 'pending'). 
   El LeadSniper los procesa después y busca emails. Si no encuentra, 
   el status queda en 'scraped' (sin email).

P: ¿Los dos workers deben estar corriendo siempre?
R: Sí. domain_hunter_worker.py agrega dominios, main.py los procesa.

P: ¿Puedo ver el bot en acción?
R: Sí, ejecuta 'python domain_hunter_worker.py' en la terminal y verás 
   los logs en tiempo real.

================================================================================

¿Necesitas más ayuda? Revisa los logs del bot en 'hunter_logs' para ver 
mensajes de error específicos.

================================================================================

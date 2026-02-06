-- ============================================================================
-- DEBUG: ¿Por qué el bot no funciona después del reinicio?
-- ============================================================================
-- User ID: 38152119-7da4-442e-9826-20901c65f42e
-- ============================================================================

-- PASO 1: Verificar que el tracking se creó correctamente
-- ============================================================================
SELECT 
    'TRACKING CREADO' as verificacion,
    COUNT(*) as total_combinaciones,
    COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas,
    MAX(last_searched_at) as ultima_busqueda
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Si total_combinaciones = 0, ejecutar el INSERT del archivo SOLUCION_TRACKING_VACIO.sql

-- ============================================================================
-- PASO 2: Ver las primeras 10 combinaciones
-- ============================================================================
SELECT 
    'COMBINACIONES EXISTENTES' as info,
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at,
    created_at
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY created_at
LIMIT 10;

-- ============================================================================
-- PASO 3: Ver si hay dominios NUEVOS (últimos 15 minutos)
-- ============================================================================
SELECT 
    'DOMINIOS RECIENTES' as info,
    domain,
    status,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutos_atras
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND created_at > NOW() - INTERVAL '15 minutes'
ORDER BY created_at DESC;

-- Si no hay resultados, el bot NO está agregando dominios

-- ============================================================================
-- PASO 4: Ver logs del Domain Hunter (últimos 10 minutos)
-- ============================================================================
SELECT 
    'LOGS DOMAIN HUNTER' as info,
    created_at,
    level,
    action,
    domain,
    message,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutos_atras
FROM hunter_logs
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND action = 'domain_added'
  AND created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;

-- ============================================================================
-- PASO 5: Ver TODOS los logs recientes (últimos 5 minutos)
-- ============================================================================
SELECT 
    'TODOS LOS LOGS RECIENTES' as info,
    created_at,
    level,
    action,
    domain,
    message,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutos_atras
FROM hunter_logs
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND created_at > NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC
LIMIT 50;

-- ============================================================================
-- PASO 6: Verificar configuración del bot
-- ============================================================================
SELECT 
    'CONFIGURACION BOT' as info,
    user_id,
    bot_enabled,
    nicho,
    ciudades,
    pais,
    is_active,
    resend_api_key IS NOT NULL as tiene_resend,
    updated_at
FROM hunter_configs
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- ============================================================================
-- PASO 7: Ver el último lead agregado
-- ============================================================================
SELECT 
    'ULTIMO LEAD' as info,
    domain,
    status,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as horas_atras
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY created_at DESC
LIMIT 1;

-- ============================================================================
-- PASO 8: Contar leads por hora (últimas 24 horas)
-- ============================================================================
SELECT 
    'LEADS POR HORA' as info,
    DATE_TRUNC('hour', created_at) as hora,
    COUNT(*) as cantidad_leads
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hora DESC;

-- ============================================================================
-- DIAGNÓSTICO BASADO EN RESULTADOS
-- ============================================================================

-- SI total_combinaciones = 0:
--   → El INSERT no se ejecutó correctamente
--   → Ejecutar el SQL completo de SOLUCION_TRACKING_VACIO.sql

-- SI total_combinaciones > 0 PERO last_searched_at IS NULL:
--   → El worker NO está leyendo el tracking
--   → Verificar que domain_hunter_worker.py esté corriendo en Railway
--   → Verificar SERPAPI_KEY en variables de entorno de Railway

-- SI hay logs "domain_added" recientes:
--   → El bot SÍ está corriendo
--   → Verificar si los dominios son duplicados (por eso no se insertan)

-- SI NO hay logs recientes:
--   → El worker NO está corriendo
--   → Verificar Railway logs
--   → Verificar que el servicio esté deployed

-- ============================================================================
-- COMANDOS DE EMERGENCIA
-- ============================================================================

-- Resetear todo el tracking (si está corrupto)
-- DELETE FROM domain_search_tracking 
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Ver variables de entorno necesarias en Railway:
-- SERPAPI_KEY (CRÍTICO)
-- SUPABASE_URL
-- SUPABASE_KEY
-- CHECK_USERS_INTERVAL=60
-- MIN_DELAY_BETWEEN_SEARCHES=3
-- MAX_DELAY_BETWEEN_SEARCHES=10

-- ============================================================================
-- FIN
-- ============================================================================

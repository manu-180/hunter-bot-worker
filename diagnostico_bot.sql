-- =============================================================================
-- DIAGNÓSTICO COMPLETO DEL BOT HUNTER - LeadSniper
-- Ejecutar en Supabase SQL Editor para ver toda la información
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. VERIFICAR USUARIOS CON BOT HABILITADO
-- -----------------------------------------------------------------------------
SELECT 
    '🔍 USUARIOS CON BOT ACTIVO' as seccion,
    user_id,
    bot_enabled,
    nicho,
    ciudades,
    pais,
    is_active,
    resend_api_key IS NOT NULL as tiene_resend_key,
    created_at,
    updated_at
FROM hunter_configs
WHERE bot_enabled = true
ORDER BY updated_at DESC;

-- Si esta query no devuelve filas, el bot NO ESTÁ HABILITADO para ningún usuario
-- Solución: UPDATE hunter_configs SET bot_enabled = true WHERE user_id = 'TU_USER_ID';

-- -----------------------------------------------------------------------------
-- 2. ESTADO DEL TRACKING DE BÚSQUEDAS (Sistema de Rotación)
-- -----------------------------------------------------------------------------
SELECT 
    '📊 TRACKING DE BÚSQUEDAS POR USUARIO' as seccion,
    user_id,
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at,
    updated_at
FROM domain_search_tracking
ORDER BY user_id, is_exhausted, current_page
LIMIT 50;

-- Si esta query está vacía, no hay tracking iniciado
-- Si todas las filas tienen is_exhausted = true, el bot resetea automáticamente

-- -----------------------------------------------------------------------------
-- 3. RESUMEN DE TRACKING POR USUARIO
-- -----------------------------------------------------------------------------
SELECT 
    '📈 RESUMEN DE TRACKING' as seccion,
    user_id,
    COUNT(*) as combinaciones_totales,
    COUNT(*) FILTER (WHERE is_exhausted = false) as combinaciones_activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as combinaciones_agotadas,
    SUM(total_domains_found) as dominios_encontrados_total,
    MAX(last_searched_at) as ultima_busqueda
FROM domain_search_tracking
GROUP BY user_id;

-- -----------------------------------------------------------------------------
-- 4. ESTADO DE LA TABLA LEADS (Dominios recopilados)
-- -----------------------------------------------------------------------------
SELECT 
    '📋 LEADS POR USUARIO Y STATUS' as seccion,
    user_id,
    status,
    COUNT(*) as cantidad,
    MIN(created_at) as primer_lead,
    MAX(created_at) as ultimo_lead
FROM leads
GROUP BY user_id, status
ORDER BY user_id, status;

-- -----------------------------------------------------------------------------
-- 5. LEADS RECIENTES (últimos 20 agregados)
-- -----------------------------------------------------------------------------
SELECT 
    '🆕 LEADS MÁS RECIENTES' as seccion,
    id,
    user_id,
    domain,
    email,
    status,
    created_at,
    updated_at
FROM leads
ORDER BY created_at DESC
LIMIT 20;

-- -----------------------------------------------------------------------------
-- 6. LOGS DEL HUNTER (últimos 50)
-- -----------------------------------------------------------------------------
SELECT 
    '📝 LOGS RECIENTES DEL BOT' as seccion,
    user_id,
    domain,
    level,
    action,
    message,
    created_at
FROM hunter_logs
ORDER BY created_at DESC
LIMIT 50;

-- -----------------------------------------------------------------------------
-- 7. ESTADÍSTICAS GLOBALES
-- -----------------------------------------------------------------------------
SELECT 
    '📊 ESTADÍSTICAS GLOBALES' as seccion,
    (SELECT COUNT(*) FROM hunter_configs WHERE bot_enabled = true) as usuarios_bot_activo,
    (SELECT COUNT(*) FROM hunter_configs) as usuarios_totales,
    (SELECT COUNT(*) FROM leads) as leads_totales,
    (SELECT COUNT(*) FROM leads WHERE status = 'pending') as leads_pendientes,
    (SELECT COUNT(*) FROM leads WHERE status = 'scraped') as leads_scrapeados,
    (SELECT COUNT(*) FROM leads WHERE status = 'queued_for_send') as leads_cola_envio,
    (SELECT COUNT(*) FROM leads WHERE status = 'sent') as leads_enviados,
    (SELECT COUNT(*) FROM leads WHERE status = 'failed') as leads_fallidos,
    (SELECT COUNT(*) FROM leads WHERE email IS NOT NULL) as leads_con_email,
    (SELECT COUNT(*) FROM domain_search_tracking) as combinaciones_tracking,
    (SELECT COUNT(*) FROM domain_search_tracking WHERE is_exhausted = false) as combinaciones_activas;

-- -----------------------------------------------------------------------------
-- 8. VERIFICAR SI HAY DOMINIOS AGREGADOS RECIENTEMENTE (últimas 24hs)
-- -----------------------------------------------------------------------------
SELECT 
    '⏰ DOMINIOS AGREGADOS EN ÚLTIMAS 24 HORAS' as seccion,
    user_id,
    COUNT(*) as dominios_agregados,
    MIN(created_at) as primero,
    MAX(created_at) as ultimo
FROM leads
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY user_id;

-- -----------------------------------------------------------------------------
-- 9. PRÓXIMAS COMBINACIONES A BUSCAR (si el bot está corriendo)
-- -----------------------------------------------------------------------------
SELECT 
    '🎯 PRÓXIMAS COMBINACIONES A BUSCAR' as seccion,
    user_id,
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at
FROM domain_search_tracking
WHERE is_exhausted = false
ORDER BY user_id, current_page ASC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- 10. VERIFICAR TABLAS CRÍTICAS
-- -----------------------------------------------------------------------------
SELECT 
    '🔍 VERIFICACIÓN DE TABLAS' as seccion,
    'hunter_configs' as tabla,
    COUNT(*) as filas
FROM hunter_configs
UNION ALL
SELECT 
    '🔍 VERIFICACIÓN DE TABLAS',
    'leads',
    COUNT(*)
FROM leads
UNION ALL
SELECT 
    '🔍 VERIFICACIÓN DE TABLAS',
    'domain_search_tracking',
    COUNT(*)
FROM domain_search_tracking
UNION ALL
SELECT 
    '🔍 VERIFICACIÓN DE TABLAS',
    'hunter_logs',
    COUNT(*)
FROM hunter_logs;

-- =============================================================================
-- COMANDOS ÚTILES PARA ACTIVAR EL BOT
-- =============================================================================

-- Si el bot NO está activo, ejecutar esto (reemplazar USER_ID con tu ID):
-- UPDATE hunter_configs 
-- SET bot_enabled = true, 
--     nicho = 'inmobiliarias',
--     ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza'],
--     pais = 'Argentina'
-- WHERE user_id = 'TU_USER_ID_AQUI';

-- Para resetear el tracking (si todo está exhausted):
-- UPDATE domain_search_tracking 
-- SET is_exhausted = false, current_page = 0 
-- WHERE user_id = 'TU_USER_ID_AQUI';

-- Para ver solo tus datos (reemplazar USER_ID):
-- SELECT * FROM hunter_configs WHERE user_id = 'TU_USER_ID_AQUI';
-- SELECT * FROM leads WHERE user_id = 'TU_USER_ID_AQUI' ORDER BY created_at DESC LIMIT 50;
-- SELECT * FROM domain_search_tracking WHERE user_id = 'TU_USER_ID_AQUI';
-- SELECT * FROM hunter_logs WHERE user_id = 'TU_USER_ID_AQUI' ORDER BY created_at DESC LIMIT 100;

-- =============================================================================
-- FIN DEL DIAGNÓSTICO
-- =============================================================================

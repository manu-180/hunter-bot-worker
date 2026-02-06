-- =============================================================================
-- SOLUCIONES RÁPIDAS - BOT NO RECOPILA DOMINIOS
-- =============================================================================
-- Este archivo contiene los comandos SQL para solucionar los problemas más comunes

-- =============================================================================
-- PROBLEMA 1: Bot no está habilitado para tu usuario
-- =============================================================================
-- SOLUCIÓN: Habilitar el bot
-- ⚠️  IMPORTANTE: Reemplaza 'TU_USER_ID_AQUI' con tu user_id real

UPDATE hunter_configs 
SET 
    bot_enabled = true,
    nicho = 'inmobiliarias',  -- Cambia esto al nicho que quieras
    ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'],
    pais = 'Argentina'
WHERE user_id = 'TU_USER_ID_AQUI';

-- Verificar que se aplicó:
SELECT user_id, bot_enabled, nicho, ciudades, pais 
FROM hunter_configs 
WHERE user_id = 'TU_USER_ID_AQUI';

-- =============================================================================
-- PROBLEMA 2: No existe registro en hunter_configs para tu usuario
-- =============================================================================
-- SOLUCIÓN: Crear el registro

INSERT INTO hunter_configs (
    user_id,
    bot_enabled,
    nicho,
    ciudades,
    pais,
    resend_api_key,
    from_email,
    from_name,
    email_subject,
    is_active
) VALUES (
    'TU_USER_ID_AQUI',  -- ⚠️  Reemplazar con tu user_id
    true,                -- Bot habilitado
    'inmobiliarias',     -- Nicho a buscar
    ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza'],  -- Ciudades
    'Argentina',         -- País
    'TU_RESEND_API_KEY', -- ⚠️  Opcional: tu Resend API key
    'tu@email.com',      -- ⚠️  Opcional: tu email de envío
    'Tu Nombre',         -- Tu nombre
    'Potenciemos tu negocio juntos',
    true                 -- Configuración activa
)
ON CONFLICT (user_id) DO UPDATE SET
    bot_enabled = true,
    nicho = 'inmobiliarias',
    ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza'],
    pais = 'Argentina';

-- =============================================================================
-- PROBLEMA 3: Todas las combinaciones están agotadas (is_exhausted = true)
-- =============================================================================
-- SOLUCIÓN: Resetear el tracking para que vuelva a buscar

-- Opción A: Resetear solo tu usuario
UPDATE domain_search_tracking 
SET 
    is_exhausted = false,
    current_page = 0,
    updated_at = NOW()
WHERE user_id = 'TU_USER_ID_AQUI';

-- Opción B: Eliminar todo el tracking (el bot creará nuevas combinaciones)
DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID_AQUI';

-- Verificar:
SELECT * FROM domain_search_tracking WHERE user_id = 'TU_USER_ID_AQUI';

-- =============================================================================
-- PROBLEMA 4: Ver qué está pasando con el bot en tiempo real
-- =============================================================================
-- Consultar los logs más recientes

SELECT 
    created_at,
    level,
    action,
    domain,
    message
FROM hunter_logs
WHERE user_id = 'TU_USER_ID_AQUI'
ORDER BY created_at DESC
LIMIT 50;

-- =============================================================================
-- PROBLEMA 5: Ver si el bot está agregando dominios
-- =============================================================================
-- Ver los últimos dominios agregados

SELECT 
    domain,
    status,
    email,
    created_at,
    updated_at
FROM leads
WHERE user_id = 'TU_USER_ID_AQUI'
ORDER BY created_at DESC
LIMIT 100;

-- Ver cuántos dominios hay por status
SELECT 
    status,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = 'TU_USER_ID_AQUI'
GROUP BY status
ORDER BY status;

-- =============================================================================
-- PROBLEMA 6: El bot está buscando pero no encuentra dominios
-- =============================================================================
-- Esto puede ser porque:
-- 1. El nicho está muy saturado
-- 2. Las ciudades ya no tienen más resultados
-- 3. SerpAPI está bloqueado o sin créditos

-- SOLUCIÓN: Cambiar a otro nicho o país

UPDATE hunter_configs 
SET 
    nicho = 'agencias de marketing',  -- Cambiar nicho
    pais = 'México',                  -- Cambiar país
    ciudades = ARRAY['Ciudad de México', 'Guadalajara', 'Monterrey']
WHERE user_id = 'TU_USER_ID_AQUI';

-- Y resetear el tracking
DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID_AQUI';

-- =============================================================================
-- ÚTILES: Ver tu configuración completa
-- =============================================================================

-- Ver tu config actual
SELECT 
    user_id,
    bot_enabled,
    nicho,
    ciudades,
    pais,
    resend_api_key IS NOT NULL as tiene_resend,
    from_email,
    from_name,
    is_active,
    created_at,
    updated_at
FROM hunter_configs
WHERE user_id = 'TU_USER_ID_AQUI';

-- Ver cuántas combinaciones tiene el bot para buscar
SELECT 
    COUNT(*) as total_combinaciones,
    COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas,
    SUM(total_domains_found) as dominios_encontrados
FROM domain_search_tracking
WHERE user_id = 'TU_USER_ID_AQUI';

-- Ver las próximas 10 combinaciones que el bot va a buscar
SELECT 
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at
FROM domain_search_tracking
WHERE user_id = 'TU_USER_ID_AQUI'
  AND is_exhausted = false
ORDER BY current_page ASC
LIMIT 10;

-- =============================================================================
-- COMANDOS DE MANTENIMIENTO
-- =============================================================================

-- Limpiar logs viejos (más de 7 días)
DELETE FROM hunter_logs 
WHERE user_id = 'TU_USER_ID_AQUI' 
  AND created_at < NOW() - INTERVAL '7 days';

-- Limpiar leads fallidos antiguos (más de 30 días)
DELETE FROM leads 
WHERE user_id = 'TU_USER_ID_AQUI' 
  AND status = 'failed' 
  AND created_at < NOW() - INTERVAL '30 days';

-- Re-intentar leads que fallaron (cambiarlos a pending otra vez)
UPDATE leads 
SET status = 'pending', error_message = NULL, updated_at = NOW()
WHERE user_id = 'TU_USER_ID_AQUI' 
  AND status = 'failed';

-- =============================================================================
-- VERIFICACIÓN FINAL: ¿El bot debería estar funcionando?
-- =============================================================================
-- Ejecuta esto para ver un resumen completo de tu configuración

SELECT 
    '✅ Bot habilitado' as check,
    bot_enabled::text as valor
FROM hunter_configs WHERE user_id = 'TU_USER_ID_AQUI'
UNION ALL
SELECT 
    '📊 Combinaciones activas',
    COUNT(*)::text
FROM domain_search_tracking 
WHERE user_id = 'TU_USER_ID_AQUI' AND is_exhausted = false
UNION ALL
SELECT 
    '📦 Dominios PENDING',
    COUNT(*)::text
FROM leads 
WHERE user_id = 'TU_USER_ID_AQUI' AND status = 'pending'
UNION ALL
SELECT 
    '📧 Emails encontrados',
    COUNT(*)::text
FROM leads 
WHERE user_id = 'TU_USER_ID_AQUI' AND email IS NOT NULL
UNION ALL
SELECT 
    '🚀 Emails enviados',
    COUNT(*)::text
FROM leads 
WHERE user_id = 'TU_USER_ID_AQUI' AND status = 'sent'
UNION ALL
SELECT 
    '⏰ Último lead agregado',
    TO_CHAR(MAX(created_at), 'YYYY-MM-DD HH24:MI:SS')
FROM leads 
WHERE user_id = 'TU_USER_ID_AQUI';

-- =============================================================================
-- ¿CÓMO OBTENER TU USER_ID?
-- =============================================================================
-- Si no sabes tu user_id, ejecuta esto:

SELECT 
    id as user_id,
    email,
    created_at
FROM auth.users
ORDER BY created_at DESC;

-- Tu user_id es el campo 'id' de tu usuario

-- =============================================================================
-- FIN
-- =============================================================================

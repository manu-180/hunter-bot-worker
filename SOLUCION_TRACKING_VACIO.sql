-- ============================================================================
-- SOLUCIÓN: Domain Hunter Worker NO está recopilando dominios
-- ============================================================================
-- User ID: 38152119-7da4-442e-9826-20901c65f42e
-- Problema: domain_search_tracking está VACÍO (0 filas)
-- Solución: Crear combinaciones iniciales para que el bot pueda buscar
-- ============================================================================

-- ============================================================================
-- PASO 1: Verificar el estado actual
-- ============================================================================

-- ¿Cuántas combinaciones hay actualmente?
SELECT COUNT(*) as total_tracking 
FROM domain_search_tracking 
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';
-- Resultado esperado: 0 (esto confirma el problema)

-- ============================================================================
-- PASO 2: Crear combinaciones iniciales de búsqueda
-- ============================================================================

-- Crear 30 combinaciones para el sistema de rotación
-- (Inmobiliarias en 3 ciudades x 10 variaciones)

INSERT INTO domain_search_tracking (
    user_id,
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at,
    created_at,
    updated_at
) VALUES
-- Buenos Aires - Inmobiliarias
('38152119-7da4-442e-9826-20901c65f42e', 'inmobiliarias', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios contables', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de marketing', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios juridicos', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'consultoras', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de diseño', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios de arquitectura', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'desarrolladores web', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'gimnasios', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'restaurantes', 'Buenos Aires', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),

-- Córdoba
('38152119-7da4-442e-9826-20901c65f42e', 'inmobiliarias', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios contables', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de marketing', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios juridicos', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'consultoras', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de diseño', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios de arquitectura', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'desarrolladores web', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'gimnasios', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'restaurantes', 'Córdoba', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),

-- Rosario
('38152119-7da4-442e-9826-20901c65f42e', 'inmobiliarias', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios contables', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de marketing', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios juridicos', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'consultoras', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'agencias de diseño', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'estudios de arquitectura', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'desarrolladores web', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'gimnasios', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW()),
('38152119-7da4-442e-9826-20901c65f42e', 'restaurantes', 'Rosario', 'Argentina', 0, 0, false, NOW(), NOW(), NOW())

ON CONFLICT (user_id, nicho, ciudad, pais) DO NOTHING;

-- ============================================================================
-- PASO 3: Verificar que se crearon las combinaciones
-- ============================================================================

SELECT 
    nicho,
    ciudad,
    current_page,
    is_exhausted,
    created_at
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY ciudad, nicho;

-- Resultado esperado: 30 filas con diferentes combinaciones

-- ============================================================================
-- PASO 4: Ver resumen de combinaciones creadas
-- ============================================================================

SELECT 
    COUNT(*) as total_combinaciones,
    COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Resultado esperado:
-- total_combinaciones: 30
-- activas: 30
-- agotadas: 0

-- ============================================================================
-- PASO 5: Ver las próximas 5 combinaciones que el bot va a buscar
-- ============================================================================

SELECT 
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND is_exhausted = false
ORDER BY current_page ASC, created_at ASC
LIMIT 5;

-- Esto muestra las próximas 5 búsquedas que el bot va a hacer

-- ============================================================================
-- PASO 6 (OPCIONAL): Limpiar leads viejos que son basura
-- ============================================================================

-- Ver dominios que claramente NO son del nicho
SELECT domain, status 
FROM leads 
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    domain LIKE '%google%' OR
    domain LIKE '%facebook%' OR
    domain LIKE '%booking.com%' OR
    domain LIKE '%yelp.com%' OR
    domain LIKE '%gob.ar%' OR
    domain LIKE '%gov.ar%' OR
    domain LIKE '/maps/%' OR
    domain LIKE '%clarin.com%' OR
    domain LIKE '%lavoz.com.ar%'
  )
ORDER BY created_at DESC;

-- Si hay muchos, puedes eliminarlos (OPCIONAL):
-- DELETE FROM leads 
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
--   AND (
--     domain LIKE '%google%' OR
--     domain LIKE '%facebook%' OR
--     domain LIKE '%booking.com%' OR
--     domain LIKE '%yelp.com%' OR
--     domain LIKE '%gob.ar%' OR
--     domain LIKE '%gov.ar%' OR
--     domain LIKE '/maps/%' OR
--     domain LIKE '%clarin.com%' OR
--     domain LIKE '%lavoz.com.ar%'
--   );

-- ============================================================================
-- PASO 7: Monitorear en tiempo real
-- ============================================================================

-- Ver si el bot está agregando dominios NUEVOS (ejecutar cada 2 minutos)
SELECT 
    domain,
    status,
    created_at
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY created_at DESC
LIMIT 10;

-- Ver logs recientes del Domain Hunter
SELECT 
    created_at,
    level,
    action,
    message
FROM hunter_logs
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND action = 'domain_added'
ORDER BY created_at DESC
LIMIT 20;

-- Ver progreso del tracking
SELECT 
    nicho,
    ciudad,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY last_searched_at DESC NULLS LAST
LIMIT 10;

-- ============================================================================
-- PASO 8: Estadísticas actualizadas
-- ============================================================================

SELECT 
    status,
    COUNT(*) as cantidad,
    MIN(created_at) as primer_lead,
    MAX(created_at) as ultimo_lead
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
GROUP BY status
ORDER BY status;

-- ============================================================================
-- COMANDOS DE EMERGENCIA (solo si algo sale mal)
-- ============================================================================

-- Si las combinaciones se agotan todas, resetear:
-- UPDATE domain_search_tracking 
-- SET is_exhausted = false, current_page = 0, updated_at = NOW()
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Si quieres eliminar todo el tracking y empezar de cero:
-- DELETE FROM domain_search_tracking 
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';
-- (Luego volver a ejecutar el PASO 2)

-- Ver configuración del bot:
-- SELECT * FROM hunter_configs 
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- ============================================================================
-- FIN
-- ============================================================================

-- IMPORTANTE: Después de ejecutar estos comandos:
-- 1. Reiniciar el domain_hunter_worker.py
-- 2. Verificar en la terminal que diga "SerpAPI configurada"
-- 3. Verificar que diga "1 usuario(s) con bot activo"
-- 4. Esperar 2-3 minutos
-- 5. Ejecutar las queries de monitoreo (PASO 7)
-- 6. Deberías ver dominios NUEVOS siendo agregados

-- Si después de esto SIGUE sin funcionar:
-- - Verificar SERPAPI_KEY en el archivo .env
-- - Verificar créditos de SerpAPI en https://serpapi.com/dashboard
-- - Revisar logs del worker en la terminal

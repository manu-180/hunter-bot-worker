-- ============================================================================
-- LIMPIAR DOMINIOS NO DESEADOS (Basura) DE LA BASE DE DATOS
-- ============================================================================
-- User ID: 38152119-7da4-442e-9826-20901c65f42e
-- 
-- Este script elimina dominios que NO son negocios reales:
-- - Páginas del gobierno (.gob.ar, .gov.ar)
-- - Portales genéricos (booking.com, yelp.com, clarin.com)
-- - Links de Google Maps
-- - Sitios de ejemplo
-- ============================================================================

-- ============================================================================
-- PASO 1: Ver cuántos dominios basura tienes (NO ELIMINA, SOLO MUESTRA)
-- ============================================================================

SELECT 
    'DOMINIOS DE GOBIERNO' as tipo,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    domain LIKE '%.gob.ar%' OR 
    domain LIKE '%.gov.ar%' OR
    domain LIKE '%gobierno%' OR
    domain LIKE '%municipalidad%' OR
    domain LIKE '%provincia.%'
  )

UNION ALL

SELECT 
    'PORTALES GENERICOS',
    COUNT(*)
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    domain LIKE '%booking.com%' OR
    domain LIKE '%yelp.com%' OR
    domain LIKE '%clarin.com%' OR
    domain LIKE '%lavoz.com.ar%' OR
    domain LIKE '%lanacion.%' OR
    domain LIKE '%mercadolibre%' OR
    domain LIKE '%despegar%' OR
    domain LIKE '%tripadvisor%'
  )

UNION ALL

SELECT 
    'LINKS DE GOOGLE MAPS',
    COUNT(*)
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND domain LIKE '/maps/%'

UNION ALL

SELECT 
    'BANCOS Y SERVICIOS',
    COUNT(*)
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    domain LIKE '%banco%' OR
    domain LIKE '%santander%' OR
    domain LIKE '%galicia%' OR
    domain LIKE '%provincia.com%'
  )

UNION ALL

SELECT 
    'PORTALES INMOBILIARIOS',
    COUNT(*)
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    domain LIKE '%zonaprop%' OR
    domain LIKE '%argenprop%' OR
    domain LIKE '%properati%' OR
    domain LIKE '%mercadolibre%'
  )

UNION ALL

SELECT 
    'TOTAL DE BASURA',
    COUNT(*)
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    -- Gobierno
    domain LIKE '%.gob.ar%' OR domain LIKE '%.gov.ar%' OR
    domain LIKE '%gobierno%' OR domain LIKE '%municipalidad%' OR
    domain LIKE '%provincia.%' OR domain LIKE '%afip%' OR
    domain LIKE '%anses%' OR domain LIKE '%arba%' OR
    
    -- Portales genéricos
    domain LIKE '%booking.com%' OR domain LIKE '%yelp.com%' OR
    domain LIKE '%clarin.com%' OR domain LIKE '%lavoz.com.ar%' OR
    domain LIKE '%lanacion.%' OR domain LIKE '%infobae%' OR
    domain LIKE '%despegar%' OR domain LIKE '%tripadvisor%' OR
    
    -- Google Maps
    domain LIKE '/maps/%' OR domain LIKE '%maps.google%' OR
    
    -- Bancos
    domain LIKE '%banco%' OR domain LIKE '%santander%' OR
    domain LIKE '%galicia%' OR domain LIKE '%provincia.com%' OR
    domain LIKE '%hsbc%' OR domain LIKE '%bbva%' OR
    
    -- Portales inmobiliarios
    domain LIKE '%zonaprop%' OR domain LIKE '%argenprop%' OR
    domain LIKE '%properati%' OR domain LIKE '%mercadolibre%' OR
    domain LIKE '%trovit%' OR
    
    -- Redes sociales
    domain LIKE '%facebook%' OR domain LIKE '%instagram%' OR
    domain LIKE '%twitter%' OR domain LIKE '%linkedin%' OR
    domain LIKE '%youtube%' OR
    
    -- Portales de noticias
    domain LIKE '%perfil.com%' OR domain LIKE '%pagina12%' OR
    domain LIKE '%ambito.com%' OR domain LIKE '%cronista%' OR
    
    -- Educación
    domain LIKE '%.edu.ar%' OR domain LIKE '%universidad%' OR
    domain LIKE '%educacion%'
  );

-- ============================================================================
-- PASO 2: Ver los dominios específicos antes de eliminar
-- ============================================================================

SELECT 
    domain,
    status,
    email,
    created_at
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    -- Gobierno
    domain LIKE '%.gob.ar%' OR domain LIKE '%.gov.ar%' OR
    domain LIKE '%gobierno%' OR domain LIKE '/maps/%' OR
    -- Portales
    domain LIKE '%booking.com%' OR domain LIKE '%yelp%' OR
    domain LIKE '%clarin%' OR domain LIKE '%banco%' OR
    domain LIKE '%provincia.com%'
  )
ORDER BY created_at DESC
LIMIT 50;

-- ============================================================================
-- PASO 3: ELIMINAR dominios basura (EJECUTAR CON CUIDADO)
-- ============================================================================

-- ⚠️  ADVERTENCIA: Este comando ELIMINA dominios permanentemente.
-- Solo ejecutar si estás seguro después de revisar el PASO 1 y 2.

-- Descomentar las siguientes líneas para eliminar:

/*
DELETE FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND (
    -- Gobierno
    domain LIKE '%.gob.ar%' OR domain LIKE '%.gov.ar%' OR
    domain LIKE '%gobierno%' OR domain LIKE '%municipalidad%' OR
    domain LIKE '%provincia.%' OR domain LIKE '%afip%' OR
    domain LIKE '%anses%' OR domain LIKE '%arba%' OR
    
    -- Portales genéricos
    domain LIKE '%booking.com%' OR domain LIKE '%yelp.com%' OR
    domain LIKE '%clarin.com%' OR domain LIKE '%lavoz.com.ar%' OR
    domain LIKE '%lanacion.%' OR domain LIKE '%infobae%' OR
    domain LIKE '%despegar%' OR domain LIKE '%tripadvisor%' OR
    domain LIKE '%almundo%' OR domain LIKE '%expedia%' OR
    
    -- Google Maps y rutas
    domain LIKE '/maps/%' OR domain LIKE '%maps.google%' OR
    domain LIKE '%google.com%' OR
    
    -- Bancos
    domain LIKE '%banco%' OR domain LIKE '%santander%' OR
    domain LIKE '%galicia%' OR domain LIKE '%provincia.com%' OR
    domain LIKE '%hsbc%' OR domain LIKE '%bbva%' OR
    domain LIKE '%icbc%' OR domain LIKE '%frances%' OR
    
    -- Portales inmobiliarios (queremos inmobiliarias directas, no portales)
    domain LIKE '%zonaprop%' OR domain LIKE '%argenprop%' OR
    domain LIKE '%properati%' OR domain LIKE '%mercadolibre%' OR
    domain LIKE '%trovit%' OR domain LIKE '%lamudi%' OR
    domain LIKE '%inmuebles24%' OR
    
    -- Redes sociales
    domain LIKE '%facebook%' OR domain LIKE '%instagram%' OR
    domain LIKE '%twitter%' OR domain LIKE '%linkedin%' OR
    domain LIKE '%youtube%' OR domain LIKE '%tiktok%' OR
    
    -- Portales de noticias
    domain LIKE '%perfil.com%' OR domain LIKE '%pagina12%' OR
    domain LIKE '%ambito.com%' OR domain LIKE '%cronista%' OR
    domain LIKE '%telam%' OR
    
    -- Educación
    domain LIKE '%.edu.ar%' OR domain LIKE '%universidad%' OR
    domain LIKE '%educacion%' OR domain LIKE '%campus%' OR
    
    -- Portales de empleo
    domain LIKE '%zonajobs%' OR domain LIKE '%computrabajo%' OR
    domain LIKE '%bumeran%' OR domain LIKE '%indeed%' OR
    
    -- Wikipedia y similares
    domain LIKE '%wikipedia%' OR domain LIKE '%wikidata%' OR
    
    -- Sitios de ejemplo
    domain LIKE '%ejemplo%' OR domain LIKE '%example%' OR
    domain LIKE '%test%' OR domain LIKE '%demo%'
  );
*/

-- ============================================================================
-- PASO 4: Verificar cuántos dominios quedaron después de la limpieza
-- ============================================================================

SELECT 
    'TOTAL ANTES DE LIMPIEZA' as info,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Ejecutar después de eliminar para ver cuántos quedaron

-- ============================================================================
-- PASO 5: Ver estadísticas de los dominios que quedaron
-- ============================================================================

SELECT 
    status,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
GROUP BY status
ORDER BY status;

-- ============================================================================
-- QUERIES ÚTILES ADICIONALES
-- ============================================================================

-- Ver solo dominios válidos (buenos)
SELECT domain, status, email
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND domain NOT LIKE '%.gob.ar%'
  AND domain NOT LIKE '%.gov.ar%'
  AND domain NOT LIKE '/maps/%'
  AND domain NOT LIKE '%google%'
  AND domain NOT LIKE '%banco%'
ORDER BY created_at DESC
LIMIT 50;

-- Contar dominios buenos vs basura
SELECT 
    CASE 
        WHEN domain LIKE '%.gob.ar%' OR domain LIKE '%.gov.ar%' OR domain LIKE '/maps/%' THEN 'BASURA'
        ELSE 'BUENO'
    END as tipo,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
GROUP BY tipo;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================

-- RESUMEN DE USO:
-- 1. Ejecutar PASO 1 para ver cuántos dominios basura tienes
-- 2. Ejecutar PASO 2 para ver los dominios específicos
-- 3. Si estás conforme, descomentar y ejecutar PASO 3 para eliminar
-- 4. Ejecutar PASO 4 y 5 para verificar el resultado

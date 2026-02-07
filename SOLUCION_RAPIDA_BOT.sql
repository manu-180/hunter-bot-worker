-- =============================================================================
-- 🔧 SOLUCIÓN RÁPIDA - Bot no está recopilando dominios
-- =============================================================================
-- Ejecuta este archivo COMPLETO en el SQL Editor de Supabase
-- Esto diagnosticará y solucionará el problema automáticamente
-- =============================================================================

-- =============================================================================
-- PASO 1: Verificar que las columnas necesarias existan
-- =============================================================================
-- Si no existen, se crean automáticamente

DO $$ 
BEGIN
    -- Crear bot_enabled si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'bot_enabled'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN bot_enabled BOOLEAN DEFAULT false;
        RAISE NOTICE '✅ Columna bot_enabled creada';
    ELSE
        RAISE NOTICE '✓ Columna bot_enabled ya existe';
    END IF;
    
    -- Crear nicho si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'nicho'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN nicho TEXT DEFAULT 'inmobiliarias';
        RAISE NOTICE '✅ Columna nicho creada';
    ELSE
        RAISE NOTICE '✓ Columna nicho ya existe';
    END IF;
    
    -- Crear ciudades si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'ciudades'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN ciudades TEXT[] DEFAULT ARRAY['Buenos Aires', 'Córdoba', 'Rosario'];
        RAISE NOTICE '✅ Columna ciudades creada';
    ELSE
        RAISE NOTICE '✓ Columna ciudades ya existe';
    END IF;
    
    -- Crear pais si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'pais'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN pais TEXT DEFAULT 'Argentina';
        RAISE NOTICE '✅ Columna pais creada';
    ELSE
        RAISE NOTICE '✓ Columna pais ya existe';
    END IF;
END $$;

-- Crear índice para performance
CREATE INDEX IF NOT EXISTS idx_hunter_configs_bot_enabled 
    ON hunter_configs(bot_enabled) 
    WHERE bot_enabled = true;

-- =============================================================================
-- PASO 2: DIAGNÓSTICO - Ver el estado actual
-- =============================================================================

-- Ver todos los usuarios
SELECT 
    '👥 USUARIOS REGISTRADOS' as estado,
    id as user_id,
    email,
    created_at
FROM auth.users
ORDER BY created_at DESC;

-- Ver configuraciones actuales
SELECT 
    '⚙️ CONFIGURACIONES ACTUALES' as estado,
    user_id,
    bot_enabled,
    nicho,
    pais,
    is_active,
    created_at
FROM hunter_configs
ORDER BY created_at DESC;

-- Ver cuántos usuarios tienen el bot activo
SELECT 
    '📊 RESUMEN' as info,
    (SELECT COUNT(*) FROM hunter_configs WHERE bot_enabled = true) as "usuarios_con_bot_activo",
    (SELECT COUNT(*) FROM hunter_configs) as "total_usuarios_con_config",
    (SELECT COUNT(*) FROM auth.users) as "total_usuarios_registrados";

-- Ver leads recientes
SELECT 
    '📋 LEADS RECIENTES (últimos 10)' as info,
    user_id,
    domain,
    status,
    created_at
FROM leads
ORDER BY created_at DESC
LIMIT 10;

-- =============================================================================
-- PASO 3: SOLUCIÓN - Habilitar el bot
-- =============================================================================
-- ⚠️ IMPORTANTE: Necesitas reemplazar 'TU_USER_ID_AQUI' con tu user_id real
-- Para obtener tu user_id, mira los resultados de las queries de arriba
-- =============================================================================

-- Opción A: Si YA TIENES un registro en hunter_configs, solo actívalo
/*
UPDATE hunter_configs 
SET 
    bot_enabled = true,
    nicho = 'inmobiliarias',  -- Cambia esto al nicho que quieras
    ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'],
    pais = 'Argentina'
WHERE user_id = 'TU_USER_ID_AQUI';  -- ⚠️ REEMPLAZAR AQUÍ
*/

-- Opción B: Si NO TIENES registro en hunter_configs, créalo
/*
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
    'TU_USER_ID_AQUI',  -- ⚠️ REEMPLAZAR con tu user_id
    true,                -- Bot habilitado ✅
    'inmobiliarias',     -- Nicho a buscar
    ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'],  -- Ciudades
    'Argentina',         -- País
    'tu_resend_api_key', -- Tu Resend API key (opcional ahora)
    'tu@email.com',      -- Tu email (opcional ahora)
    'Tu Nombre',         -- Tu nombre
    'Potenciemos tu negocio juntos',  -- Asunto del email
    true                 -- Configuración activa
)
ON CONFLICT (user_id) DO UPDATE SET
    bot_enabled = true,
    nicho = 'inmobiliarias',
    ciudades = ARRAY['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'],
    pais = 'Argentina';
*/

-- =============================================================================
-- PASO 4: VERIFICACIÓN FINAL
-- =============================================================================
-- Después de ejecutar la solución, verifica que todo esté correcto

-- Ver el estado del bot
SELECT 
    '✅ VERIFICACIÓN FINAL' as check,
    user_id,
    bot_enabled as "bot_activo",
    nicho,
    ciudades,
    pais,
    is_active
FROM hunter_configs
WHERE bot_enabled = true;

-- Si ves tu usuario aquí con bot_enabled = true, ¡el bot debería empezar a funcionar!

-- =============================================================================
-- COMANDOS ADICIONALES ÚTILES
-- =============================================================================

-- Para ver los logs del bot en tiempo real:
/*
SELECT 
    created_at,
    level,
    action,
    domain,
    message
FROM hunter_logs
WHERE user_id = 'TU_USER_ID_AQUI'  -- ⚠️ REEMPLAZAR AQUÍ
ORDER BY created_at DESC
LIMIT 50;
*/

-- Para ver cuántos dominios se están agregando:
/*
SELECT 
    status,
    COUNT(*) as cantidad
FROM leads
WHERE user_id = 'TU_USER_ID_AQUI'  -- ⚠️ REEMPLAZAR AQUÍ
GROUP BY status
ORDER BY status;
*/

-- Para resetear el tracking si no encuentra más dominios:
/*
DELETE FROM domain_search_tracking 
WHERE user_id = 'TU_USER_ID_AQUI';  -- ⚠️ REEMPLAZAR AQUÍ
*/

-- =============================================================================
-- RESUMEN DE LA SOLUCIÓN
-- =============================================================================
/*
1. Ejecuta TODA esta query en Supabase SQL Editor
2. Mira los resultados del DIAGNÓSTICO para obtener tu user_id
3. Descomenta (quita el /* y */) la Opción A o B del PASO 3
4. Reemplaza 'TU_USER_ID_AQUI' con tu user_id real
5. Ejecuta la query de nuevo
6. Verifica en la VERIFICACIÓN FINAL que bot_enabled = true
7. ¡El bot debería empezar a recopilar dominios en pocos minutos!

Si el bot NO está corriendo (Railway/local), inícialo con:
  python start_workers.py
  
O solo el domain hunter:
  python domain_hunter_worker.py
*/

-- =============================================================================
-- FIN
-- =============================================================================

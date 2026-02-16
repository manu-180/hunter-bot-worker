-- =============================================================================
-- Actualizar dominio de email: assistify.lat -> getbotlode.com
-- =============================================================================
-- Ejecutar en Supabase SQL Editor después de verificar getbotlode.com en Resend.
-- Afecta la columna from_email en hunter_configs (remitente de los emails).
-- Dominio viejo assistify.lat no se usa; todos los envíos deben ser getbotlode.com.
-- =============================================================================

-- 1) Ver qué registros tienen el dominio viejo (solo revisión)
SELECT
    user_id,
    from_email,
    from_name,
    updated_at
FROM hunter_configs
WHERE from_email ILIKE '%asstistify.lat%'
   OR from_email ILIKE '%assistify.lat%';

-- 2) Actualizar: reemplazar assistify.lat por manuel@getbotlode.com
UPDATE hunter_configs
SET
    from_email = 'manuel@getbotlode.com',
    updated_at = NOW()
WHERE from_email ILIKE '%asstistify.lat%'
   OR from_email ILIKE '%assistify.lat%';

-- 3) Verificar resultado
SELECT
    user_id,
    from_email,
    from_name,
    updated_at
FROM hunter_configs
WHERE from_email ILIKE '%getbotlode.com%';

-- =============================================================================
-- Actualizar dominio de email: asstistify.lat -> botlode.com
-- =============================================================================
-- Ejecutar en Supabase SQL Editor después de verificar botlode.com en Resend.
-- Afecta la columna from_email en hunter_configs (remitente de los emails).
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

-- 2) Actualizar: reemplazar asstistify.lat / assistify.lat por botlode.com
UPDATE hunter_configs
SET
    from_email = REPLACE(REPLACE(LOWER(from_email), '@asstistify.lat', '@botlode.com'), '@assistify.lat', '@botlode.com'),
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
WHERE from_email ILIKE '%botlode.com%';

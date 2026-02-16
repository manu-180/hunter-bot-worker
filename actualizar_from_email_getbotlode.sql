-- =============================================================================
-- Usar FROM_EMAIL = manuel@getbotlode.com en hunter_configs
-- =============================================================================
-- La variable FROM_EMAIL de Railway solo se usa si hunter_configs.from_email
-- está vacío. Si en la BD tenés soporte@assistify.lat, esa gana. Ejecutá esto
-- en Supabase SQL Editor para que los envíos usen manuel@getbotlode.com.
-- =============================================================================

-- 1) Ver registros que hoy usan assistify
SELECT user_id, from_email, from_name
FROM hunter_configs
WHERE from_email ILIKE '%assistify.lat%' OR from_email ILIKE '%asstistify.lat%';

-- 2) Actualizar a manuel@getbotlode.com (mismo que tu variable en Railway)
UPDATE hunter_configs
SET
    from_email = 'manuel@getbotlode.com',
    updated_at = NOW()
WHERE from_email ILIKE '%assistify.lat%'
   OR from_email ILIKE '%asstistify.lat%';

-- 3) Verificar
SELECT user_id, from_email, from_name, updated_at
FROM hunter_configs;

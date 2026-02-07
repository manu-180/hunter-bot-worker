-- =============================================================================
-- REENVIAR EMAIL A manunv97@gmail.com
-- =============================================================================
-- El worker toma leads con status 'queued_for_send'. Este script pone de nuevo
-- en cola el lead para que te vuelva a mandar el mail en ~10-60 segundos.
-- Ejecutá esto en el SQL Editor de Supabase.
-- =============================================================================

-- Opción 1: Reencolar CUALQUIER lead tuyo que ya haya sido enviado a tu mail
-- (útil si no recordás el domain)
UPDATE leads
SET
    status = 'queued_for_send',
    error_message = NULL,
    sent_at = NULL,
    updated_at = NOW()
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND email = 'manunv97@gmail.com'
  AND status = 'sent';

-- Si no se actualizó ninguna fila, probá la Opción 2 por domain:

-- Opción 2: Reencolar por domain (elegí el que uses para prueba)
-- UPDATE leads
-- SET
--     status = 'queued_for_send',
--     error_message = NULL,
--     sent_at = NULL,
--     updated_at = NOW()
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
--   AND domain = 'test-verificacion-email-manunv.com';

-- UPDATE leads
-- SET
--     status = 'queued_for_send',
--     error_message = NULL,
--     sent_at = NULL,
--     updated_at = NOW()
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
--   AND domain = 'prueba-email-botlode.com';

-- Ver cuántos quedaron en cola (debería ser >= 1)
-- SELECT id, domain, email, status, updated_at FROM leads
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e' AND status = 'queued_for_send';

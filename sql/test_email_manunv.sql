-- =============================================================================
-- TEST: Ver el mail de Hunter Bot - Enviar de nuevo a manunv97@gmail.com
-- =============================================================================
-- El worker (main.py / Railway) toma leads con status 'queued_for_send' y les
-- manda el email. Ejecutá primero el BORRADO (opción A) y después el INSERT (B).
--
-- Reemplazá TU_USER_ID por tu user_id. Si no lo tenés:
--   SELECT id, email FROM auth.users WHERE email = 'manunv97@gmail.com';
-- =============================================================================

-- -----------------------------------------------------------------------------
-- A) BORRAR el lead de prueba (para empezar limpio y que no diga "ya enviado")
-- -----------------------------------------------------------------------------
DELETE FROM leads
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'   -- <-- Tu user_id
  AND domain = 'test-verificacion-email-manunv.com';


-- -----------------------------------------------------------------------------
-- B) INSERTAR de nuevo → el worker lo agarrará y te manda el mail en ~1 minuto
-- -----------------------------------------------------------------------------
INSERT INTO leads (user_id, domain, email, status, meta_title)
VALUES (
  '38152119-7da4-442e-9826-20901c65f42e',   -- <-- Tu user_id
  'test-verificacion-email-manunv.com',
  'manunv97@gmail.com',
  'queued_for_send',
  'Test de envío Hunter Bot'
)
ON CONFLICT (user_id, domain) DO UPDATE SET
  email = EXCLUDED.email,
  status = 'queued_for_send',
  error_message = NULL,
  updated_at = NOW();


-- =============================================================================
-- OPCIÓN RÁPIDA: Si ya tenés un lead enviado y querés que te lo reenvíe a vos
-- (solo cambiar email y poner status otra vez en cola)
-- =============================================================================
-- UPDATE leads
-- SET email = 'manunv97@gmail.com',
--     status = 'queued_for_send',
--     error_message = NULL,
--     updated_at = NOW()
-- WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
--   AND id = 'PONER_ACÁ_EL_ID_DEL_LEAD';

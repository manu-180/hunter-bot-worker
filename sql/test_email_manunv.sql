-- =============================================================================
-- TEST: Enviar un email de prueba a manunv97@gmail.com
-- =============================================================================
-- Este SQL inserta un lead en estado "queued_for_send". Cuando el worker
-- (python main.py) esté corriendo, lo tomará y enviará el email usando
-- tu configuración de Resend (from_email, from_name, plantilla, etc.).
--
-- IMPORTANTE: Reemplazá TU_USER_ID por tu user_id de Supabase.
-- Podés obtenerlo en Botslode (estando logueado) o con la query de abajo.
-- =============================================================================

-- Opción 1: Si sabés tu user_id (ej. 38152119-7da4-442e-9826-20901c65f42e)
INSERT INTO leads (user_id, domain, email, status, meta_title)
VALUES (
  '38152119-7da4-442e-9826-20901c65f42e',   -- <-- Reemplazá por tu user_id
  'test-verificacion-email-manunv.com',
  'manunv97@gmail.com',
  'queued_for_send',
  'Test de envío Hunter Bot'
)
ON CONFLICT (domain) DO UPDATE SET
  email = EXCLUDED.email,
  status = 'queued_for_send',
  error_message = NULL,
  updated_at = NOW();

-- =============================================================================
-- Cómo obtener tu user_id (ejecutá en SQL Editor si no lo tenés):
-- =============================================================================
-- SELECT id, email FROM auth.users WHERE email = 'manunv97@gmail.com';
-- Copiá el "id" y usalo en la query de arriba.
-- =============================================================================

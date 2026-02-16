-- =============================================================================
-- Reencolar leads warm-up por email para volver a enviarles
-- =============================================================================
-- Ejecutar en Supabase SQL Editor.
-- Pone status = queued_for_send y sent_at = NULL para que el worker los vuelva
-- a enviar. Solo afecta leads con dominio warmup-* (warm-up).
-- Así el límite de warm-up deja de bloquear (esos 9 ya no cuentan como "sent").
-- =============================================================================

-- 1) Ver cuáles coinciden (solo revisión)
SELECT id, email, domain, status, sent_at, updated_at
FROM leads
WHERE domain LIKE 'warmup-%'
  AND status = 'sent'
  AND email IN (
    'manunv97@gmail.com',
    'manumanu97@hotmail.com',
    'ivannarisaro@hotmail.com',
    'geimul@gmail.com',
    'geimul@hotmail.com',
    'reycamila04@gmail.com',
    'agustin.leonetti@outlook.com',
    'leonettichaka@gmail.com',
    'julinv3d@gmail.com'
  )
ORDER BY email;

-- 2) Reencolar: poner en cola para que se les reenvíe
UPDATE leads
SET
  status = 'queued_for_send',
  sent_at = NULL,
  updated_at = NOW(),
  error_message = NULL
WHERE domain LIKE 'warmup-%'
  AND status = 'sent'
  AND email IN (
    'manunv97@gmail.com',
    'manumanu97@hotmail.com',
    'ivannarisaro@hotmail.com',
    'geimul@gmail.com',
    'geimul@hotmail.com',
    'reycamila04@gmail.com',
    'agustin.leonetti@outlook.com',
    'leonettichaka@gmail.com',
    'julinv3d@gmail.com'
  );

-- 3) Ver cuántos quedaron reencolados (debería ser 9 o menos si alguno no existía)
-- Ejecutar después del UPDATE para verificar:
-- SELECT COUNT(*) FROM leads WHERE status = 'queued_for_send' AND domain LIKE 'warmup-%';

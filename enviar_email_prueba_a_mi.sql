-- Próxima vez: ejecutar esto y en 10-60 seg te llega el mail a manunv97@gmail.com
UPDATE leads
SET 
    status = 'queued_for_send',
    error_message = NULL,
    updated_at = NOW()
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND domain = 'prueba-email-botlode.com';
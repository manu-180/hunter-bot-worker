-- =============================================================================
-- ACTUALIZAR DEFAULT de email_subject en hunter_configs
-- =============================================================================
-- El código Python (mailer.py) no lee este campo, pero es mejor que el default
-- en la base esté consistente con el código.
-- =============================================================================

ALTER TABLE hunter_configs 
ALTER COLUMN email_subject 
SET DEFAULT 'Tu web está perdiendo clientes - Elevá su nivel ahora';

-- Opcional: actualizar registros existentes que tengan el subject viejo
-- (no afecta el funcionamiento actual porque mailer.py no lee este campo)
UPDATE hunter_configs
SET email_subject = 'Tu web está perdiendo clientes - Elevá su nivel ahora'
WHERE email_subject = 'Potenciemos tu negocio juntos';

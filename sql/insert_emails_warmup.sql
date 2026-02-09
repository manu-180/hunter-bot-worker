-- =============================================================================
-- PRIMEROS 9 EMAILS PARA WARM-UP (ganar confianza con Gmail/Outlook)
-- =============================================================================
-- Estos correos se enviarán ANTES que cualquier lead scraped (scraped_at antigua).
-- El worker ordena por scraped_at ASC, así que salen primero.
--
-- Reemplazá el user_id si usás otro (el de abajo es el de manunv).
-- Para ver el tuyo: SELECT user_id FROM hunter_configs WHERE bot_enabled = true;
-- =============================================================================

INSERT INTO leads (user_id, domain, email, status, meta_title, scraped_at, created_at, updated_at)
VALUES
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-1.getbotlode.com', 'manunv97@gmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:00+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-2.getbotlode.com', 'manumanu97@hotmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:01+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-3.getbotlode.com', 'ivannarisaro@hotmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:02+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-4.getbotlode.com', 'geimul@gmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:03+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-5.getbotlode.com', 'geimul@hotmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:04+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-6.getbotlode.com', 'reycamila04@gmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:05+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-7.getbotlode.com', 'agustin.leonetti@outlook.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:06+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-8.getbotlode.com', 'leonettichaka@gmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:07+00', NOW(), NOW()),
  ('38152119-7da4-442e-9826-20901c65f42e', 'warmup-9.getbotlode.com', 'julinv3d@gmail.com', 'queued_for_send', 'Warm-up', '2020-01-01 00:00:08+00', NOW(), NOW())
ON CONFLICT (user_id, domain) DO UPDATE SET
  email = EXCLUDED.email,
  status = 'queued_for_send',
  meta_title = EXCLUDED.meta_title,
  scraped_at = EXCLUDED.scraped_at,
  error_message = NULL,
  updated_at = NOW();

-- ============================================================
-- Migration: Hunter Bot — WPP follow-up stats + allow new log action
-- ============================================================
-- 1. Allow action 'wpp_followup_sent' in hunter_logs (para logs del follow-up WPP).
-- 2. Extender get_hunter_stats con: sent_today, wpp_sent_today, wpp_sent_total.
--
-- Ejecutar en Supabase SQL Editor una sola vez.
-- ============================================================

-- 1. Permitir la nueva acción en hunter_logs
ALTER TABLE hunter_logs
  DROP CONSTRAINT IF EXISTS hunter_logs_action_check;

ALTER TABLE hunter_logs
  ADD CONSTRAINT hunter_logs_action_check CHECK (action IN (
    'scrape_start', 'scrape_end',
    'email_found', 'email_not_found',
    'send_start', 'send_success', 'send_failed',
    'config_missing', 'domain_added', 'system_info',
    'wpp_followup_sent'
  ));

-- 2. Función de estadísticas extendida (emails enviados hoy + WPP follow-up hoy/total)
CREATE OR REPLACE FUNCTION get_hunter_stats(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
    v_sent_today BIGINT;
    v_wpp_sent_today BIGINT;
    v_wpp_sent_total BIGINT;
BEGIN
    -- Emails enviados hoy (por sent_at en leads)
    SELECT COUNT(*) INTO v_sent_today
    FROM leads
    WHERE user_id = p_user_id
      AND status = 'sent'
      AND sent_at IS NOT NULL
      AND (sent_at AT TIME ZONE 'UTC')::date = (NOW() AT TIME ZONE 'UTC')::date;

    -- WPP follow-up: hoy y total (desde hunter_logs)
    SELECT
        COUNT(*) FILTER (WHERE (created_at AT TIME ZONE 'UTC')::date = (NOW() AT TIME ZONE 'UTC')::date),
        COUNT(*)
    INTO v_wpp_sent_today, v_wpp_sent_total
    FROM hunter_logs
    WHERE user_id = p_user_id
      AND action = 'wpp_followup_sent';

    SELECT json_build_object(
        'total', COUNT(*),
        'pending', COUNT(*) FILTER (WHERE status = 'pending'),
        'scraping', COUNT(*) FILTER (WHERE status = 'scraping'),
        'scraped', COUNT(*) FILTER (WHERE status = 'scraped'),
        'queued_for_send', COUNT(*) FILTER (WHERE status = 'queued_for_send'),
        'sending', COUNT(*) FILTER (WHERE status = 'sending'),
        'sent', COUNT(*) FILTER (WHERE status = 'sent'),
        'failed', COUNT(*) FILTER (WHERE status = 'failed'),
        'emails_found', COUNT(*) FILTER (WHERE email IS NOT NULL),
        'sent_today', COALESCE(v_sent_today, 0),
        'wpp_sent_today', COALESCE(v_wpp_sent_today, 0),
        'wpp_sent_total', COALESCE(v_wpp_sent_total, 0)
    ) INTO result
    FROM leads
    WHERE user_id = p_user_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_hunter_stats(UUID) TO authenticated;

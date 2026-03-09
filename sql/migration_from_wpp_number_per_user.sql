-- ═══════════════════════════════════════════════════════════════════════════
-- Hunter Bot: número de WhatsApp de seguimiento por usuario
-- Ejecutar en Supabase SQL Editor (mismo proyecto que usa el Hunter Bot).
-- Así cada usuario puede tener su propio número (ej. Metalwailers con su SIM).
-- ═══════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'hunter_configs' AND column_name = 'from_wpp_number'
  ) THEN
    ALTER TABLE hunter_configs
      ADD COLUMN from_wpp_number TEXT;
    COMMENT ON COLUMN hunter_configs.from_wpp_number IS
      'Número desde el que se envía el WhatsApp de seguimiento (ej. whatsapp:+5491125330794). Si NULL, el worker usa HUNTER_FROM_WPP_NUMBER del entorno.';
  END IF;
END $$;

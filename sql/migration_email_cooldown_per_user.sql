-- ═══════════════════════════════════════════════════════════════════════════
-- Cooldown de email por usuario (Hunter Bot): Botlode 5 min, Metalwailers 10 min
-- Ejecutar en Supabase SQL Editor.
-- ═══════════════════════════════════════════════════════════════════════════

-- Agregar columna si no existe
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'hunter_configs' AND column_name = 'email_cooldown_seconds'
  ) THEN
    ALTER TABLE hunter_configs ADD COLUMN email_cooldown_seconds INTEGER DEFAULT 300;
    COMMENT ON COLUMN hunter_configs.email_cooldown_seconds IS 'Segundos de espera tras cada email enviado para este usuario (300=5min Botlode, 600=10min Metalwailers). NULL = usar default del worker (300).';
  END IF;
END $$;

-- Botlode (getbotlode / tu cuenta): cada 5 minutos
UPDATE hunter_configs SET email_cooldown_seconds = 300
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Metalwailers: cada 10 minutos (mitad de emails por día)
UPDATE hunter_configs SET email_cooldown_seconds = 600
WHERE user_id = 'a18aa369-a8b7-45e4-9f73-cae2df5b0c78';

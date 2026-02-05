-- =============================================================================
-- HUNTER BOT - Control de bot y configuración de nicho
-- Añade campos para controlar el bot desde Botslode
-- =============================================================================

-- Agregar campos de control del bot a hunter_configs
DO $$ 
BEGIN
    -- Campo bot_enabled: si el bot está prendido o apagado
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'bot_enabled'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN bot_enabled BOOLEAN DEFAULT false;
    END IF;
    
    -- Campo nicho: qué tipo de negocios buscar
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'nicho'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN nicho TEXT DEFAULT 'inmobiliarias';
    END IF;
    
    -- Campo ciudades: array de ciudades donde buscar
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'ciudades'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN ciudades TEXT[] DEFAULT ARRAY['Buenos Aires', 'Córdoba', 'Rosario'];
    END IF;
    
    -- Campo pais: país donde buscar
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hunter_configs' AND column_name = 'pais'
    ) THEN
        ALTER TABLE hunter_configs ADD COLUMN pais TEXT DEFAULT 'Argentina';
    END IF;
END $$;

-- Índice para buscar usuarios con bot habilitado (query frecuente del worker)
CREATE INDEX IF NOT EXISTS idx_hunter_configs_bot_enabled 
    ON hunter_configs(bot_enabled) 
    WHERE bot_enabled = true;

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================

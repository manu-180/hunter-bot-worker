-- =============================================================================
-- FIX: Cambiar UNIQUE de domain a (user_id, domain)
-- =============================================================================
-- Esto permite que varios usuarios puedan scrapear el mismo dominio,
-- pero cada usuario NO puede duplicar sus propios dominios.
-- =============================================================================

-- 1. Eliminar el constraint UNIQUE viejo (solo en domain)
ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_domain_key;

-- 2. Crear UNIQUE constraint nuevo: (user_id, domain)
-- Esto permite:
--   ✅ Usuario A → empresa.com
--   ✅ Usuario B → empresa.com (ambos pueden tener el mismo dominio)
--   ❌ Usuario A → empresa.com (duplicado) → se bloquea
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'leads_user_domain_unique'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT leads_user_domain_unique 
            UNIQUE (user_id, domain);
    END IF;
END $$;

-- =============================================================================
-- Verificación
-- =============================================================================
-- Para verificar que el constraint se aplicó correctamente:
-- SELECT conname, contype FROM pg_constraint WHERE conrelid = 'leads'::regclass;
-- 
-- Deberías ver: leads_user_domain_unique | u
-- =============================================================================

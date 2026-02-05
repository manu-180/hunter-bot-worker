-- =============================================================================
-- HUNTER BOT - Tablas adicionales para soporte multi-tenant
-- Ejecutar en Supabase SQL Editor
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Tabla hunter_configs: Configuración de Resend por usuario
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hunter_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Credenciales de Resend
    resend_api_key TEXT,
    from_email TEXT,
    from_name TEXT DEFAULT 'Mi Empresa',
    
    -- Configuración adicional
    calendar_link TEXT,
    email_subject TEXT DEFAULT 'Potenciemos tu negocio juntos',
    
    -- Estado
    is_active BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Un usuario solo puede tener una configuración
    UNIQUE(user_id)
);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_hunter_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_hunter_configs_updated_at ON hunter_configs;
CREATE TRIGGER trigger_update_hunter_configs_updated_at
    BEFORE UPDATE ON hunter_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_hunter_configs_updated_at();

-- Índice para búsqueda por usuario
CREATE INDEX IF NOT EXISTS idx_hunter_configs_user ON hunter_configs(user_id);

-- RLS (Row Level Security) para que cada usuario solo vea su config
ALTER TABLE hunter_configs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own config" ON hunter_configs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own config" ON hunter_configs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own config" ON hunter_configs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own config" ON hunter_configs
    FOR DELETE USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 2. Tabla hunter_logs: Logs en tiempo real del proceso
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hunter_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Información del log
    domain TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('info', 'success', 'warning', 'error')),
    action TEXT NOT NULL CHECK (action IN (
        'scrape_start', 'scrape_end', 
        'email_found', 'email_not_found',
        'send_start', 'send_success', 'send_failed',
        'config_missing', 'domain_added', 'system_info'
    )),
    message TEXT NOT NULL,
    
    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_hunter_logs_user ON hunter_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_hunter_logs_created ON hunter_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hunter_logs_user_created ON hunter_logs(user_id, created_at DESC);

-- RLS para que cada usuario solo vea sus logs
ALTER TABLE hunter_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own logs" ON hunter_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own logs" ON hunter_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Limpieza automática de logs viejos (más de 7 días)
-- Ejecutar como cron job o manualmente
-- DELETE FROM hunter_logs WHERE created_at < NOW() - INTERVAL '7 days';

-- -----------------------------------------------------------------------------
-- 3. Modificar tabla leads para soporte multi-tenant
-- -----------------------------------------------------------------------------
-- Agregar columna user_id si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE leads ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Índice para búsqueda por usuario
CREATE INDEX IF NOT EXISTS idx_leads_user ON leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_user_status ON leads(user_id, status);

-- RLS para leads (cada usuario ve solo sus leads)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own leads" ON leads;
CREATE POLICY "Users can view own leads" ON leads
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own leads" ON leads;
CREATE POLICY "Users can insert own leads" ON leads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own leads" ON leads;
CREATE POLICY "Users can update own leads" ON leads
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own leads" ON leads;
CREATE POLICY "Users can delete own leads" ON leads
    FOR DELETE USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 4. Habilitar Realtime para las tablas
-- -----------------------------------------------------------------------------
-- Habilitar realtime para hunter_logs (para ver logs en tiempo real)
ALTER PUBLICATION supabase_realtime ADD TABLE hunter_logs;

-- Habilitar realtime para leads (para ver cambios de estado)
ALTER PUBLICATION supabase_realtime ADD TABLE leads;

-- -----------------------------------------------------------------------------
-- 5. Función para obtener estadísticas del usuario
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_hunter_stats(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total', COUNT(*),
        'pending', COUNT(*) FILTER (WHERE status = 'pending'),
        'scraping', COUNT(*) FILTER (WHERE status = 'scraping'),
        'scraped', COUNT(*) FILTER (WHERE status = 'scraped'),
        'queued_for_send', COUNT(*) FILTER (WHERE status = 'queued_for_send'),
        'sending', COUNT(*) FILTER (WHERE status = 'sending'),
        'sent', COUNT(*) FILTER (WHERE status = 'sent'),
        'failed', COUNT(*) FILTER (WHERE status = 'failed'),
        'emails_found', COUNT(*) FILTER (WHERE email IS NOT NULL)
    ) INTO result
    FROM leads
    WHERE user_id = p_user_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Dar permisos para ejecutar la función
GRANT EXECUTE ON FUNCTION get_hunter_stats(UUID) TO authenticated;

-- -----------------------------------------------------------------------------
-- 6. Tabla user_products: Productos comprados por usuario
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL,
    
    -- Estado de la compra
    purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- NULL = permanente
    is_active BOOLEAN DEFAULT true,
    
    -- Referencia al pago
    transaction_id UUID,
    
    UNIQUE(user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_user_products_user ON user_products(user_id);

-- RLS para user_products
ALTER TABLE user_products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own products" ON user_products
    FOR SELECT USING (auth.uid() = user_id);

-- Solo el backend puede insertar/actualizar productos (service role)
-- No se agregan policies de INSERT/UPDATE para usuarios normales

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================

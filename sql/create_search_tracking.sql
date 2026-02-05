-- =============================================================================
-- DOMAIN SEARCH TRACKING - Sistema de Rotación Inteligente
-- Tabla para rastrear el progreso de búsqueda de cada usuario en cada combinación
-- =============================================================================

CREATE TABLE IF NOT EXISTS domain_search_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    nicho TEXT NOT NULL,
    ciudad TEXT NOT NULL,
    pais TEXT NOT NULL,
    current_page INT DEFAULT 0,
    total_domains_found INT DEFAULT 0,
    is_exhausted BOOLEAN DEFAULT false,
    last_searched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraint: cada combinación es única por usuario
    UNIQUE(user_id, nicho, ciudad, pais)
);

-- =============================================================================
-- ÍNDICES para optimizar queries frecuentes
-- =============================================================================

-- Índice para buscar tracking de un usuario específico
CREATE INDEX IF NOT EXISTS idx_search_tracking_user 
    ON domain_search_tracking(user_id);

-- Índice para buscar combinaciones no agotadas (query principal del worker)
CREATE INDEX IF NOT EXISTS idx_search_tracking_exhausted 
    ON domain_search_tracking(user_id, is_exhausted);

-- Índice compuesto para ordenar por página (para "exprimir" cada combinación)
CREATE INDEX IF NOT EXISTS idx_search_tracking_user_page 
    ON domain_search_tracking(user_id, is_exhausted, current_page);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

ALTER TABLE domain_search_tracking ENABLE ROW LEVEL SECURITY;

-- Policy: usuarios pueden ver solo su propio tracking
CREATE POLICY "Users can view own tracking"
    ON domain_search_tracking
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: usuarios pueden actualizar solo su propio tracking
CREATE POLICY "Users can update own tracking"
    ON domain_search_tracking
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: usuarios pueden insertar su propio tracking
CREATE POLICY "Users can insert own tracking"
    ON domain_search_tracking
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: service_role puede hacer todo (para el worker)
CREATE POLICY "Service role has full access"
    ON domain_search_tracking
    FOR ALL
    USING (true);

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================

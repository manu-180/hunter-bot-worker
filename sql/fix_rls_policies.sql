-- =============================================================================
-- FIX: Políticas RLS para que el worker (service_role) pueda operar
-- Ejecutar en Supabase SQL Editor
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Agregar políticas para service_role en hunter_logs
-- El backend worker necesita insertar logs para cualquier usuario
-- -----------------------------------------------------------------------------

-- Política para que service_role pueda insertar logs (backend worker)
DROP POLICY IF EXISTS "Service role can insert logs" ON hunter_logs;
CREATE POLICY "Service role can insert logs" ON hunter_logs
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Política para que service_role pueda leer logs (debugging)
DROP POLICY IF EXISTS "Service role can view all logs" ON hunter_logs;
CREATE POLICY "Service role can view all logs" ON hunter_logs
    FOR SELECT
    TO service_role
    USING (true);

-- -----------------------------------------------------------------------------
-- 2. Agregar políticas para service_role en leads
-- El backend necesita leer/actualizar leads de todos los usuarios
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS "Service role can view all leads" ON leads;
CREATE POLICY "Service role can view all leads" ON leads
    FOR SELECT
    TO service_role
    USING (true);

DROP POLICY IF EXISTS "Service role can update all leads" ON leads;
CREATE POLICY "Service role can update all leads" ON leads
    FOR UPDATE
    TO service_role
    USING (true);

DROP POLICY IF EXISTS "Service role can insert leads" ON leads;
CREATE POLICY "Service role can insert leads" ON leads
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- 3. Agregar políticas para service_role en hunter_configs
-- El backend necesita leer configs de todos los usuarios para enviar emails
-- -----------------------------------------------------------------------------

DROP POLICY IF EXISTS "Service role can view all configs" ON hunter_configs;
CREATE POLICY "Service role can view all configs" ON hunter_configs
    FOR SELECT
    TO service_role
    USING (true);

-- -----------------------------------------------------------------------------
-- 4. Verificar que Realtime esté habilitado
-- -----------------------------------------------------------------------------

-- Si da error "already exists", ignorar - ya está habilitado
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE hunter_logs;
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'hunter_logs already in realtime publication';
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE leads;
EXCEPTION WHEN duplicate_object THEN
    RAISE NOTICE 'leads already in realtime publication';
END $$;

-- =============================================================================
-- FIN - Ahora el worker con service_role key puede operar
-- =============================================================================

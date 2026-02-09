-- =============================================================================
-- RPC: increment_search_page
-- Reduce 2 queries (SELECT + UPDATE) a 1 sola operación atómica.
-- Llamado desde domain_hunter_worker.py via supabase.rpc()
-- =============================================================================

CREATE OR REPLACE FUNCTION increment_search_page(
    p_user_id UUID,
    p_nicho TEXT,
    p_ciudad TEXT,
    p_pais TEXT,
    p_domains_found INT
) RETURNS VOID AS $$
BEGIN
    UPDATE domain_search_tracking
    SET current_page = current_page + 1,
        total_domains_found = total_domains_found + p_domains_found,
        last_searched_at = NOW(),
        updated_at = NOW()
    WHERE user_id = p_user_id
      AND nicho = p_nicho
      AND ciudad = p_ciudad
      AND pais = p_pais;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Permitir invocación desde service_role
GRANT EXECUTE ON FUNCTION increment_search_page(UUID, TEXT, TEXT, TEXT, INT) TO service_role;

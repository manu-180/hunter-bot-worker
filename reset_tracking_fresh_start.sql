-- ═══════════════════════════════════════════════════════════════════════════════
-- 🔄 RESET COMPLETO DEL TRACKING - INICIO DESDE CERO
-- ═══════════════════════════════════════════════════════════════════════════════
-- 
-- Este script BORRA todas las combinaciones existentes y deja que el bot
-- cree automáticamente las nuevas desde cero con el algoritmo mejorado.
--
-- ⚠️  IMPORTANTE: Esto NO borra los dominios ya recopilados en la tabla "leads"
--    Solo resetea el tracking para que el bot empiece con las nuevas 2,100 ciudades.
--
-- CUÁNDO USAR:
-- - Después de deployar los cambios del algoritmo infinito
-- - Si querés empezar de cero con la nueva base de ciudades
-- - Si el tracking está desactualizado o tiene combinaciones viejas
--
-- CUÁNDO NO USAR:
-- - Si el bot ya está funcionando bien con las combinaciones actuales
-- - Si no querés perder el progreso de las combinaciones existentes
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1️⃣  VER ESTADO ACTUAL (antes de borrar)
SELECT
    COUNT(*) as total_combinaciones,
    COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas,
    SUM(total_domains_found) as total_dominios_encontrados
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- 2️⃣  VER ÚLTIMAS COMBINACIONES PROCESADAS
SELECT
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
ORDER BY last_searched_at DESC NULLS LAST
LIMIT 20;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 🗑️  BORRAR TODO EL TRACKING (DESCOMENTAR PARA EJECUTAR)
-- ═══════════════════════════════════════════════════════════════════════════════

/*
DELETE FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';
*/

-- ═══════════════════════════════════════════════════════════════════════════════
-- ✅ VERIFICAR QUE SE BORRÓ TODO
-- ═══════════════════════════════════════════════════════════════════════════════

SELECT COUNT(*) as combinaciones_restantes
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';
-- Debería retornar 0

-- ═══════════════════════════════════════════════════════════════════════════════
-- 🚀 PRÓXIMOS PASOS (después de borrar)
-- ═══════════════════════════════════════════════════════════════════════════════
-- 
-- 1. El bot automáticamente creará la primera combinación:
--    - Nicho: primer nicho de la lista (ej: "inmobiliarias")
--    - País: Argentina (primer país)
--    - Ciudad: Buenos Aires (primera ciudad de Argentina)
--
-- 2. Desde ahí, el algoritmo progresará secuencialmente:
--    Buenos Aires → Córdoba → Rosario → ... → toda Argentina
--    → México → Colombia → ... → todos los países
--    → siguiente nicho → reinicia países
--
-- 3. Monitorear en Railway logs:
--    - Buscar: "Nueva combinación"
--    - Buscar: "Progresión: Siguiente ciudad en..."
--    - Buscar: "Progresión: Completado X, pasando a Y"
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- 📊 MONITOREO EN TIEMPO REAL (ejecutar cada 5 min)
SELECT
    nicho,
    pais,
    COUNT(*) as ciudades_procesadas,
    SUM(total_domains_found) as dominios_encontrados,
    MAX(last_searched_at) as ultima_busqueda
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
GROUP BY nicho, pais
ORDER BY ultima_busqueda DESC NULLS LAST;

-- Ver progreso detallado de la combinación actual
SELECT
    nicho,
    ciudad,
    pais,
    current_page,
    total_domains_found,
    is_exhausted,
    last_searched_at,
    EXTRACT(EPOCH FROM (NOW() - last_searched_at))/60 as minutos_desde_ultima
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND last_searched_at IS NOT NULL
ORDER BY last_searched_at DESC
LIMIT 1;

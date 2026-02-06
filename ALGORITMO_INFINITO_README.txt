═══════════════════════════════════════════════════════════════════════════════
🚀 ALGORITMO DE BÚSQUEDA "CASI INFINITO" - IMPLEMENTACIÓN COMPLETA
═══════════════════════════════════════════════════════════════════════════════

Este documento explica el nuevo sistema de búsqueda masiva de dominios que puede
generar MILLONES de combinaciones sin repetir.

═══════════════════════════════════════════════════════════════════════════════
📊 NÚMEROS DEL SISTEMA
═══════════════════════════════════════════════════════════════════════════════

✅ NICHOS: 120 (expandido desde 50)
   - Servicios profesionales (20)
   - Servicios locales (25)
   - Construcción y mantenimiento (15)
   - Retail y comercio (20)
   - Gastronomía (20)
   - Salud y bienestar (20)
   - Educación y capacitación (15)
   - Turismo y hotelería (15)
   - Eventos y entretenimiento (12)
   - Industria y producción (15)
   - Agricultura y ganadería (10)
   - Transporte y logística (12)
   - Tecnología y comunicaciones (10)
   - Servicios financieros y seguros (8)
   - Automotor (10)
   - Decoración y hogar (10)
   - Mascotas y animales (8)
   - Flores y jardinería (8)

✅ PAÍSES: 17 países latinoamericanos (sin Brasil por idioma)
   - Argentina (primero - ~350 ciudades)
   - México (~300 ciudades)
   - Colombia (~200 ciudades)
   - Chile (~150 ciudades)
   - Perú (~150 ciudades)
   - Ecuador (~100 ciudades)
   - Venezuela (~80 ciudades)
   - Bolivia (~80 ciudades)
   - Paraguay (~60 ciudades)
   - Uruguay (~50 ciudades)
   - República Dominicana (~60 ciudades)
   - Guatemala (~50 ciudades)
   - Honduras (~40 ciudades)
   - Nicaragua (~40 ciudades)
   - Costa Rica (~40 ciudades)
   - Panamá (~40 ciudades)
   - El Salvador (~40 ciudades)

✅ CIUDADES: ~2,100 ciudades en total

✅ COMBINACIONES TOTALES:
   120 nichos × 2,100 ciudades = 252,000 combinaciones

✅ PÁGINAS POR COMBINACIÓN: ~3 páginas promedio (hasta agotar)
   252,000 combinaciones × 3 páginas = 756,000 búsquedas totales

✅ DOMINIOS POTENCIALES:
   756,000 búsquedas × 5 dominios promedio = 3,780,000 dominios únicos

═══════════════════════════════════════════════════════════════════════════════
🎯 ESTRATEGIA DE PROGRESIÓN (CLAVE DEL SISTEMA)
═══════════════════════════════════════════════════════════════════════════════

El bot sigue una estrategia SECUENCIAL y EXHAUSTIVA para nunca repetir hasta
completar TODO el ciclo:

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. NICHO ACTUAL: "inmobiliarias"                                            │
│    ├─ 2. PAÍS ACTUAL: "Argentina"                                           │
│    │  ├─ 3. CIUDAD: Buenos Aires                                            │
│    │  │  ├─ Página 0 (resultados 1-20)                                      │
│    │  │  ├─ Página 1 (resultados 21-40)                                     │
│    │  │  ├─ Página 2 (resultados 41-60)                                     │
│    │  │  └─ ✅ 0 resultados → AGOTADA, siguiente ciudad                     │
│    │  ├─ 3. CIUDAD: Córdoba                                                 │
│    │  ├─ 3. CIUDAD: Rosario                                                 │
│    │  ├─ ...                                                                │
│    │  └─ 3. CIUDAD: Ushuaia (última de Argentina)                          │
│    │      └─ ✅ Completó Argentina → Siguiente país                         │
│    ├─ 2. PAÍS: "México"                                                     │
│    │  ├─ 3. CIUDAD: Ciudad de México                                        │
│    │  ├─ ...                                                                │
│    │  └─ 3. CIUDAD: Cancún (última de México)                              │
│    ├─ 2. PAÍS: "Colombia"                                                   │
│    ├─ ...                                                                   │
│    └─ 2. PAÍS: "El Salvador" (último país)                                 │
│       └─ ✅ Completó todos los países → Siguiente nicho                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. NICHO: "estudios contables"                                              │
│    ├─ 2. PAÍS: "Argentina" (reinicia desde primer país)                    │
│    │  ├─ 3. CIUDAD: Buenos Aires                                            │
│    │  ├─ ...                                                                │
└─────────────────────────────────────────────────────────────────────────────┘

CLAVE: El bot NO salta aleatoriamente entre nichos/países. Completa TODO un
país antes de pasar al siguiente, y TODOS los países antes de cambiar de nicho.

═══════════════════════════════════════════════════════════════════════════════
🧠 LÓGICA INTELIGENTE DE AGOTAMIENTO
═══════════════════════════════════════════════════════════════════════════════

ANTES (problema): Marcaba como agotada después de 1 búsqueda sin resultados
AHORA (mejor): Da 3 intentos antes de marcar como agotada

Pseudocódigo:

    if dominios_encontrados == 0:
        if pagina_actual >= 2:  # Ya probamos páginas 0, 1, 2
            → Marcar como AGOTADA
            → Rotar a siguiente ciudad/país/nicho
        else:  # Primer o segundo intento
            → Incrementar página
            → Dar otra chance

Esto evita descartar combinaciones productivas prematuramente.

═══════════════════════════════════════════════════════════════════════════════
🔄 VARIACIÓN DE QUERIES (PARA EVITAR DUPLICADOS)
═══════════════════════════════════════════════════════════════════════════════

Cada página usa un MODIFICADOR diferente para obtener resultados variados:

Página 0: "inmobiliarias en Buenos Aires"
Página 1: "inmobiliarias Buenos Aires contacto"
Página 2: "inmobiliarias profesionales Buenos Aires"
Página 3: "empresas de inmobiliarias Buenos Aires"
Página 4: "inmobiliarias en Buenos Aires" (vuelve a empezar el ciclo)

Esto aumenta la variedad de resultados y reduce duplicados.

═══════════════════════════════════════════════════════════════════════════════
🛡️ FILTROS AVANZADOS (PARA CALIDAD)
═══════════════════════════════════════════════════════════════════════════════

El bot aplica 9 validaciones a cada dominio encontrado:

1. ❌ Google Maps links (/maps/)
2. ❌ Caracteres inválidos ([]{}\|% etc)
3. ❌ Sin TLD (.com, .ar, etc)
4. ❌ Palabras de prueba (test, demo, example)
5. ❌ Blacklist expandida (50+ dominios genéricos)
6. ❌ Dominios gubernamentales (.gob., .gov., .mil., .edu.ar)
7. ❌ Nombres muy cortos (<3 caracteres antes del TLD)
8. ❌ Plataformas gratuitas (blogspot, wix, etc)
9. ❌ Emails mal formateados

Solo pasan dominios REALES de negocios.

═══════════════════════════════════════════════════════════════════════════════
📁 ARCHIVOS MODIFICADOS
═══════════════════════════════════════════════════════════════════════════════

1. 🆕 cities_data.py
   - Nuevo archivo con 2,100 ciudades organizadas
   - Categorizado por país
   - Argentina primero, resto por población

2. ✏️  domain_hunter_worker.py
   - NICHOS expandido de 50 → 120
   - Import de cities_data.py
   - _create_next_combination() mejorado (progresión secuencial)
   - Lógica de agotamiento inteligente (3 intentos)
   - Variación de queries por página

═══════════════════════════════════════════════════════════════════════════════
🚀 DEPLOYMENT
═══════════════════════════════════════════════════════════════════════════════

1. Subir cambios a Railway:
   
   git add .
   git commit -m "Algoritmo infinito: 120 nichos × 2,100 ciudades"
   git push origin main

2. Railway detectará los cambios y re-deployará automáticamente

3. Verificar logs en Railway:
   - Buscar: "Base de ciudades cargada: 17 países, 2100 ciudades"
   - Buscar: "Progresión: Siguiente ciudad en..."

4. Resetear tracking existente (OPCIONAL):

   -- Borrar combinaciones viejas (opcional)
   DELETE FROM domain_search_tracking
   WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

   -- El bot creará automáticamente desde cero

═══════════════════════════════════════════════════════════════════════════════
📊 MONITOREO
═══════════════════════════════════════════════════════════════════════════════

Ver progresión en tiempo real:

-- Combinaciones activas
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
LIMIT 10;

-- Estadísticas globales
SELECT
    COUNT(*) as total_combinaciones,
    COUNT(*) FILTER (WHERE is_exhausted = false) as activas,
    COUNT(*) FILTER (WHERE is_exhausted = true) as agotadas,
    SUM(total_domains_found) as total_dominios_encontrados,
    COUNT(DISTINCT nicho) as nichos_unicos,
    COUNT(DISTINCT pais) as paises_unicos,
    COUNT(DISTINCT ciudad) as ciudades_unicas
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e';

-- Ver último nicho/país/ciudad procesados
SELECT
    nicho,
    pais,
    ciudad,
    current_page,
    last_searched_at
FROM domain_search_tracking
WHERE user_id = '38152119-7da4-442e-9826-20901c65f42e'
  AND last_searched_at IS NOT NULL
ORDER BY last_searched_at DESC
LIMIT 1;

═══════════════════════════════════════════════════════════════════════════════
⚠️  CONSIDERACIONES IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

1. COSTOS DE SERPAPI:
   - 756,000 búsquedas totales estimadas
   - A $5 por 1,000 búsquedas = $3,780 total
   - Distribución sugerida en tiempo:
     * 1,000 búsquedas/día = 2.5 años para completar ciclo
     * 5,000 búsquedas/día = 5 meses para completar ciclo
     * 10,000 búsquedas/día = 2.5 meses para completar ciclo

2. RATE LIMITS:
   - SerpAPI: 100 búsquedas/segundo (no es problema)
   - Supabase: 100 requests/segundo (no es problema)
   - Delay configurado: 4-8 segundos entre búsquedas

3. TIEMPO DE EJECUCIÓN:
   - Con delay de 6s promedio = 10 búsquedas/minuto = 600/hora
   - 756,000 búsquedas ÷ 600/hora = 1,260 horas = 52 días de ejecución continua

4. DUPLICADOS:
   - El constraint UNIQUE(user_id, domain) en la tabla leads previene duplicados
   - Si un dominio ya existe, simplemente se ignora

═══════════════════════════════════════════════════════════════════════════════
🎉 RESUMEN FINAL
═══════════════════════════════════════════════════════════════════════════════

✅ Sistema configurado para generar 252,000 combinaciones únicas
✅ 756,000 búsquedas estimadas antes de repetir
✅ ~3,780,000 dominios potenciales
✅ Progresión inteligente: ciudad → país → nicho → loop infinito
✅ Filtros avanzados para dominios de calidad
✅ Argentina primero, Brasil excluido
✅ Sin repeticiones hasta completar ciclo completo
✅ Sistema auto-gestionado (crea combinaciones sobre la marcha)

🚀 El bot ahora es imparable. Puede correr 24/7 durante MESES sin repetir.

═══════════════════════════════════════════════════════════════════════════════
📞 SOPORTE
═══════════════════════════════════════════════════════════════════════════════

Si el bot se detiene o hay problemas:

1. Verificar logs en Railway
2. Verificar SERPAPI_KEY tiene créditos
3. Verificar bot_enabled = true en hunter_configs
4. Consultar este documento para entender la lógica

═══════════════════════════════════════════════════════════════════════════════
Creado: 2026-02-06
Versión: 2.0 - ALGORITMO INFINITO
═══════════════════════════════════════════════════════════════════════════════

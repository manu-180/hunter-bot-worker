"""
Configuración para Domain Hunter - Editar según tu nicho

Este archivo define qué buscar en Google. Editá los valores y ejecutá:
    python domain_hunter.py
"""

# =============================================================================
# CONFIGURACIÓN PRINCIPAL
# =============================================================================

# Nicho/industria a buscar
NICHO = "inmobiliarias"

# País
PAIS = "Argentina"

# Ciudades a buscar (más ciudades = más resultados)
CIUDADES = [
    "Buenos Aires",
    "Córdoba",
    "Rosario",
    "Mendoza",
    "Tucumán",
    "La Plata",
    "Mar del Plata",
    "Salta",
    "Santa Fe",
    "San Juan",
]

# =============================================================================
# OPCIONES AVANZADAS
# =============================================================================

# User ID de Supabase (para guardar dominios automáticamente)
# Dejalo en None si querés solo generar el archivo .txt
# Si ponés tu user_id, los dominios se agregan directo a tu cola en Botslode
USER_ID = None  # Ej: "38152119-7da4-442e-9826-20901c65f42e"

# Delays para evitar bloqueo de Google
MIN_DELAY_SECONDS = 30   # Mínimo 30s (recomendado)
MAX_DELAY_SECONDS = 90   # Máximo 90s (recomendado)

# Cuántos dominios conseguir antes de detenerse
MAX_DOMAINS = 5000

# =============================================================================
# EJEMPLOS DE NICHOS
# =============================================================================
# Descomentá el que quieras usar:

# NICHO = "agencias de marketing digital"
# NICHO = "estudios contables"
# NICHO = "despachos de abogados"
# NICHO = "clínicas dentales"
# NICHO = "estudios de arquitectura"
# NICHO = "consultoras de recursos humanos"
# NICHO = "empresas de software"
# NICHO = "talleres mecánicos"
# NICHO = "restaurantes"
# NICHO = "gimnasios"

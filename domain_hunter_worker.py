"""
Domain Hunter Worker v8 - Worker daemon optimizado para buscar dominios.

Optimizaciones v8 (sobre v7):
- Query limpia: sin -site: exclusions en query (filtrado post-extraction con blacklist)
- num=100: máximo absoluto de resultados orgánicos por crédito (SerpAPI cobra igual)
- Maps x4: paginación extendida start=0/20/40/60 (antes solo 0/20)
- Web paginación: start=0/10 para obtener páginas 2+ de la misma query
- Cache cross-user: reusar resultados de queries idénticas (0 créditos)
- Per-user cache: session cache separado por usuario (sin cross-contamination)
- User config: respeta nicho/ciudades/pais de la config del usuario
- Related searches: captura sugerencias gratuitas de Google
- Sin doble delay: un solo sleep entre búsquedas (antes había 2)
- Constantes optimizadas: frozensets a nivel de módulo (no per-call)
- Secuencia 25 pasos: Web num=100 + Maps, ~1000+ dominios/combinación
- 15 fuentes de extracción web (organic, snippets, displayed_link, local, KG, ads,
  places, answer_box, news, videos, questions, shopping, images, events, jobs, twitter)
- Regex en snippets: extrae dominios mencionados en texto de resultados
- Maps zoom 12z: cobertura geográfica más amplia por búsqueda
- Rotación de nichos: prioriza el del usuario pero rota por todos (45+)

Optimizaciones v7 (heredadas):
- Multi-source extraction: organic + local + KG + ads + places (7 fuentes)
- Blacklist O(1): lookup optimizado con sets separados
- Credit management: pre-check periódico, budget por usuario
- Parallel users: procesamiento concurrente con semáforo

Usage:
    python domain_hunter_worker.py
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import time
import traceback
import urllib.request
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from serpapi import GoogleSearch
from supabase import create_client, Client

from src.config import BotConfig
from src.key_rotator import SerpApiKeyRotator
from src.utils.timezone import is_business_hours, format_argentina_time, format_utc_time, utc_now
from src.web_verification import (
    STRICT_NO_WEB_CHECK, STRICT_NO_WEB_MIN_CONFIDENCE,
    batch_verify as _batch_verify_no_web,
)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role key
# Delays y configuración centralizada via BotConfig (overrideable via env vars)
MIN_DELAY_BETWEEN_SEARCHES = BotConfig.MIN_DELAY_BETWEEN_SEARCHES
MAX_DELAY_BETWEEN_SEARCHES = BotConfig.MAX_DELAY_BETWEEN_SEARCHES
CHECK_USERS_INTERVAL = BotConfig.CHECK_USERS_INTERVAL
BUSINESS_HOURS_START = BotConfig.BUSINESS_HOURS_START
BUSINESS_HOURS_END = BotConfig.BUSINESS_HOURS_END
PAUSE_CHECK_INTERVAL = BotConfig.PAUSE_CHECK_INTERVAL

# =============================================================================
# v8: QUERY_SITE_EXCLUSIONS eliminadas del query string.
# Razón: Google tiene límite de ~32 palabras. 14 operadores -site: consumían
# ~300 chars y podían truncar la query real. Ahora se filtran post-extraction
# con la blacklist O(1) que ya existe (_ALL_BLACKLIST), que es más precisa
# y no desperdicia espacio en la query.
# =============================================================================

# =============================================================================
# TEMPLATES DE QUERY EXPANDIDOS v7
# 8 templates con operadores avanzados para máxima diversidad.
# Cada combinación usa hasta MAX_PAGES_PER_COMBINATION templates (rotación).
# Índices pares = web search, índices impares = Google Maps search.
# =============================================================================
QUERY_TEMPLATES_WEB = [
    "{nicho} en {ciudad}",                                    # 0: Busqueda directa
    "{nicho} {ciudad} contacto email",                        # 1: Datos de contacto
    "mejores {nicho} {ciudad} 2025",                          # 2: Rankings actuales
    "{nicho} {ciudad} whatsapp telefono sitio web",           # 3: Negocios con presencia web
    'intitle:"{nicho}" "{ciudad}" -directorio -listado',      # 4: Excluir directorios
    "{nicho} profesional {ciudad} presupuesto",               # 5: Intent comercial
    "{nicho} recomendados {ciudad} opiniones",                # 6: Reviews con negocios
    "empresas de {nicho} en {ciudad} servicios",              # 7: B2B intent
    "{nicho} cerca de {ciudad} sitio web oficial",            # 8: Negocios con web oficial
    "{nicho} nuevos {ciudad} 2025 2026",                      # 9: Negocios recientes
    "directorio {nicho} {ciudad}",                            # 10: Listados con links a negocios
]

QUERY_TEMPLATES_MAPS = [
    "{nicho} en {ciudad}",                                    # Query directa para Maps
    "{nicho} {ciudad}",                                       # Query corta para Maps
    "mejores {nicho} {ciudad}",                               # Query con ranking para Maps
]

# =============================================================================
# SECUENCIA DE BÚSQUEDA v8 - Prioriza Maps (20+ dominios/crédito) sobre Web (~10)
# Cada entrada: (tipo, índice_template, start_offset)
#   - tipo: 'web' o 'maps'
#   - índice_template: qué template de query usar
#   - start_offset: paginación (web: 0/10/20, maps: 0/20/40/60)
# =============================================================================
SEARCH_SEQUENCE = [
    # Cada web search devuelve hasta 100 orgánicos + local pack + KG + snippets + ads
    # Cada maps search devuelve ~20 negocios con website directo
    # COSTO: 1 crédito por línea, sin importar cuántos resultados devuelva
    #
    # --- Bloque 1: máximo rendimiento por crédito ---
    ("web",  0, 0),     # "{nicho} en {ciudad}": ~100 orgánicos + 15 fuentes extra
    ("maps", 0, 0),     # Maps pag 1: ~20 negocios con website
    ("web",  1, 0),     # "{nicho} {ciudad} contacto email": ~100 con datos
    ("maps", 0, 20),    # Maps pag 2: ~20 más
    ("web",  2, 0),     # "mejores {nicho} {ciudad} 2025": ~100 rankings
    ("maps", 1, 0),     # Maps query corta pag 1: ~20 negocios
    ("web",  3, 0),     # "{nicho} {ciudad} whatsapp telefono sitio web": ~100
    ("maps", 1, 20),    # Maps query corta pag 2: ~20 más
    # --- Bloque 2: queries de intención comercial ---
    ("web",  4, 0),     # intitle:"{nicho}" "{ciudad}": ~100 hits directos
    ("maps", 2, 0),     # Maps query ranking pag 1: ~20 negocios
    ("web",  5, 0),     # "{nicho} profesional {ciudad} presupuesto": ~100
    ("maps", 2, 20),    # Maps query ranking pag 2: ~20 más
    ("web",  6, 0),     # "{nicho} recomendados {ciudad} opiniones": ~100
    ("web",  7, 0),     # "empresas de {nicho} en {ciudad} servicios": ~100
    # --- Bloque 3: queries de cola larga (encuentran negocios que los demás no) ---
    ("web",  8, 0),     # "{nicho} cerca de {ciudad} sitio web oficial": ~100
    ("web",  9, 0),     # "{nicho} nuevos {ciudad} 2025 2026": ~100 recientes
    ("web",  10, 0),    # "directorio {nicho} {ciudad}": ~100 desde directorios
    ("maps", 0, 40),    # Maps T0 pag 3: ~20 más
    ("maps", 0, 60),    # Maps T0 pag 4: ~20 más
    ("maps", 0, 80),    # Maps T0 pag 5: ~20 más
]

# Máximo de búsquedas a probar por combinación (cada una = 1 crédito)
MAX_PAGES_PER_COMBINATION = len(SEARCH_SEQUENCE)

# Ratio mínimo de dominios nuevos para justificar seguir con más templates
MIN_NEW_RATIO_FOR_PAGINATION = 0.15  # Si <15% son nuevos, no gastar más créditos

# Mapeo correcto de país → código ISO 3166-1 para parámetro gl de Google
PAIS_GL_CODE = {
    "Argentina": "ar",
    "México": "mx",
    "Colombia": "co",
    "Chile": "cl",
    "Perú": "pe",
    "Ecuador": "ec",
    "Venezuela": "ve",
    "Bolivia": "bo",
    "Paraguay": "py",
    "Uruguay": "uy",
    "República Dominicana": "do",
    "Guatemala": "gt",
    "Honduras": "hn",
    "Nicaragua": "ni",
    "Costa Rica": "cr",
    "Panamá": "pa",
    "El Salvador": "sv",
}

# =============================================================================
# BLACKLIST OPTIMIZADA v7 - Separada en dos sets para lookup O(1)
# BLACKLIST_SUFFIXES: entradas con punto → se comparan con endswith()
# BLACKLIST_NAME_PARTS: palabras sueltas → se buscan en el name_part del dominio
# =============================================================================

_ALL_BLACKLIST = {
    # Redes sociales
    'google', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
    'tiktok', 'pinterest', 'whatsapp', 'telegram', 'snapchat', 'reddit',
    'threads.net', 'x.com',
    
    # Portales inmobiliarios (queremos inmobiliarias reales, no portales)
    'mercadolibre', 'olx', 'zonaprop', 'argenprop', 'properati',
    'trovit', 'lamudi', 'inmuebles24', 'metrocuadrado', 'fincaraiz',
    'nuroa', 'icasas', 'plusvalia', 'segundamano', 'vivanuncios',
    'doomos', 'nocnok',
    
    # Gobierno y entidades públicas
    'gob.ar', 'gov.ar', 'gobierno', 'afip', 'anses', 'arba',
    'municipalidad', 'intendencia',
    
    # Portales de noticias y medios
    'clarin', 'lanacion', 'infobae', 'pagina12', 'lavoz', 'losandes',
    'telam', 'perfil', 'ambito', 'cronista', 'elpais.com', 'bbc.com',
    'cnn.com', 'elnacional', 'eluniversal', 'milenio', 'excelsior',
    'eltiempo.com', 'semana.com',
    
    # Portales educativos
    'edu.ar', 'educacion', 'universidad', 'campus',
    
    # Bancos y servicios financieros
    'banco', 'santander', 'galicia', 'nacion', 'provincia.com',
    'hsbc', 'bbva', 'icbc', 'frances', 'supervielle',
    
    # Organizaciones y ONGs
    'wikipedia', 'wikidata', 'fundacion',
    
    # Portales de empleo
    'zonajobs', 'computrabajo', 'bumeran', 'indeed',
    'glassdoor', 'laborum',
    
    # Portales genéricos y marketplaces
    'booking.com', 'airbnb', 'tripadvisor', 'yelp', 'foursquare',
    'despegar', 'almundo', 'decolar', 'expedia',
    'amazon.com', 'ebay.com', 'alibaba', 'aliexpress',
    
    # Otros sitios a evitar
    'blogspot', 'wordpress.com', 'wix.com', 'weebly', 'tumblr',
    'gmail', 'outlook', 'hotmail', 'yahoo',
    
    # Directorios, agregadores y listados (NO son negocios reales)
    'paginasamarillas', 'guialocal', 'cylex', 'infoisinfo', 'tupalo',
    'hotfrog', 'brownbook', 'tuugo', 'findglocal', 'alignable',
    'manta.com', 'bbb.org', 'chamberofcommerce', 'justdial',
    'sulekha', 'yellowpages', 'whitepages', 'superpages',
    'citysearch', 'local.com', 'merchantcircle', 'showmelocal',
    'kompass', 'europages', 'dnb.com', 'crunchbase', 'zoominfo',
    'clutch.co', 'goodfirms', 'sortlist', 'designrush', 'upcity',
    'bark.com', 'thumbtack', 'angi.com', 'homeadvisor',
    'doctoralia', 'doctoranytime', 'topdoctors', 'saludonnet',
    'practo', 'zocdoc',
    'guiamedicadelsur', 'doctores.com',
    
    # Plataformas de reviews y listados
    'trustpilot', 'sitejabber', 'reviewsolicitors', 'getapp',
    'capterra', 'g2.com', 'softwareadvice', 'sourceforge',
    
    # CDNs, hosting, tech platforms (no son negocios target)
    'cloudflare', 'amazonaws', 'azurewebsites', 'herokuapp',
    'netlify', 'vercel', 'firebase', 'appspot', 'github',
    'gitlab', 'bitbucket', 'stackexchange', 'stackoverflow',
    'medium.com', 'substack',
    
    # Dominios genéricos de servicios/plataformas LATAM
    'mercadopago', 'mercadoshops', 'tiendanube', 'empretienda',
    'mitienda', 'pedidosya', 'rappi', 'uber', 'cabify', 'didi',
}

# Separar: entradas con punto = suffix match, sin punto = name_part match
BLACKLIST_SUFFIXES: frozenset = frozenset(b for b in _ALL_BLACKLIST if '.' in b)
BLACKLIST_NAME_PARTS: frozenset = frozenset(b for b in _ALL_BLACKLIST if '.' not in b)

# Extensiones de dominio gubernamentales a filtrar
GOVERNMENT_TLD: frozenset = frozenset({
    '.gob.', '.gov.', '.mil.', '.edu.ar', '.edu.mx', '.edu.co',
    '.edu.cl', '.edu.pe', '.edu.ec', '.ac.',
})

# =============================================================================
# TLDs VÁLIDOS para negocios en LATAM
# Solo aceptamos dominios con extensiones que un negocio real usaría
# =============================================================================
VALID_BUSINESS_TLDS: frozenset = frozenset({
    # Genéricos
    '.com', '.net', '.org', '.info', '.biz', '.co',
    # Argentina
    '.com.ar', '.ar',
    # México
    '.com.mx', '.mx',
    # Colombia
    '.com.co',
    # Chile
    '.cl',
    # Perú
    '.com.pe', '.pe',
    # Ecuador
    '.com.ec', '.ec',
    # Venezuela
    '.com.ve', '.ve',
    # Bolivia
    '.com.bo', '.bo',
    # Paraguay
    '.com.py', '.py',
    # Uruguay
    '.com.uy', '.uy',
    # República Dominicana
    '.com.do', '.do',
    # Centroamérica
    '.com.gt', '.gt', '.com.hn', '.hn', '.com.ni', '.ni',
    '.com.cr', '.cr', '.com.pa', '.pa', '.com.sv', '.sv',
    # Otros válidos
    '.io', '.app', '.dev', '.store', '.shop', '.online',
    '.site', '.website', '.tech', '.digital', '.agency',
    '.studio', '.design', '.consulting', '.legal', '.dental',
    '.health', '.clinic', '.vet', '.salon', '.spa',
    '.fitness', '.coach', '.photography', '.travel', '.realty',
    '.auto', '.car', '.restaurant', '.cafe', '.bar',
    '.hotel', '.tours',
})

# =============================================================================
# v8: CONSTANTES MOVIDAS A NIVEL DE MÓDULO (antes se creaban en cada llamada)
# Evita garbage collection innecesario en cada invocación de _is_valid_domain
# =============================================================================
INVALID_DOMAIN_CHARS: frozenset = frozenset('[]{|}\\  %?=&#›·»')

DIRECTORY_PATTERNS: frozenset = frozenset({
    'directorio', 'listado', 'guia-de', 'ranking', 'top10',
    'top-10', 'mejores-', 'buscar-', 'encontrar-', 'busca-',
    'encuentra-', 'compara-', 'comparar-', 'comparador',
    'paginas-', 'sitios-', 'empresas-de-', 'negocios-de-',
    'listof', 'directory', 'listing', 'finder', 'locator',
    'yellowpage', 'whitepage', 'reviews-', 'opiniones-de-',
})

EXAMPLE_DOMAIN_WORDS: tuple = ('ejemplo', 'example', 'test.', 'demo.', 'sample', 'localhost')

# Dominios EXACTOS de plataformas gratuitas / subdominios (filtrar por endswith)
FREE_PLATFORM_SUFFIXES: frozenset = frozenset({
    '.blogspot.com', '.blogspot.com.ar', '.blogspot.com.mx',
    '.wordpress.com', '.wix.com', '.wixsite.com',
    '.weebly.com', '.tumblr.com', '.github.io',
    '.netlify.app', '.vercel.app', '.herokuapp.com',
    '.web.app', '.firebaseapp.com', '.appspot.com',
    '.azurewebsites.net', '.onrender.com',
    '.carrd.co', '.godaddysites.com', '.squarespace.com',
    '.jimdosite.com', '.strikingly.com', '.webnode.com',
    '.empretienda.com.ar', '.mitiendanube.com',
    '.mercadoshops.com.ar', '.dfrwk.com',
})

# =============================================================================
# CLASIFICACIÓN EMPRESAS SIN DOMINIO (ventas_reservas vs landing_info)
# SerpAPI Maps devuelve type / types; mapeamos a oferta de servicio web.
# =============================================================================
_CLASIF_VENTAS_KEYWORDS = frozenset({
    "restaurant", "cafe", "bar", "hotel", "store", "shop", "retail",
    "real_estate", "car_dealer", "travel_agency", "gym", "spa", "salon",
    "dentist", "doctor", "clinic", "hospital", "pharmacy", "veterinar",
    "auto", "rental", "booking", "food", "bakery", "florist", "jewelry",
    "restaurant", "pizzeria", "panaderia", "inmobiliaria", "concesionaria",
    "hotel", "cabaña", "alojamiento", "gimnasio", "peluqueria", "farmacia",
})
_CLASIF_LANDING_KEYWORDS = frozenset({
    "lawyer", "attorney", "accountant", "consultant", "architect",
    "designer", "photographer", "abogado", "contador", "consultor",
    "arquitecto", "estudio", "asesor", "psicologo", "nutricionista",
})

def _clasificar_negocio(type_raw: Optional[str], types_list: Optional[List[str]]) -> Optional[str]:
    """Mapea type/types de SerpAPI a ventas_reservas o landing_info. None si no se puede."""
    combined = []
    if type_raw:
        combined.append(type_raw.lower().replace(" ", "_").replace("-", "_"))
    if types_list:
        for t in types_list:
            if isinstance(t, str):
                combined.append(t.lower().replace(" ", "_").replace("-", "_"))
    text = " ".join(combined)
    for kw in _CLASIF_VENTAS_KEYWORDS:
        if kw in text:
            return "ventas_reservas"
    for kw in _CLASIF_LANDING_KEYWORDS:
        if kw in text:
            return "landing_info"
    return None

# =============================================================================
# LISTAS DE ROTACIÓN AUTOMÁTICA
# =============================================================================

# Nichos con ALTA probabilidad de querer un bot asistente virtual 24/7
# Ordenados de MAYOR a MENOR probabilidad de conversión
# Criterios: necesitan captar leads 24/7, agendar turnos/reuniones,
# responder consultas fuera de horario, y tienen margen para invertir.
NICHOS = [
    # ========== TIER 1 - MÁXIMA PROBABILIDAD (leads 24/7 + alto ticket) ==========
    "inmobiliarias",                        # 1. Consultas de propiedades a toda hora, alto ticket
    "clinicas dentales",                    # 2. Turnos, urgencias, presupuestos 24/7
    "concesionarias de autos",              # 3. Alto ticket, test drives, cotizaciones
    "centros de estetica",                  # 4. Turnos online, alta competencia digital
    "clinicas y centros medicos",           # 5. Turnos médicos, consultas de pacientes
    "hoteles",                              # 6. Reservas 24/7, huéspedes en distintas zonas horarias
    "agencias de marketing digital",        # 7. Tech-savvy, potenciales revendedores del bot
    "estudios juridicos",                   # 8. Consultas legales, agendar reuniones, alto ticket
    "consultorios medicos",                 # 9. Turnos, preguntas frecuentes de pacientes
    "estudios contables",                   # 10. Consultas de clientes, picos estacionales

    # ========== TIER 2 - ALTA PROBABILIDAD (servicios + agenda de turnos) ==========
    "aseguradoras",                         # 11. Cotizaciones automáticas, leads constantes
    "gimnasios",                            # 12. Membresías, horarios de clases, promos
    "agencias de viajes",                   # 13. Consultas de viajes a toda hora
    "spa y centros de bienestar",           # 14. Turnos, paquetes, disponibilidad
    "veterinarias",                         # 15. Turnos, urgencias, consultas
    "constructoras",                        # 16. Presupuestos, consultas de obra
    "psicologos y terapeutas",             # 17. Agendar sesiones, privacidad en consultas
    "estudios de arquitectura",             # 18. Consultas de proyecto, presupuestos
    "academias e institutos de idiomas",    # 19. Inscripciones, niveles, horarios
    "centros de capacitacion",              # 20. Cursos, inscripciones, cronogramas

    # ========== TIER 3 - BUENA PROBABILIDAD (eventos + reservas + consultas) ==========
    "salones de fiestas y eventos",         # 21. Disponibilidad, presupuestos, visitas
    "fotografos profesionales",             # 22. Reservar sesiones, portafolio
    "empresas de seguridad",                # 23. Cotización de servicios de monitoreo
    "consultoras",                          # 24. Captación de leads, agendar reuniones
    "restaurantes",                         # 25. Reservas de mesa, menú, eventos
    "rent a car",                           # 26. Disponibilidad, reservas, precios
    "nutricionistas",                       # 27. Turnos, planes, consultas
    "kinesiologos y fisioterapeutas",       # 28. Turnos de rehabilitación
    "catering",                             # 29. Presupuestos de eventos, menús
    "organizadores de eventos",             # 30. Consultas, disponibilidad, cotización

    # ========== TIER 4 - PROBABILIDAD MEDIA-ALTA (comercio + servicios) ==========
    "empresas de software",                 # 31. Tech-savvy, demos, onboarding
    "cabañas y alojamientos turisticos",    # 32. Reservas, disponibilidad, temporadas
    "peluquerias y barberias",              # 33. Turnos, servicios, precios
    "empresas de limpieza",                 # 34. Cotización de servicios
    "decoracion y diseño de interiores",    # 35. Consultas de proyecto, presupuestos
    "opticas",                              # 36. Turnos, stock de lentes
    "productoras audiovisuales",            # 37. Consultas de producción, presupuestos
    "agencias de publicidad",               # 38. Captación de leads, servicios
    "mueblerias",                           # 39. Consultas de productos, delivery
    "joyerias",                             # 40. Alto ticket, consultas, encargos
    "farmacias",                            # 41. Disponibilidad, turnos de vacunación
    "floristerias",                         # 42. Pedidos, delivery, disponibilidad
    "escuelas de musica y arte",            # 43. Inscripciones, horarios
    "empresas de mudanzas",                 # 44. Cotizaciones, agendamiento
    "laboratorios de analisis clinicos",    # 45. Turnos, preparación, resultados
]

# is_business_hours() imported from src.utils.timezone (handles DST correctly)

# =============================================================================
# LOGGER
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# =============================================================================
# IMPORTAR BASE DE DATOS DE CIUDADES (2,000+ ciudades)
# =============================================================================
# Debe ir después de definir log para no provocar NameError al iniciar el worker
try:
    from cities_data import CIUDADES_POR_PAIS, PAISES, TOTAL_CIUDADES, TOTAL_PAISES, CITY_COORDINATES
    log.info(f"✅ Base de ciudades cargada: {TOTAL_PAISES} países, {TOTAL_CIUDADES} ciudades, {len(CITY_COORDINATES)} con GPS")
except ImportError:
    log.warning("⚠️  cities_data.py no encontrado, usando lista reducida")
    CIUDADES_POR_PAIS = {
        "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza"],
        "México": ["Ciudad de México", "Guadalajara", "Monterrey"],
        "Colombia": ["Bogotá", "Medellín", "Cali"],
    }
    PAISES = list(CIUDADES_POR_PAIS.keys())
    TOTAL_CIUDADES = sum(len(c) for c in CIUDADES_POR_PAIS.values())
    TOTAL_PAISES = len(PAISES)
    CITY_COORDINATES = {}

# =============================================================================
# DOMAIN HUNTER WORKER
# =============================================================================

class DomainHunterWorker:
    """Worker daemon optimizado v8 que busca dominios en Google + Maps 24/7."""
    
    def __init__(self):
        """Inicializa el worker."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self._key_rotator = SerpApiKeyRotator()
        self.active_users: Dict[str, dict] = {}
        # v8: cache de dominios por usuario (evita cross-contamination entre usuarios)
        self._user_domains_cache: Dict[str, Set[str]] = {}
        # Resilience
        self._error_streak = 0
        # Credit management
        self._searches_since_credit_check = 0
        self._cached_credits_left: Optional[int] = None
        # Semaphore for parallel user processing
        self._user_semaphore = asyncio.Semaphore(BotConfig.MAX_CONCURRENT_USERS)
        # v8: cache de related searches (sugerencias gratuitas de Google)
        self._related_queries_cache: List[str] = []
        # v8: cache cross-user de resultados de búsqueda {query_hash: (domains, timestamp)}
        self._search_results_cache: Dict[str, tuple] = {}
        
    async def start(self):
        """Inicia el worker daemon."""
        log.info("=" * 70)
        log.info("🔍 DOMAIN HUNTER WORKER v8 - Iniciando")
        log.info("=" * 70)
        
        # Fingerprint compacto
        _bh = is_business_hours()
        log.info(
            f"🔖 v8 | {format_argentina_time()} | "
            f"Horario: {BUSINESS_HOURS_START}-{BUSINESS_HOURS_END}h | "
            f"{'ACTIVO' if _bh else 'PAUSADO'} | "
            f"{TOTAL_PAISES} países, {TOTAL_CIUDADES} ciudades, {len(NICHOS)} nichos | "
            f"Secuencia: {len(SEARCH_SEQUENCE)} búsquedas/combo (web+maps) | "
            f"Keys: {self._key_rotator.total_keys}"
        )
        
        # Test de conectividad
        if not await self._test_connectivity():
            return
        
        log.info("✅ Servicios conectados — iniciando loop principal")
        
        try:
            await self._main_loop()
        except KeyboardInterrupt:
            log.info("⚠️  Detenido por el usuario")
        finally:
            log.info("✅ Worker cerrado correctamente")
    
    async def _test_connectivity(self) -> bool:
        """Verifica conectividad con Supabase y SerpAPI. Retorna True si OK."""
        # Test Supabase
        try:
            test = self.supabase.table("hunter_configs").select("user_id").limit(1).execute()
            log.info(f"✅ Supabase OK ({len(test.data)} registros)")
        except Exception as e:
            log.error(f"❌ Supabase ERROR: {e}")
            return False
        
        # Test SerpAPI — verificar créditos de todas las keys
        all_credits = await self._key_rotator.check_all_credits()
        total = sum(v for v in all_credits.values() if v >= 0)
        if total <= 0:
            log.error("❌ SerpAPI ERROR: ninguna key tiene créditos disponibles")
            return False
        
        return True
    
    async def _check_remaining_credits(self) -> Optional[int]:
        """Verifica créditos de la key activa via KeyRotator (auto-rota si agotada)."""
        credits = await self._key_rotator.check_credits()
        self._searches_since_credit_check = 0
        if credits is not None:
            self._cached_credits_left = credits
        return credits
    
    def _get_sent_count(self) -> int:
        """Emails enviados solo en dominios warm-up (warmup-*). Para límite warm-up."""
        try:
            response = self.supabase.table("leads")\
                .select("id", count="exact")\
                .eq("status", "sent")\
                .like("domain", "warmup-%")\
                .execute()
            return response.count or 0
        except Exception as e:
            log.error(f"❌ Error obteniendo sent_count: {e}")
            return 0
    
    async def _main_loop(self):
        """Loop principal del worker con procesamiento paralelo de usuarios."""
        while True:
            try:
                await self._update_active_users()
                
                if not self.active_users:
                    log.info(f"😴 Sin usuarios activos. Revisando en {CHECK_USERS_INTERVAL}s")
                    await asyncio.sleep(CHECK_USERS_INTERVAL)
                    continue
                
                # Pre-check de créditos periódico
                if self._searches_since_credit_check >= BotConfig.CREDIT_CHECK_INTERVAL:
                    credits = await self._check_remaining_credits()
                    if credits is not None and credits < BotConfig.CREDIT_RESERVE_MIN:
                        log.warning(f"⚠️  Solo {credits} créditos restantes. Pausando {BotConfig.CREDIT_PAUSE_SECONDS}s")
                        await asyncio.sleep(BotConfig.CREDIT_PAUSE_SECONDS)
                        continue
                
                log.info(f"🔄 Procesando {len(self.active_users)} usuario(s) | {format_argentina_time()}")
                log.info(self._key_rotator.get_stats())
                
                # Procesar usuarios en paralelo con semáforo
                tasks = [
                    self._process_user_safe(uid, cfg)
                    for uid, cfg in self.active_users.items()
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log de errores de tareas fallidas
                for uid, result in zip(self.active_users.keys(), results):
                    if isinstance(result, Exception):
                        log.error(f"❌ Error procesando {uid[:8]}: {result}")
                
                self._error_streak = 0
                await asyncio.sleep(CHECK_USERS_INTERVAL)
                
            except Exception as e:
                self._error_streak += 1
                backoff = min(BotConfig.ERROR_BACKOFF_BASE * (2 ** min(self._error_streak, 5)),
                              BotConfig.ERROR_BACKOFF_MAX)
                log.error(f"❌ Error en loop (streak {self._error_streak}): {e}")
                await asyncio.sleep(backoff)
    
    async def _process_user_safe(self, user_id: str, config: dict):
        """Procesa un usuario con semáforo. Búsquedas 24/7 sin límite diario."""
        async with self._user_semaphore:
            domains = await self._search_domains_for_user(user_id, config)
            
            if domains:
                await self._save_domains_to_supabase(user_id, domains)
                await self._log_to_user(
                    user_id=user_id, level="success", action="domain_added",
                    domain="system",
                    message=f"✅ {len(domains)} dominios nuevos agregados a la cola"
                )
                self._searches_since_credit_check += 1
                
                delay = random.randint(MIN_DELAY_BETWEEN_SEARCHES, MAX_DELAY_BETWEEN_SEARCHES)
                await asyncio.sleep(delay)
    
    async def _update_active_users(self):
        """Obtiene usuarios con bot habilitado desde Supabase."""
        try:
            response = self.supabase.table("hunter_configs")\
                .select("*")\
                .eq("bot_enabled", True)\
                .execute()
            
            self.active_users = {c['user_id']: c for c in response.data}
            
            if self.active_users:
                users_summary = ", ".join(
                    f"{uid[:8]}({c.get('nicho', '?')})"
                    for uid, c in self.active_users.items()
                )
                log.info(f"👥 {len(self.active_users)} activo(s): {users_summary}")
        except Exception as e:
            log.error(f"❌ Error obteniendo usuarios: {e}")
    
    async def _search_domains_for_user(self, user_id: str, config: dict) -> List[str]:
        """
        Busca dominios con alternancia Web/Maps y extracción multi-source v7.
        
        Secuencia por combinación (cada paso = 1 crédito):
        - Páginas pares: Web search con template diferente
        - Páginas impares: Google Maps search (20+ negocios/crédito)
        """
        tracking = await self._get_next_combination_to_search(user_id)
        if not tracking:
            return []
        
        nicho = tracking['nicho']
        ciudad = tracking['ciudad']
        pais = tracking['pais']
        current_page = tracking['current_page']
        
        # Determinar tipo de búsqueda según la secuencia v8 (tipo, template, start)
        seq_idx = current_page % len(SEARCH_SEQUENCE)
        search_type, template_idx, start_offset = SEARCH_SEQUENCE[seq_idx]
        
        gl_code = PAIS_GL_CODE.get(pais, pais[:2].lower())
        
        try:
            if search_type == "maps":
                domains_found = await self._search_via_maps(
                    user_id, nicho, ciudad, pais, gl_code, template_idx, start_offset
                )
                log.info(
                    f"[{user_id[:8]}] 🗺️  Maps T{template_idx} S{start_offset} | {nicho} | {ciudad},{pais} | "
                    f"P{current_page} | {len(domains_found)} dominios"
                )
            else:
                domains_found = await self._search_via_web(
                    user_id, nicho, ciudad, pais, gl_code, template_idx, start_offset
                )
                log.info(
                    f"[{user_id[:8]}] 🌐 Web T{template_idx} S{start_offset} | {nicho} | {ciudad},{pais} | "
                    f"P{current_page} | {len(domains_found)} dominios"
                )
            
            # v8: cache per-user para evaluar % nuevos sin cross-contamination
            user_cache = self._user_domains_cache.setdefault(user_id, set())
            truly_new = domains_found - user_cache
            new_ratio = len(truly_new) / len(domains_found) if domains_found else 0
            
            user_cache.update(domains_found)
            if len(user_cache) > BotConfig.SESSION_CACHE_MAX_SIZE:
                # Mantener solo los últimos encontrados
                user_cache.clear()
                user_cache.update(domains_found)
            
            log.info(
                f"[{user_id[:8]}] 📈 {len(truly_new)}/{len(domains_found)} nuevos ({new_ratio:.0%}) | "
                f"Cache[{user_id[:8]}]: {len(user_cache)}"
            )
            
            # Lógica de agotamiento inteligente
            await self._handle_pagination_logic(
                user_id, nicho, ciudad, pais, current_page,
                len(domains_found), new_ratio, seq_idx
            )
            
            # v8: retornar solo dominios nuevos (reduce tráfico de red al upsert)
            return list(truly_new) if truly_new else list(domains_found)
            
        except Exception as e:
            log.error(f"[{user_id[:8]}] ❌ Error búsqueda: {e}")
            log.error(traceback.format_exc())
            return []
    
    # =============================================================================
    # v8: CACHE CROSS-USER — Reusar resultados de queries recientes
    # Si otro usuario (o el mismo) ya hizo la misma query en las últimas 24h,
    # reusar los dominios encontrados sin gastar otro crédito.
    # =============================================================================
    
    _CACHE_TTL_SECONDS = 86400  # 24 horas
    _CACHE_MAX_ENTRIES = 1000
    
    def _cache_key(self, search_type: str, query: str, start: int) -> str:
        """Genera key de cache determinístico para una query."""
        raw = f"{search_type}:{query}:{start}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def _cache_get(self, key: str) -> Optional[Set[str]]:
        """Busca en cache cross-user. Retorna dominios si hay hit válido."""
        entry = self._search_results_cache.get(key)
        if entry is None:
            return None
        domains, ts = entry
        if time.time() - ts > self._CACHE_TTL_SECONDS:
            del self._search_results_cache[key]
            return None
        return domains
    
    def _cache_put(self, key: str, domains: Set[str]) -> None:
        """Almacena resultados en cache cross-user."""
        # Limpiar entradas viejas si el cache está lleno
        if len(self._search_results_cache) >= self._CACHE_MAX_ENTRIES:
            now = time.time()
            expired = [k for k, (_, ts) in self._search_results_cache.items()
                       if now - ts > self._CACHE_TTL_SECONDS]
            for k in expired:
                del self._search_results_cache[k]
            # Si aún está lleno, eliminar el 25% más viejo
            if len(self._search_results_cache) >= self._CACHE_MAX_ENTRIES:
                sorted_keys = sorted(self._search_results_cache.keys(),
                                     key=lambda k: self._search_results_cache[k][1])
                for k in sorted_keys[:len(sorted_keys) // 4]:
                    del self._search_results_cache[k]
        
        self._search_results_cache[key] = (domains, time.time())

    async def _search_via_web(self, user_id: str, nicho: str, ciudad: str, pais: str,
                              gl_code: str, template_idx: int,
                              start: int = 0) -> Set[str]:
        """Búsqueda web con extracción multi-source de 7 fuentes.
        
        v8: query limpia sin -site: exclusions (filtrado post-extraction),
        num=100 (máximo absoluto, mismo costo por crédito), 15 fuentes de extracción,
        cache cross-user para evitar gastar créditos en queries repetidas.
        """
        template = QUERY_TEMPLATES_WEB[template_idx % len(QUERY_TEMPLATES_WEB)]
        query = template.format(nicho=nicho, ciudad=ciudad)
        
        # v8: verificar cache cross-user antes de gastar crédito
        cache_key = self._cache_key("web", query, start)
        cached = self._cache_get(cache_key)
        if cached is not None:
            log.info(f"  💾 Cache hit web: {len(cached)} dominios (0 créditos)")
            return cached
        
        active_key = await self._key_rotator.get_key()
        params = {
            "q": query,
            "location": f"{ciudad}, {pais}",
            "hl": "es",
            "gl": gl_code,
            "num": 100,
            "start": start,
            "filter": 0,
            "nfpr": 1,
            "api_key": active_key
        }
        
        search_obj = GoogleSearch(params)
        try:
            search = await asyncio.wait_for(
                asyncio.to_thread(search_obj.get_dict),
                timeout=BotConfig.SERPAPI_TIMEOUT
            )
            await self._key_rotator.report_success()
        except asyncio.TimeoutError:
            log.error(f"❌ SerpAPI timeout ({BotConfig.SERPAPI_TIMEOUT}s)")
            await self._key_rotator.report_error("timeout")
            return set()
        except Exception as e:
            await self._key_rotator.report_error(str(e))
            raise
        
        domains = self._extract_domains_from_web_response(search)
        await self._save_empresas_sin_dominio_from_web(search, user_id, nicho, ciudad, pais)
        
        # v8: almacenar en cache cross-user
        if domains:
            self._cache_put(cache_key, domains)
        
        # v8: extraer related_searches como sugerencias gratuitas (ya vienen en la respuesta)
        self._harvest_related_searches(search)
        
        return domains
    
    async def _search_via_maps(self, user_id: str, nicho: str, ciudad: str, pais: str,
                               gl_code: str, template_idx: int,
                               start: int = 0) -> Set[str]:
        """Búsqueda en Google Maps — devuelve 20+ negocios con website directo.
        
        v8: soporte de paginación extendida (start=0/20/40/60) para extraer
        hasta 80 negocios por query. Cache cross-user incluido.
        En paralelo guarda negocios sin website en empresas_sin_dominio.
        """
        template = QUERY_TEMPLATES_MAPS[template_idx % len(QUERY_TEMPLATES_MAPS)]
        query = template.format(nicho=nicho, ciudad=ciudad)
        
        # v8: verificar cache cross-user antes de gastar crédito
        cache_key = self._cache_key("maps", query, start)
        cached = self._cache_get(cache_key)
        if cached is not None:
            log.info(f"  💾 Cache hit maps: {len(cached)} dominios (0 créditos)")
            return cached
        
        active_key = await self._key_rotator.get_key()
        params = {
            "engine": "google_maps",
            "q": query,
            "hl": "es",
            "type": "search",
            "api_key": active_key
        }
        
        # Usar coordenadas GPS si disponibles, sino location text
        coords = CITY_COORDINATES.get(ciudad)
        if coords:
            params["ll"] = f"@{coords},12z"
        else:
            params["ll"] = None  # Dejar que SerpAPI geocodifique
            params["location"] = f"{ciudad}, {pais}"
        
        # Limpiar None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # v8: paginación controlada desde SEARCH_SEQUENCE
        if start > 0:
            params["start"] = start
        
        search_obj = GoogleSearch(params)
        try:
            search = await asyncio.wait_for(
                asyncio.to_thread(search_obj.get_dict),
                timeout=BotConfig.SERPAPI_TIMEOUT
            )
            await self._key_rotator.report_success()
        except asyncio.TimeoutError:
            log.error(f"❌ Maps timeout ({BotConfig.SERPAPI_TIMEOUT}s)")
            await self._key_rotator.report_error("timeout")
            return set()
        except Exception as e:
            await self._key_rotator.report_error(str(e))
            raise
        
        domains = self._extract_domains_from_maps_response(search)
        await self._save_empresas_sin_dominio_from_maps(search, user_id, nicho, ciudad, pais)
        
        # v8: almacenar en cache cross-user
        if domains:
            self._cache_put(cache_key, domains)
        
        return domains
    
    _SNIPPET_URL_RE = re.compile(
        r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]{1,61}\.(?:com|net|org|info|biz|co|io|app|dev'
        r'|com\.ar|com\.mx|com\.co|com\.pe|com\.br|com\.uy|com\.cl|com\.ec|com\.ve|com\.bo|com\.py'
        r'|cl|mx|ar|co|pe|br|uy|ec|ve|bo|py))\b'
    )

    def _add_domain(self, domains: set, counts: dict, source: str, url: str) -> None:
        """Helper: extrae dominio de url, valida y agrega al set."""
        d = self._extract_domain(url)
        if d and self._is_valid_domain(d):
            domains.add(d)
            counts[source] = counts.get(source, 0) + 1

    def _extract_domains_from_snippet(self, text: str) -> Set[str]:
        """Extrae dominios mencionados en texto plano (snippets, descripciones)."""
        found = set()
        if not text:
            return found
        for match in self._SNIPPET_URL_RE.finditer(text):
            d = match.group(1).lower()
            if self._is_valid_domain(d):
                found.add(d)
        return found

    def _extract_domains_from_web_response(self, search: dict) -> Set[str]:
        """Extrae dominios de 15+ fuentes en una respuesta web de SerpAPI.
        
        Maximiza dominios por crédito extrayendo de TODAS las secciones
        que SerpAPI devuelve en una sola respuesta.
        """
        domains = set()
        counts: dict = {}
        
        # SOURCE 1: Resultados orgánicos (hasta 40 con num=40)
        for result in search.get("organic_results", []):
            link = result.get("link")
            if link:
                self._add_domain(domains, counts, "organic", link)
            
            displayed = result.get("displayed_link", "")
            if displayed and displayed != link:
                if "›" in displayed:
                    displayed = displayed.replace(" › ", "/").replace("›", "/")
                if not displayed.startswith("http"):
                    displayed = "https://" + displayed
                self._add_domain(domains, counts, "organic", displayed)
            
            # Dominios mencionados en snippets
            snippet = result.get("snippet", "")
            for sd in self._extract_domains_from_snippet(snippet):
                domains.add(sd)
                counts["snippet"] = counts.get("snippet", 0) + 1
            
            # Rich snippet con links
            rich = result.get("rich_snippet", {})
            if isinstance(rich, dict):
                for _key, val in rich.items():
                    if isinstance(val, dict):
                        for v in val.values():
                            if isinstance(v, str) and '.' in v:
                                for sd in self._extract_domains_from_snippet(v):
                                    domains.add(sd)
                                    counts["snippet"] = counts.get("snippet", 0) + 1
            
            # Sitelinks (inline + expanded)
            sitelinks = result.get("sitelinks", {})
            for group in [sitelinks.get("inline", []), sitelinks.get("expanded", [])]:
                for sl in group:
                    sl_link = sl.get("link")
                    if sl_link:
                        self._add_domain(domains, counts, "sitelinks", sl_link)
            
            # Source info
            source_info = result.get("source", {})
            if isinstance(source_info, dict):
                src_link = source_info.get("link") or source_info.get("url", "")
                if src_link:
                    self._add_domain(domains, counts, "organic", src_link)
        
        # SOURCE 2: Local Results (Google Maps pack)
        local_results = search.get("local_results", [])
        if isinstance(local_results, dict):
            local_results = local_results.get("places", local_results.get("results", []))
        for local in local_results:
            if not isinstance(local, dict):
                continue
            for field in ("website", "link"):
                val = local.get(field)
                if val:
                    self._add_domain(domains, counts, "local", val)
        
        # SOURCE 3: Knowledge Graph (completo)
        kg = search.get("knowledge_graph", {})
        if isinstance(kg, dict):
            kg_web = kg.get("website")
            if kg_web:
                self._add_domain(domains, counts, "kg", kg_web)
            # KG profiles (redes sociales NO, pero websites de socios/competidores SÍ)
            for profile in kg.get("profiles", []):
                if isinstance(profile, dict):
                    p_link = profile.get("link", "")
                    if p_link:
                        self._add_domain(domains, counts, "kg", p_link)
            # KG known attributes con links
            for attr_key in ("source", "header_images", "local_results"):
                attr_val = kg.get(attr_key)
                if isinstance(attr_val, dict):
                    for v in attr_val.values():
                        if isinstance(v, str) and v.startswith("http"):
                            self._add_domain(domains, counts, "kg", v)
                elif isinstance(attr_val, list):
                    for item in attr_val:
                        if isinstance(item, dict):
                            for v in item.values():
                                if isinstance(v, str) and v.startswith("http"):
                                    self._add_domain(domains, counts, "kg", v)
        
        # SOURCE 4: Related Results
        for rel in search.get("related_results", []):
            if isinstance(rel, dict) and rel.get("link"):
                self._add_domain(domains, counts, "related", rel["link"])
        
        # SOURCE 5: Ads (negocios reales con presupuesto publicitario)
        for ad in search.get("ads", []):
            if not isinstance(ad, dict):
                continue
            for field in ("link", "tracking_link", "displayed_link"):
                val = ad.get(field, "")
                if val:
                    if "›" in val:
                        val = val.replace(" › ", "/").replace("›", "/")
                    if not val.startswith("http"):
                        val = "https://" + val
                    self._add_domain(domains, counts, "ads", val)
            # Sitelinks de ads
            for sl in ad.get("sitelinks", []):
                if isinstance(sl, dict) and sl.get("link"):
                    self._add_domain(domains, counts, "ads", sl["link"])
        
        # SOURCE 6: Places Results (Maps embebido en web search)
        for place in search.get("places_results", []):
            if isinstance(place, dict):
                for field in ("website", "link"):
                    val = place.get(field, "")
                    if val:
                        self._add_domain(domains, counts, "places", val)
        
        # SOURCE 7: Answer Box / Featured Snippet
        answer = search.get("answer_box", {})
        if isinstance(answer, dict):
            for field in ("link", "displayed_link", "result"):
                val = answer.get(field, "")
                if val:
                    if isinstance(val, str) and (val.startswith("http") or '.' in val):
                        if "›" in val:
                            val = val.replace(" › ", "/").replace("›", "/")
                        if not val.startswith("http"):
                            val = "https://" + val
                        self._add_domain(domains, counts, "answer", val)
            # Snippet text de answer box
            for sd in self._extract_domains_from_snippet(answer.get("snippet", "")):
                domains.add(sd)
                counts["snippet"] = counts.get("snippet", 0) + 1
        
        # SOURCE 8: Top Stories / News Results
        for key in ("top_stories", "news_results"):
            for story in search.get(key, []):
                if isinstance(story, dict) and story.get("link"):
                    self._add_domain(domains, counts, "news", story["link"])
        
        # SOURCE 9: Inline Videos
        for video in search.get("inline_videos", []):
            if isinstance(video, dict) and video.get("link"):
                self._add_domain(domains, counts, "videos", video["link"])
        
        # SOURCE 10: Related Questions ("People also ask")
        for ppl in search.get("related_questions", []):
            if isinstance(ppl, dict):
                if ppl.get("link"):
                    self._add_domain(domains, counts, "questions", ppl["link"])
                for sd in self._extract_domains_from_snippet(ppl.get("snippet", "")):
                    domains.add(sd)
                    counts["snippet"] = counts.get("snippet", 0) + 1
        
        # SOURCE 11: Inline Shopping
        for item in search.get("inline_shopping", search.get("shopping_results", [])):
            if isinstance(item, dict):
                for field in ("link", "source"):
                    val = item.get(field, "")
                    if val and val.startswith("http"):
                        self._add_domain(domains, counts, "shopping", val)
        
        # SOURCE 12: Inline Images (links de origen)
        for img in search.get("inline_images", []):
            if isinstance(img, dict) and img.get("source"):
                self._add_domain(domains, counts, "images", img["source"])
        
        # SOURCE 13: Events Results
        for event in search.get("events_results", []):
            if isinstance(event, dict) and event.get("link"):
                self._add_domain(domains, counts, "events", event["link"])
        
        # SOURCE 14: Jobs Results (empresas que contratan = tienen web)
        for job in search.get("jobs_results", []):
            if isinstance(job, dict):
                for field in ("link", "company_link"):
                    val = job.get(field, "")
                    if val:
                        self._add_domain(domains, counts, "jobs", val)
        
        # SOURCE 15: Twitter/X Results (links a negocios en posts)
        for tw in search.get("twitter_results", []):
            if isinstance(tw, dict) and tw.get("link"):
                self._add_domain(domains, counts, "twitter", tw["link"])
        
        active_sources = {k: v for k, v in counts.items() if v > 0}
        log.info(f"  📊 Web extraction: {active_sources} = {len(domains)} únicos")
        
        return domains
    
    def _extract_domains_from_maps_response(self, search: dict) -> Set[str]:
        """Extrae dominios de respuesta de Google Maps API."""
        domains = set()
        total = 0
        
        local_results = search.get("local_results", [])
        if isinstance(local_results, dict):
            local_results = local_results.get("places", [])
        for result in local_results:
            if not isinstance(result, dict):
                continue
            website = result.get("website")
            if website:
                d = self._extract_domain(website)
                if d and self._is_valid_domain(d):
                    domains.add(d)
                    total += 1
        
        log.info(f"  🗺️  Maps extraction: {total} con website → {len(domains)} únicos válidos")
        return domains

    async def _save_empresas_sin_dominio_from_maps(
        self, search: dict, user_id: str, nicho: str, ciudad: str, pais: str
    ) -> None:
        """Extrae negocios SIN website de la respuesta Maps, verifica y guarda."""
        local_results = search.get("local_results", [])
        if isinstance(local_results, dict):
            local_results = local_results.get("places", [])
        candidates = []
        for result in local_results:
            if not isinstance(result, dict):
                continue
            if result.get("website"):
                continue
            title = (result.get("title") or "").strip()
            if not title or len(title) < 2:
                continue
            address = (result.get("address") or "").strip() or None
            phone = (result.get("phone") or "").strip() or None
            type_raw = result.get("type") or result.get("type_id") or ""
            types_list = result.get("types") or result.get("type_ids") or []
            if isinstance(types_list, str):
                types_list = [types_list]
            clasif = _clasificar_negocio(type_raw, types_list)
            type_str = type_raw if isinstance(type_raw, str) else str(types_list[:1] if types_list else "")
            candidates.append({
                "user_id": user_id,
                "nombre": title[:500],
                "direccion": address[:500] if address else None,
                "telefono": phone[:100] if phone else None,
                "ciudad": ciudad[:200],
                "pais": pais[:200],
                "nicho": nicho[:200] if nicho else None,
                "source": "hunter",
                "clasificacion": clasif,
                "type_raw": type_str[:200] if type_str else None,
            })
        if not candidates:
            return

        verify_key = await self._key_rotator.get_key()
        verified = await _batch_verify_no_web(verify_key, candidates)
        saved = 0
        skipped_has_web = 0
        for row in verified:
            if row.get("verification_status") == "has_web":
                skipped_has_web += 1
                continue
            if (STRICT_NO_WEB_CHECK
                    and row.get("verification_status") == "verified_no_web"
                    and row.get("confidence_no_web", 0) < STRICT_NO_WEB_MIN_CONFIDENCE):
                skipped_has_web += 1
                continue
            try:
                self.supabase.table("empresas_sin_dominio").insert(row).execute()
                saved += 1
            except Exception as e:
                if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                    log.warning(f"  ⚠️ empresas_sin_dominio Maps: {str(e)[:80]}")
        if saved or skipped_has_web:
            log.info(
                f"  📋 empresas_sin_dominio Maps: {saved} guardados, "
                f"{skipped_has_web} descartados (tienen web) de {len(candidates)} candidatos"
            )

    async def _save_empresas_sin_dominio_from_web(
        self, search: dict, user_id: str, nicho: str, ciudad: str, pais: str
    ) -> None:
        """Extrae negocios SIN website de local_results y places_results (web), verifica y guarda."""
        candidates = []
        def add_place(place: dict) -> None:
            if not isinstance(place, dict) or (place.get("website") or place.get("link")):
                return
            title = (place.get("title") or "").strip()
            if not title or len(title) < 2:
                return
            candidates.append({
                "user_id": user_id,
                "nombre": title[:500],
                "direccion": (place.get("address") or "").strip()[:500] or None,
                "telefono": (place.get("phone") or "").strip()[:100] or None,
                "ciudad": ciudad[:200],
                "pais": pais[:200],
                "nicho": nicho[:200] if nicho else None,
                "source": "hunter",
                "clasificacion": _clasificar_negocio(place.get("type"), place.get("types") or []),
                "type_raw": (str(place.get("type") or "")[:200]) or None,
            })
        lr = search.get("local_results")
        if isinstance(lr, list):
            for local in lr:
                add_place(local)
        elif isinstance(lr, dict):
            for place in (lr.get("places") or []):
                add_place(place)
        for place in search.get("places_results", []) or []:
            add_place(place)
        if not candidates:
            return

        verify_key = await self._key_rotator.get_key()
        verified = await _batch_verify_no_web(verify_key, candidates)
        saved = 0
        skipped_has_web = 0
        for row in verified:
            if row.get("verification_status") == "has_web":
                skipped_has_web += 1
                continue
            if (STRICT_NO_WEB_CHECK
                    and row.get("verification_status") == "verified_no_web"
                    and row.get("confidence_no_web", 0) < STRICT_NO_WEB_MIN_CONFIDENCE):
                skipped_has_web += 1
                continue
            try:
                self.supabase.table("empresas_sin_dominio").insert(row).execute()
                saved += 1
            except Exception as e:
                if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                    log.warning(f"  ⚠️ empresas_sin_dominio Web: {str(e)[:80]}")
        if saved or skipped_has_web:
            log.info(
                f"  📋 empresas_sin_dominio Web: {saved} guardados, "
                f"{skipped_has_web} descartados (tienen web) de {len(candidates)} candidatos"
            )
    
    def _harvest_related_searches(self, search: dict) -> None:
        """Extrae related_searches de la respuesta de SerpAPI.
        
        v8: Las related_searches vienen gratis en cada respuesta web de Google.
        Se almacenan para potencial uso futuro como queries adicionales.
        No gastan créditos extras — es información gratuita.
        """
        related = search.get("related_searches", [])
        if not related:
            return
        
        queries = []
        for item in related:
            query_text = item.get("query")
            if query_text:
                queries.append(query_text)
        
        if queries:
            # Almacenar en cache de sugerencias (limitado para no explotar memoria)
            if not hasattr(self, '_related_queries_cache'):
                self._related_queries_cache: List[str] = []
            
            new_queries = [q for q in queries if q not in self._related_queries_cache]
            self._related_queries_cache.extend(new_queries)
            
            # Limitar a 500 sugerencias en memoria
            if len(self._related_queries_cache) > 500:
                self._related_queries_cache = self._related_queries_cache[-250:]
            
            if new_queries:
                log.info(f"  🔗 +{len(new_queries)} related searches capturadas (total: {len(self._related_queries_cache)})")

    async def _handle_pagination_logic(self, user_id: str, nicho: str, ciudad: str,
                                        pais: str, current_page: int,
                                        domains_count: int, new_ratio: float,
                                        seq_idx: int):
        """Lógica de agotamiento inteligente unificada."""
        if domains_count == 0:
            if current_page < MAX_PAGES_PER_COMBINATION - 1:
                await self._increment_page(user_id, nicho, ciudad, pais, 0)
            else:
                await self._mark_combination_exhausted(user_id, nicho, ciudad, pais)
        elif current_page >= MAX_PAGES_PER_COMBINATION - 1:
            await self._mark_combination_exhausted(user_id, nicho, ciudad, pais)
        elif new_ratio < MIN_NEW_RATIO_FOR_PAGINATION and current_page >= 2:
            await self._mark_combination_exhausted(user_id, nicho, ciudad, pais)
            log.info(f"[{user_id[:8]}] 🏁 Rendimiento bajo ({new_ratio:.0%}), rotando combinación")
        else:
            await self._increment_page(user_id, nicho, ciudad, pais, domains_count)
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extrae el dominio base de una URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.lower().strip()
            if domain.startswith('www.'):
                domain = domain[4:]
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain if domain else None
        except Exception:
            return None
    
    def _is_valid_domain(self, domain: str) -> bool:
        """
        Valida dominio de negocio real. Blacklist O(1) optimizada v7.
        
        Pipeline: formato → blacklist (O(1)) → TLD → plataformas → spam → directorios
        """
        if not domain or len(domain) < 4:
            return False
        
        domain_lower = domain.lower().strip()
        
        # ── 1. FORMATO BÁSICO ──────────────────────────────────────────────
        if domain_lower.startswith('/') or '/maps/' in domain_lower:
            return False
        
        # v8: usa constante de módulo (antes se creaba frozenset en cada llamada)
        if INVALID_DOMAIN_CHARS & set(domain):
            return False
        
        if '.' not in domain_lower or '@' in domain_lower:
            return False
        
        parts = domain_lower.split('.')
        if len(parts) < 2 or len(parts) > 4:
            return False
        
        name_part = parts[0]
        if len(name_part) < 3:
            return False
        
        # ── 2. BLACKLIST O(1) ──────────────────────────────────────────────
        
        # Ejemplo/prueba fast check (v8: usa constante de módulo)
        if any(w in domain_lower for w in EXAMPLE_DOMAIN_WORDS):
            return False
        
        # Suffix blacklist: O(|BLACKLIST_SUFFIXES|) pero set is small and endswith is fast
        for suffix in BLACKLIST_SUFFIXES:
            if domain_lower.endswith(suffix) or domain_lower.endswith('.' + suffix):
                return False
        
        # Name part blacklist: O(1) set intersection
        name_tokens = set(name_part.split('-'))
        name_tokens.add(name_part)  # Also check full name
        if BLACKLIST_NAME_PARTS & name_tokens:
            return False
        
        # Extensiones gubernamentales
        for gov_tld in GOVERNMENT_TLD:
            if gov_tld in domain_lower:
                return False
        
        # ── 3. TLD VÁLIDO ──────────────────────────────────────────────────
        if not any(domain_lower.endswith(tld) for tld in VALID_BUSINESS_TLDS):
            return False
        
        # ── 4. PLATAFORMAS GRATUITAS ───────────────────────────────────────
        for suffix in FREE_PLATFORM_SUFFIXES:
            if domain_lower.endswith(suffix):
                return False
        
        # ── 5. DETECCIÓN DE SPAM ───────────────────────────────────────────
        if len(domain_lower) > 60 or len(name_part) > 30:
            return False
        
        if name_part.count('-') > 3:
            return False
        
        if name_part.startswith('-') or name_part.endswith('-'):
            return False
        
        name_clean = name_part.replace('-', '')
        if name_clean.isdigit():
            return False
        
        digit_count = sum(1 for c in name_part if c.isdigit())
        if len(name_part) > 5 and digit_count / len(name_part) > 0.5:
            return False
        
        # ── 6. DIRECTORIOS / AGREGADORES (v8: usa constante de módulo) ─────
        for pattern in DIRECTORY_PATTERNS:
            if pattern in name_part:
                return False
        
        return True
    
    async def _save_domains_to_supabase(self, user_id: str, domains: List[str]):
        """Guarda dominios nuevos en la tabla leads (upsert con ignore_duplicates)."""
        try:
            leads_data = [
                {'user_id': user_id, 'domain': domain, 'status': 'pending'}
                for domain in domains
            ]
            self.supabase.table("leads").upsert(
                leads_data,
                on_conflict='user_id,domain',
                ignore_duplicates=True,
            ).execute()
            log.info(f"[{user_id[:8]}] 💾 {len(domains)} dominios → cola")
        except Exception as e:
            log.error(f"[{user_id[:8]}] ❌ Error guardando: {e}")
    
    # =============================================================================
    # TRACKING - Rotación Inteligente con increment simplificado
    # =============================================================================
    
    async def _get_next_combination_to_search(self, user_id: str) -> Optional[dict]:
        """Obtiene la próxima combinación no agotada. Resetea si todas agotadas."""
        try:
            response = self.supabase.table("domain_search_tracking")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_exhausted", False)\
                .order("current_page", desc=False)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            log.info(f"[{user_id[:8]}] 🔄 Todas agotadas, reseteando...")
            await self._reset_all_combinations(user_id)
            
            response = self.supabase.table("domain_search_tracking")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_exhausted", False)\
                .order("current_page", desc=False)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            return await self._create_first_combination(user_id)
        except Exception as e:
            log.error(f"[{user_id[:8]}] ❌ Error obteniendo combinación: {e}")
            return None

    def _get_user_search_params(self, user_id: str) -> tuple:
        """Obtiene nicho/pais/ciudades del config del usuario + todos los globales.
        
        Rota entre TODOS los nichos (45+), poniendo el nicho del usuario primero
        para que tenga más prioridad. Así se maximizan empresas sin dominio.
        """
        config = self.active_users.get(user_id, {})
        
        # Nicho: TODOS los nichos, con el del usuario al principio para prioridad
        user_nicho = config.get('nicho')
        if user_nicho:
            nichos_pool = [user_nicho] + [n for n in NICHOS if n != user_nicho]
        else:
            nichos_pool = list(NICHOS)
        
        # País: usar el del usuario si existe, sino aleatorio global
        user_pais = config.get('pais')
        paises_pool = [user_pais] if user_pais else PAISES
        
        # Ciudades: usar las del usuario si existen (puede ser lista o string CSV)
        user_ciudades = config.get('ciudades')
        if user_ciudades:
            if isinstance(user_ciudades, str):
                ciudades_list = [c.strip() for c in user_ciudades.split(',') if c.strip()]
            elif isinstance(user_ciudades, list):
                ciudades_list = user_ciudades
            else:
                ciudades_list = None
        else:
            ciudades_list = None
        
        return nichos_pool, paises_pool, ciudades_list

    async def _create_first_combination(self, user_id: str) -> Optional[dict]:
        """Crea la primera combinación para un usuario nuevo.
        
        v8: Usa nicho/pais/ciudades de la config del usuario si están configurados.
        """
        try:
            nichos_pool, paises_pool, user_ciudades = self._get_user_search_params(user_id)
            
            nicho = random.choice(nichos_pool)
            pais = random.choice(paises_pool)
            
            if user_ciudades:
                ciudad = random.choice(user_ciudades)
            else:
                ciudades = CIUDADES_POR_PAIS.get(pais, ["Buenos Aires"])
                ciudad = random.choice(ciudades)
            
            data = {
                "user_id": user_id, "nicho": nicho, "ciudad": ciudad,
                "pais": pais, "current_page": 0, "total_domains_found": 0,
                "is_exhausted": False, "last_searched_at": utc_now().isoformat()
            }
            response = self.supabase.table("domain_search_tracking").insert(data).execute()
            log.info(f"[{user_id[:8]}] ➕ Primera combinación: {nicho} | {ciudad}, {pais}")
            return response.data[0] if response.data else None
        except Exception as e:
            log.error(f"[{user_id[:8]}] ❌ Error creando primera combinación: {e}")
            return None

    _rpc_increment_available: bool = True

    async def _increment_page(self, user_id: str, nicho: str, ciudad: str, pais: str, domains_found: int):
        """Incrementa página con un solo UPDATE (sin SELECT previo)."""
        try:
            if self._rpc_increment_available:
                try:
                    self.supabase.rpc("increment_search_page", {
                        "p_user_id": user_id,
                        "p_nicho": nicho,
                        "p_ciudad": ciudad,
                        "p_pais": pais,
                        "p_domains_found": domains_found
                    }).execute()
                    return
                except Exception as rpc_err:
                    if "404" in str(rpc_err) or "not found" in str(rpc_err).lower():
                        self.__class__._rpc_increment_available = False
                        log.warning("⚠️ RPC increment_search_page no existe, usando fallback SELECT+UPDATE")
                    else:
                        raise

            response = self.supabase.table("domain_search_tracking")\
                .select("current_page, total_domains_found")\
                .eq("user_id", user_id).eq("nicho", nicho)\
                .eq("ciudad", ciudad).eq("pais", pais)\
                .execute()

            if response.data:
                cd = response.data[0]
                self.supabase.table("domain_search_tracking").update({
                    "current_page": cd['current_page'] + 1,
                    "total_domains_found": cd['total_domains_found'] + domains_found,
                    "last_searched_at": utc_now().isoformat(),
                    "updated_at": utc_now().isoformat()
                }).eq("user_id", user_id).eq("nicho", nicho)\
                  .eq("ciudad", ciudad).eq("pais", pais).execute()
        except Exception as e:
            log.error(f"❌ Error incrementando página: {e}")

    async def _mark_combination_exhausted(self, user_id: str, nicho: str, ciudad: str, pais: str):
        """Marca combinación agotada y crea la siguiente."""
        try:
            self.supabase.table("domain_search_tracking").update({
                "is_exhausted": True, "updated_at": utc_now().isoformat()
            }).eq("user_id", user_id).eq("nicho", nicho)\
              .eq("ciudad", ciudad).eq("pais", pais).execute()
            
            await self._create_next_combination(user_id, nicho, ciudad, pais)
        except Exception as e:
            log.error(f"❌ Error marcando agotada: {e}")

    async def _create_next_combination(self, user_id: str, current_nicho: str,
                                       current_ciudad: str, current_pais: str):
        """
        Progresión infinita: ciudad → país → nicho → loop.
        v8: Respeta config del usuario. Si tiene nicho/pais/ciudades configurados,
        solo rota dentro de esos valores.
        """
        try:
            nichos_pool, paises_pool, user_ciudades = self._get_user_search_params(user_id)
            
            # Determinar pool de ciudades para el país actual
            if user_ciudades:
                ciudades = user_ciudades
            else:
                ciudades = CIUDADES_POR_PAIS.get(current_pais, [])
            
            idx = ciudades.index(current_ciudad) if current_ciudad in ciudades else -1
            
            if 0 <= idx < len(ciudades) - 1:
                # Siguiente ciudad en el mismo país
                next_ciudad, next_pais, next_nicho = ciudades[idx + 1], current_pais, current_nicho
            else:
                # Ciudades agotadas → siguiente país
                pais_idx = paises_pool.index(current_pais) if current_pais in paises_pool else -1
                if 0 <= pais_idx < len(paises_pool) - 1:
                    next_pais = paises_pool[pais_idx + 1]
                    if user_ciudades:
                        next_ciudad = user_ciudades[0]
                    else:
                        next_ciudad = CIUDADES_POR_PAIS.get(next_pais, ["Buenos Aires"])[0]
                    next_nicho = current_nicho
                else:
                    # Países agotados → siguiente nicho
                    nicho_idx = nichos_pool.index(current_nicho) if current_nicho in nichos_pool else -1
                    next_nicho = nichos_pool[(nicho_idx + 1) % len(nichos_pool)]
                    next_pais = paises_pool[0]
                    if user_ciudades:
                        next_ciudad = user_ciudades[0]
                    else:
                        next_ciudad = CIUDADES_POR_PAIS.get(next_pais, ["Buenos Aires"])[0]
            
            # Verificar si ya existe
            existing = self.supabase.table("domain_search_tracking")\
                .select("id").eq("user_id", user_id)\
                .eq("nicho", next_nicho).eq("ciudad", next_ciudad)\
                .eq("pais", next_pais).execute()
            
            if not existing.data:
                self.supabase.table("domain_search_tracking").insert({
                    "user_id": user_id, "nicho": next_nicho, "ciudad": next_ciudad,
                    "pais": next_pais, "current_page": 0, "total_domains_found": 0,
                    "is_exhausted": False, "last_searched_at": utc_now().isoformat()
                }).execute()
                log.info(f"[{user_id[:8]}] ➕ Siguiente: {next_nicho} | {next_ciudad}, {next_pais}")
            
        except Exception as e:
            log.error(f"❌ Error creando siguiente combinación: {e}")

    async def _reset_all_combinations(self, user_id: str):
        """Resetea todas las combinaciones (is_exhausted=false, page=0)."""
        try:
            self.supabase.table("domain_search_tracking").update({
                "is_exhausted": False, "current_page": 0,
                "updated_at": utc_now().isoformat()
            }).eq("user_id", user_id).execute()
        except Exception as e:
            log.error(f"❌ Error reseteando combinaciones: {e}")
    
    async def _log_to_user(self, user_id: str, level: str, action: str, domain: str, message: str):
        """Envía log al usuario en tiempo real."""
        try:
            self.supabase.table("hunter_logs").insert({
                'user_id': user_id, 'domain': domain,
                'level': level, 'action': action, 'message': message,
            }).execute()
        except Exception:
            pass  # Non-critical, don't spam error logs


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Entry point."""
    env = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    print(f"\n{'='*70}")
    print(f"DOMAIN HUNTER WORKER v8 | {env} | {utc_now().isoformat()}")
    print(f"{'='*70}\n")
    
    worker = DomainHunterWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())

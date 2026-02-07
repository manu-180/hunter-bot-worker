"""
Domain Hunter Worker - Worker daemon para buscar dominios automáticamente desde Google.

Este worker:
1. Consulta periódicamente Supabase para encontrar usuarios con bot_enabled = true
2. Para cada usuario activo, busca dominios en Google según su nicho
3. Cada 5 dominios encontrados, los inserta en la tabla leads del usuario
4. Continúa 24/7 con pausas largas entre búsquedas para evitar bloqueos
5. Trabaja en sinergia con main.py (LeadSniper) que procesa los dominios agregados

Usage:
    python domain_hunter_worker.py
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import List, Set
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from serpapi import GoogleSearch
from supabase import create_client, Client

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role key
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # SerpAPI key para búsquedas

# Delays para evitar bloqueo (en segundos)
MIN_DELAY_BETWEEN_SEARCHES = 3  # Reducido de 30s a 3s (SerpAPI protege contra bloqueos)
MAX_DELAY_BETWEEN_SEARCHES = 10  # Reducido de 90s a 10s

# Cada cuánto checar por usuarios con bot enabled (en segundos)
CHECK_USERS_INTERVAL = 60  # 1 minuto

# =============================================================================
# HORARIO INTELIGENTE - Pausar búsquedas de noche para no gastar SerpAPI
# =============================================================================
BUSINESS_HOURS_START = 8   # 8 AM (hora Argentina)
BUSINESS_HOURS_END = 20    # 8 PM (hora Argentina) - EXTENDIDO
PAUSE_CHECK_INTERVAL = 300  # Revisar cada 5 minutos cuando está pausado

# Batch size: cuántos dominios intentar agregar por búsqueda (solo los nuevos se insertan)
DOMAIN_BATCH_SIZE = 20  # Más candidatos por ronda para que la cola PEND pueda crecer

# User Agents para rotar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Blacklist de dominios a ignorar (ampliada y mejorada)
BLACKLIST_DOMAINS = {
    # Redes sociales
    'google', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
    'tiktok', 'pinterest', 'whatsapp', 'telegram', 'snapchat',
    
    # Portales inmobiliarios (queremos inmobiliarias reales, no portales)
    'mercadolibre', 'olx', 'zonaprop', 'argenprop', 'properati',
    'trovit', 'lamudi', 'inmuebles24', 'metrocuadrado', 'fincaraiz',
    
    # Gobierno y entidades públicas
    'gob.ar', 'gov.ar', 'gobierno', '.mil.', 'afip', 'anses', 'arba',
    'provincia.', 'municipalidad', 'intendencia',
    
    # Portales de noticias y medios
    'clarin', 'lanacion', 'infobae', 'pagina12', 'lavoz', 'losandes',
    'telam', 'perfil', 'ambito', 'cronista',
    
    # Portales educativos
    'edu.ar', 'educacion', 'universidad', '.edu', 'campus',
    
    # Bancos y servicios financieros
    'banco', 'santander', 'galicia', 'nacion', 'provincia.com',
    'hsbc', 'bbva', 'icbc', 'frances', 'supervielle',
    
    # Organizaciones y ONGs
    'wikipedia', 'wikidata', 'ong', 'fundacion',
    
    # Portales de empleo
    'zonajobs', 'computrabajo', 'bumeran', 'indeed', 'linkedin',
    
    # Portales genéricos y marketplaces
    'booking.com', 'airbnb', 'tripadvisor', 'yelp', 'foursquare',
    'despegar', 'almundo', 'decolar', 'expedia',
    
    # Otros sitios a evitar
    'maps.google', '/maps/', 'youtube', 'blogspot', 'wordpress.com',
    'wix.com', 'weebly', 'tumblr', '.gov', 'gmail', 'outlook',
    'hotmail', 'yahoo', 'ejemplo', 'example', 'test', 'demo',
}

# Extensiones de dominio gubernamentales a filtrar
GOVERNMENT_TLD = {
    '.gob.', '.gov.', '.mil.', '.edu.ar'
}

# =============================================================================
# LISTAS DE ROTACIÓN AUTOMÁTICA
# =============================================================================

# 120+ nichos con potencial de email y ventas (EXPANDIDO)
NICHOS = [
    # ========== SERVICIOS PROFESIONALES (20) ==========
    "inmobiliarias", "estudios contables", "estudios juridicos", "escribanias",
    "agencias de marketing", "agencias de marketing digital", "consultoras",
    "agencias de diseño", "agencias de diseño grafico", "estudios de arquitectura",
    "desarrolladores web", "consultoras IT", "agencias SEO", "agencias de publicidad",
    "agencias de social media", "productoras audiovisuales", "estudios de ingenieria",
    "topografos", "agrimensores", "peritos",
    
    # ========== SERVICIOS LOCALES (25) ==========
    "gimnasios", "centros de estetica", "peluquerias", "barbereias",
    "spa", "centros de masajes", "salones de belleza", "manicura y pedicura",
    "clinicas dentales", "clinicas veterinarias", "pet shops", "veterinarias",
    "talleres mecanicos", "talleres de chapa y pintura", "gomenerias",
    "lavaderos de autos", "lubricentros", "cerrajerias", "herrerias",
    "empresas de limpieza", "empresas de mudanzas", "empresas de seguridad",
    "empresas de vigilancia", "guardias de seguridad", "servicios de seguridad",
    
    # ========== CONSTRUCCIÓN Y MANTENIMIENTO (15) ==========
    "empresas de construccion", "constructoras", "arquitectura y construccion",
    "electricistas", "plomeros", "gasfiteros", "pintores", "yeseros",
    "albaniles", "carpinteros", "herreros", "vidrieros",
    "instaladores de aire acondicionado", "reparacion de electrodomesticos",
    "techistas",
    
    # ========== RETAIL Y COMERCIO (20) ==========
    "tiendas de ropa", "boutiques", "tiendas de ropa infantil",
    "joyerias", "relojerias", "opticas", "librerias", "papelerias",
    "jugueterias", "ferreterias", "viveros", "tiendas de jardineria",
    "tiendas de deportes", "casas de deportes", "bicicleterias",
    "tiendas de repuestos", "casas de musica", "instrumentos musicales",
    "tiendas de electronica", "casas de electrodomesticos",
    
    # ========== GASTRONOMÍA (20) ==========
    "restaurantes", "cafeterias", "cafes", "panaderias", "pastelerias",
    "pizzerias", "hamburgueserias", "parrillas", "asaderos",
    "heladerias", "bares", "pubs", "cervecerías artesanales",
    "catering", "servicios de catering", "rotiserias", "comidas rapidas",
    "delivery de comida", "cocinas industriales", "confiterias",
    
    # ========== SALUD Y BIENESTAR (20) ==========
    "centros medicos", "clinicas", "consultorios medicos", "policlinicas",
    "laboratorios", "laboratorios de analisis clinicos", "farmacias",
    "kinesiologos", "centros de kinesiologia", "fisioterapeutas",
    "nutricionistas", "dietistas", "psicologos", "terapeutas",
    "centros de yoga", "centros de pilates", "centros de meditacion",
    "quiropracticos", "osteopatas", "podologos",
    
    # ========== EDUCACIÓN Y CAPACITACIÓN (15) ==========
    "institutos de idiomas", "academias de ingles", "escuelas de idiomas",
    "academias de arte", "escuelas de musica", "conservatorios",
    "centros de capacitacion", "centros de formacion profesional",
    "guarderias", "jardines de infantes", "jardines maternales",
    "centros de apoyo escolar", "profesores particulares", "clases particulares",
    "centros de computacion",
    
    # ========== TURISMO Y HOTELERÍA (15) ==========
    "hoteles", "hostels", "apart hoteles", "cabañas", "posadas",
    "bed and breakfast", "agencias de turismo", "agencias de viajes",
    "operadores turisticos", "rent a car", "alquiler de autos",
    "alquiler de motos", "transporte turistico", "excursiones", "tours",
    
    # ========== EVENTOS Y ENTRETENIMIENTO (12) ==========
    "fotografos", "fotografos profesionales", "estudios fotograficos",
    "organizadores de eventos", "salones de fiestas", "quintas para eventos",
    "DJ para eventos", "bandas musicales", "animacion infantil",
    "alquiler de sonido", "alquiler de luces", "production de eventos",
    
    # ========== INDUSTRIA Y PRODUCCIÓN (15) ==========
    "metalurgicas", "carpinterias", "talleres de soldadura", "torneros",
    "fabricas de muebles", "aserraderos", "imprentas", "graficas",
    "serigrafias", "rotulaciones", "ploteos", "empresas de packaging",
    "fábricas de plástico", "fábricas de productos de limpieza", "textiles",
    
    # ========== AGRICULTURA Y GANADERÍA (10) ==========
    "agronomos", "agroquimicas", "veterinarias rurales", "cabañas ganaderas",
    "semillerias", "proveedores agricolas", "maquinaria agricola",
    "criaderos de animales", "granjas", "tambos",
    
    # ========== TRANSPORTE Y LOGÍSTICA (12) ==========
    "empresas de transporte", "logistica", "empresas de fletes", "mudanzas",
    "transporte de cargas", "correos privados", "mensajerias", "courier",
    "distribuidoras", "depositos", "almacenes", "galpones",
    
    # ========== TECNOLOGÍA Y COMUNICACIONES (10) ==========
    "desarrollo de software", "programadores", "diseño web", "hosting",
    "service de computadoras", "reparacion de celulares", "venta de celulares",
    "accesorios de tecnologia", "CCTV", "camaras de seguridad",
    
    # ========== SERVICIOS FINANCIEROS Y SEGUROS (8) ==========
    "aseguradoras", "productores de seguros", "gestorías", "gestoria automotor",
    "escribanías", "tramites legales", "financieras", "prestamos",
    
    # ========== AUTOMOTOR (10) ==========
    "concesionarias", "agencias de autos", "compra venta de autos usados",
    "desarmaderos", "repuestos para autos", "autopartes", "accesorios para autos",
    "polarizado de autos", "instalacion de alarmas", "audio para autos",
    
    # ========== DECORACIÓN Y HOGAR (10) ==========
    "decoracion de interiores", "diseño de interiores", "cortinas y persianas",
    "pisos y revestimientos", "alfombras", "pinturerias", "papeles pintados",
    "mueblerias", "colchonerias", "bazar y menaje",
    
    # ========== MASCOTAS Y ANIMALES (8) ==========
    "veterinarias", "pet shops", "peluqueria canina", "adiestramiento canino",
    "guarderia para mascotas", "criaderos de perros", "acuarios", "alimento para mascotas",
    
    # ========== FLORES Y JARDINERÍA (8) ==========
    "floristas", "florerías", "viveros", "plantas ornamentales",
    "paisajismo", "diseño de jardines", "sistemas de riego", "jardineros",
]

# =============================================================================
# FUNCIONES AUXILIARES - HORARIO INTELIGENTE
# =============================================================================

def is_business_hours() -> bool:
    """
    Verifica si estamos en horario laboral (8 AM - 7 PM, hora Argentina).
    
    Railway corre en UTC, convertimos a Argentina (UTC-3).
    
    Returns:
        True si estamos en horario laboral, False si no
    """
    utc_now = datetime.utcnow()
    utc_hour = utc_now.hour
    
    # Convertir UTC a hora de Argentina (UTC-3)
    argentina_hour = (utc_hour - 3) % 24
    
    # Verificar si estamos entre 8 AM y 7 PM (hora Argentina)
    in_business_hours = BUSINESS_HOURS_START <= argentina_hour < BUSINESS_HOURS_END
    
    return in_business_hours

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
    from cities_data import CIUDADES_POR_PAIS, PAISES, TOTAL_CIUDADES, TOTAL_PAISES
    log.info(f"✅ Base de ciudades cargada: {TOTAL_PAISES} países, {TOTAL_CIUDADES} ciudades")
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

# =============================================================================
# DOMAIN HUNTER WORKER
# =============================================================================

class DomainHunterWorker:
    """Worker daemon que busca dominios en Google 24/7."""
    
    def __init__(self):
        """Inicializa el worker."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.serpapi_key = SERPAPI_KEY
        self.active_users = {}  # user_id -> config
        self.search_pagination = {}  # (user_id, ciudad) -> página actual
        
    async def start(self):
        """Inicia el worker daemon."""
        log.info("\n" + "="*70)
        log.info("🔍 DOMAIN HUNTER WORKER - Iniciando")
        log.info("="*70 + "\n")
        
        if not self.serpapi_key:
            log.error("❌ SERPAPI_KEY no configurada en .env")
            log.error("   Consigue tu key gratis en: https://serpapi.com/")
            return
        
        log.info("✅ SerpAPI configurada")
        log.info(f"✅ Supabase URL: {SUPABASE_URL[:30]}...")
        
        # 🔖 FINGERPRINT DE VERSION - para confirmar qué código corre Railway
        utc_now = datetime.utcnow()
        utc_hour = utc_now.hour
        argentina_hour = (utc_hour - 3) % 24
        argentina_min = utc_now.minute
        log.info(f"\n🔖 VERSION: horario_extended_v3 | HORARIO EXTENDIDO HASTA 20:00")
        log.info(f"🕐 HORA ACTUAL: Argentina={argentina_hour:02d}:{argentina_min:02d} | UTC={utc_hour:02d}:{argentina_min:02d}")
        log.info(f"🕐 HORARIO LABORAL: {BUSINESS_HOURS_START}:00 - {BUSINESS_HOURS_END}:00 (hora Argentina)")
        log.info(f"🛡️ GUARDIA DOBLE: check en _main_loop() + check en _search_domains_for_user()")
        _currently_business = is_business_hours()
        log.info(f"📊 ESTADO ACTUAL: {'✅ DENTRO de horario laboral - buscando dominios' if _currently_business else '⏸️  FUERA de horario - SerpAPI PAUSADO, 0 creditos se gastaran'}")
        
        log.info(f"\n⏱️  Check de usuarios cada {CHECK_USERS_INTERVAL}s")
        log.info(f"⏱️  Delay entre búsquedas: {MIN_DELAY_BETWEEN_SEARCHES}-{MAX_DELAY_BETWEEN_SEARCHES}s")
        log.info(f"📦 Batch size: {DOMAIN_BATCH_SIZE} dominios")
        log.info(f"🌍 Total países: {TOTAL_PAISES} | Total ciudades: {TOTAL_CIUDADES}")
        log.info(f"🎯 Total nichos disponibles: {len(NICHOS)}\n")
        
        try:
            await self._main_loop()
        except KeyboardInterrupt:
            log.info("\n\n⚠️  Detenido por el usuario")
        finally:
            log.info("✅ Worker cerrado correctamente")
    
    async def _main_loop(self):
        """Loop principal del worker."""
        log.info("🚀 Entrando en loop principal del Domain Hunter Worker...\n")
        
        while True:
            try:
                # 1. Obtener usuarios con bot habilitado
                log.info("=" * 70)
                log.info("🔄 Nueva iteración del loop principal")
                log.info("=" * 70)
                
                await self._update_active_users()
                
                if not self.active_users:
                    log.warning("😴 No hay usuarios con bot habilitado. Esperando...")
                    log.info(f"⏳ Esperando {CHECK_USERS_INTERVAL}s antes de revisar de nuevo...\n")
                    await asyncio.sleep(CHECK_USERS_INTERVAL)
                    continue
                
                # 🕐 VERIFICAR HORARIO LABORAL (8 AM - 8 PM, hora Argentina)
                utc_now = datetime.utcnow()
                argentina_hour = (utc_now.hour - 3) % 24
                argentina_min = utc_now.minute
                
                log.info(f"🕐 Hora actual: Argentina {argentina_hour:02d}:{argentina_min:02d} | UTC {utc_now.hour:02d}:{argentina_min:02d}")
                
                if not is_business_hours():
                    log.warning(
                        f"⏸️  FUERA DE HORARIO LABORAL (hora Argentina: {argentina_hour:02d}:{argentina_min:02d}). "
                        f"Pausando búsquedas de dominios hasta las {BUSINESS_HOURS_START}:00 AM..."
                    )
                    log.info(f"💰 Ahorrando créditos de SerpAPI. Revisando en {PAUSE_CHECK_INTERVAL}s...\n")
                    await asyncio.sleep(PAUSE_CHECK_INTERVAL)
                    continue
                
                log.info(f"✅ Dentro de horario laboral ({BUSINESS_HOURS_START}:00 - {BUSINESS_HOURS_END}:00). Buscando dominios...")
                
                # 2. Procesar cada usuario activo
                log.info(f"📋 Procesando {len(self.active_users)} usuario(s)...\n")
                
                for user_id, config in self.active_users.items():
                    log.info(f"\n{'='*70}")
                    log.info(f"🎯 Procesando usuario: {user_id[:8]}...")
                    log.info(f"   Nicho: {config.get('nicho', 'N/A')}")
                    log.info(f"   País: {config.get('pais', 'N/A')}")
                    log.info(f"   Rotación automática: ACTIVADA")
                    log.info(f"{'='*70}\n")
                    
                    # Buscar dominios para este usuario
                    log.info("🔍 Iniciando búsqueda de dominios...")
                    domains = await self._search_domains_for_user(user_id, config)
                    
                    if domains:
                        log.info(f"\n✅ Encontrados {len(domains)} dominios válidos:")
                        for i, domain in enumerate(domains[:5], 1):
                            log.info(f"   {i}. {domain}")
                        if len(domains) > 5:
                            log.info(f"   ... y {len(domains) - 5} más\n")
                        
                        # Guardar dominios en Supabase
                        log.info(f"💾 Guardando {len(domains)} dominios en Supabase...")
                        await self._save_domains_to_supabase(user_id, domains)
                        
                        # Log de progreso
                        await self._log_to_user(
                            user_id=user_id,
                            level="success",
                            action="domain_added",
                            domain="system",
                            message=f"✅ {len(domains)} dominios nuevos agregados a la cola"
                        )
                        log.info(f"✅ Dominios guardados correctamente\n")
                    else:
                        log.warning(f"⚠️  No se encontraron dominios válidos en esta búsqueda\n")
                    
                    # Delay antes de procesar el siguiente usuario
                    delay = random.randint(5, 15)
                    log.info(f"⏳ Esperando {delay}s antes del siguiente usuario...\n")
                    await asyncio.sleep(delay)
                
                # 3. Delay antes de la siguiente ronda
                await asyncio.sleep(CHECK_USERS_INTERVAL)
                
            except Exception as e:
                log.error(f"❌ Error en loop principal: {e}")
                await asyncio.sleep(30)
    
    async def _update_active_users(self):
        """Obtiene usuarios con bot habilitado desde Supabase."""
        try:
            log.info("🔍 Consultando Supabase por usuarios con bot_enabled=true...")
            
            response = self.supabase.table("hunter_configs")\
                .select("*")\
                .eq("bot_enabled", True)\
                .execute()
            
            log.info(f"📡 Respuesta de Supabase: {len(response.data)} registros encontrados")
            
            # Actualizar diccionario de usuarios activos
            self.active_users = {
                config['user_id']: config 
                for config in response.data
            }
            
            if self.active_users:
                log.info(f"✅ {len(self.active_users)} usuario(s) con bot activo:")
                for user_id, config in self.active_users.items():
                    log.info(f"   - Usuario: {user_id[:8]}... | Nicho: {config.get('nicho', 'N/A')} | País: {config.get('pais', 'N/A')}")
            else:
                log.warning("⚠️  No se encontraron usuarios con bot_enabled=true")
            
        except Exception as e:
            log.error(f"❌ Error obteniendo usuarios: {e}")
            import traceback
            log.error(f"   Traceback: {traceback.format_exc()}")
    
    async def _search_domains_for_user(self, user_id: str, config: dict) -> List[str]:
        """
        Busca dominios usando ROTACIÓN INTELIGENTE de nichos, ciudades y países.
        Ya no usa la config del usuario (nicho, ciudades, pais) - es 100% automático.
        
        Args:
            user_id: ID del usuario
            config: Configuración del usuario (ignorada, se usa rotación automática)
        
        Returns:
            Lista de dominios encontrados (hasta DOMAIN_BATCH_SIZE)
        """
        # 1. Obtener o crear tracking para este usuario
        tracking = await self._get_next_combination_to_search(user_id)
        
        if not tracking:
            log.warning(f"⚠️  Usuario {user_id[:8]}... no tiene más combinaciones para buscar")
            return []
        
        nicho = tracking['nicho']
        ciudad = tracking['ciudad']
        pais = tracking['pais']
        current_page = tracking['current_page']
        
        # Mejorar query para obtener resultados más específicos
        # Alternamos entre diferentes tipos de queries para obtener más variedad
        query_modifiers = [
            f"{nicho} en {ciudad}",  # Búsqueda básica
            f"{nicho} {ciudad} contacto",  # Con contacto
            f"{nicho} profesionales {ciudad}",  # Profesionales
            f"empresas de {nicho} {ciudad}",  # Empresas de...
        ]
        
        # Rotar el modificador según la página actual
        query_index = current_page % len(query_modifiers)
        query = query_modifiers[query_index]
        
        start_result = current_page * 10  # SerpAPI paginación
        
        log.info(f"🎯 Rotación: {nicho} | {ciudad}, {pais} | Página {current_page + 1}")
        log.info(f"🔍 Query SerpAPI: \"{query}\"")
        
        try:
            # 🛡️ GUARDIA FINAL: verificar horario JUSTO antes de gastar crédito
            if not is_business_hours():
                utc_now = datetime.utcnow()
                argentina_hour = (utc_now.hour - 3) % 24
                log.warning(
                    f"🛡️ GUARDIA FINAL: Bloqueando llamada a SerpAPI fuera de horario "
                    f"(hora Argentina: {argentina_hour:02d}:00). No se gastará crédito."
                )
                return []
            
            # Configurar búsqueda con SerpAPI
            params = {
                "q": query,
                "location": f"{ciudad}, {pais}",
                "hl": "es",
                "gl": pais[:2].lower(),  # Código de país (ej: ar, mx, co)
                "num": 20,
                "start": start_result,
                "api_key": self.serpapi_key
            }
            
            # 💰 Log de auditoría: registrar hora exacta de cada búsqueda SerpAPI
            utc_now = datetime.utcnow()
            argentina_hour = (utc_now.hour - 3) % 24
            argentina_min = utc_now.minute
            log.info(
                f"💰 SERPAPI CALL: hora Argentina {argentina_hour:02d}:{argentina_min:02d} | "
                f"UTC {utc_now.hour:02d}:{argentina_min:02d} | Query: \"{query}\""
            )
            
            # Ejecutar búsqueda
            search = await asyncio.to_thread(GoogleSearch(params).get_dict)
            organic_results = search.get("organic_results", [])
            
            log.info(f"📊 SerpAPI devolvió {len(organic_results)} resultados")
            
            domains_found = set()
            
            for result in organic_results:
                link = result.get("link")
                if not link:
                    continue
                
                domain = self._extract_domain(link)
                if domain and self._is_valid_domain(domain):
                    domains_found.add(domain)
                    log.info(f"  ✅ {domain}")
                    
                    if len(domains_found) >= DOMAIN_BATCH_SIZE:
                        break
            
            # 2. Actualizar tracking según resultados
            if len(domains_found) == 0:
                # 🎯 ESTRATEGIA MÁS PACIENTE: No marcar como agotada inmediatamente
                # Solo después de múltiples intentos sin resultados
                if current_page >= 2:
                    # Ya buscamos en páginas 0, 1, 2 sin resultados → realmente agotada
                    await self._mark_combination_exhausted(user_id, nicho, ciudad, pais)
                    log.info(f"🏁 Combinación agotada (0 resultados en 3 intentos). Rotando a siguiente...")
                else:
                    # Primer o segundo intento → dar otra chance
                    await self._increment_page(user_id, nicho, ciudad, pais, 0)
                    log.info(f"⚠️  0 resultados (intento {current_page + 1}/3), continuando...")
            else:
                # ✅ Hay resultados - incrementar página para próxima búsqueda
                await self._increment_page(user_id, nicho, ciudad, pais, len(domains_found))
                log.info(f"📄 Próxima búsqueda: página {current_page + 2}")
            
            # Delay antes de la siguiente búsqueda
            delay = random.randint(MIN_DELAY_BETWEEN_SEARCHES, MAX_DELAY_BETWEEN_SEARCHES)
            log.info(f"⏳ Delay: {delay}s")
            await asyncio.sleep(delay)
            
            return list(domains_found)
            
        except Exception as e:
            log.error(f"❌ Error en búsqueda SerpAPI: {e}")
            return []
    
    def _extract_domain_from_search_link(self, href: str) -> str | None:
        """
        Extrae el dominio real de un link de resultados de búsqueda.
        
        DuckDuckGo usa links directos, no como Google que wrappea.
        """
        if not href:
            return None
        
        # DuckDuckGo puede tener links tipo //duckduckgo.com/l/?uddg=...
        # En ese caso, extraer el parámetro uddg
        if 'duckduckgo.com/l/' in href:
            try:
                parsed = urlparse(href if href.startswith('http') else f'https:{href}')
                params = parse_qs(parsed.query)
                if 'uddg' in params:
                    actual_url = params['uddg'][0]
                    return self._extract_domain(actual_url)
            except:
                pass
        
        # Si es un link directo
        return self._extract_domain(href)
    
    def _extract_domain(self, url: str) -> str | None:
        """Extrae el dominio base de una URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            
            # Limpiar
            domain = domain.lower().strip()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Quitar puerto si existe
            if ':' in domain:
                domain = domain.split(':')[0]
            
            return domain if domain else None
        except:
            return None
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Verifica si un dominio es válido y no está en blacklist (mejorado)."""
        if not domain or len(domain) < 4:
            return False
        
        # Convertir a minúsculas para comparación
        domain_lower = domain.lower()
        
        # 1. Filtrar links de Google Maps y rutas
        if domain_lower.startswith('/') or '/maps/' in domain_lower:
            return False
        
        # 2. Filtrar dominios con caracteres raros o mal formados
        if any(char in domain for char in ['[', ']', '{', '}', '|', '\\', ' ', '%']):
            return False
        
        # 3. Verificar que tenga al menos un punto (TLD)
        if '.' not in domain:
            return False
        
        # 4. Filtrar dominios de ejemplo/prueba
        if any(word in domain_lower for word in ['ejemplo', 'example', 'test', 'demo', 'sample']):
            return False
        
        # 5. Verificar blacklist principal
        for blacklisted in BLACKLIST_DOMAINS:
            if blacklisted in domain_lower:
                return False
        
        # 6. Verificar extensiones gubernamentales
        for gov_tld in GOVERNMENT_TLD:
            if gov_tld in domain_lower:
                return False
        
        # 7. Filtrar dominios que son solo números o muy genéricos
        parts = domain_lower.split('.')
        if len(parts) < 2:
            return False
        
        # El nombre debe tener al menos 3 caracteres (ej: abc.com es válido, ab.com no)
        if len(parts[0]) < 3:
            return False
        
        # 8. Filtrar portales muy conocidos por TLD
        if domain_lower.endswith(('.blogspot.com', '.wordpress.com', '.wix.com', 
                                   '.weebly.com', '.tumblr.com', '.github.io')):
            return False
        
        # 9. Verificar que no sea email (algunos scrapers capturan mal)
        if '@' in domain:
            return False
        
        return True
    
    async def _save_domains_to_supabase(self, user_id: str, domains: List[str]):
        """Guarda dominios NUEVOS en la tabla leads del usuario.
        
        Usamos ignore_duplicates=True para que solo se inserten dominios que
        no existan (user_id, domain). Así no re-encolamos dominios ya enviados
        o fallidos, y PEND refleja solo los realmente nuevos en cola.
        """
        try:
            leads_data = [
                {
                    'user_id': user_id,
                    'domain': domain,
                    'status': 'pending',
                }
                for domain in domains
            ]
            
            # Solo insertar si no existe (no sobrescribir enviados/fallidos)
            self.supabase.table("leads").upsert(
                leads_data,
                on_conflict='user_id,domain',
                ignore_duplicates=True,
            ).execute()
            
            log.info(f"💾 {len(domains)} dominios ofrecidos a la cola (solo nuevos se insertan)")
            
        except Exception as e:
            log.error(f"❌ Error guardando dominios: {e}")
    
    # =============================================================================
    # MÉTODOS DE TRACKING - Sistema de Rotación Inteligente
    # =============================================================================
    
    async def _get_next_combination_to_search(self, user_id: str) -> dict | None:
        """
        Obtiene la próxima combinación (nicho, ciudad, país) a buscar.
        Prioriza combinaciones no agotadas. Si todas están agotadas, resetea.
        """
        try:
            # Buscar combinación no agotada con menor página (para "exprimir" cada una)
            response = self.supabase.table("domain_search_tracking")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_exhausted", False)\
                .order("current_page", desc=False)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            # Si todas están agotadas, resetear y empezar de nuevo
            log.info(f"🔄 Todas las combinaciones agotadas para {user_id[:8]}. Reseteando...")
            await self._reset_all_combinations(user_id)
            
            # Intentar de nuevo después del reset
            response = self.supabase.table("domain_search_tracking")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_exhausted", False)\
                .order("current_page", desc=False)\
                .limit(1)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            # Si aún no hay, crear la primera combinación
            return await self._create_first_combination(user_id)
            
        except Exception as e:
            log.error(f"❌ Error obteniendo próxima combinación: {e}")
            return None

    async def _create_first_combination(self, user_id: str) -> dict | None:
        """Crea la primera combinación para un usuario nuevo."""
        try:
            nicho = random.choice(NICHOS)
            pais = random.choice(PAISES)
            ciudad = random.choice(CIUDADES_POR_PAIS[pais])
            
            data = {
                "user_id": user_id,
                "nicho": nicho,
                "ciudad": ciudad,
                "pais": pais,
                "current_page": 0,
                "total_domains_found": 0,
                "is_exhausted": False,
                "last_searched_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("domain_search_tracking")\
                .insert(data)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            log.error(f"❌ Error creando primera combinación: {e}")
            return None

    async def _increment_page(self, user_id: str, nicho: str, ciudad: str, pais: str, domains_found: int):
        """Incrementa la página para la próxima búsqueda de esta combinación."""
        try:
            # Primero obtener el valor actual
            response = self.supabase.table("domain_search_tracking")\
                .select("current_page, total_domains_found")\
                .eq("user_id", user_id)\
                .eq("nicho", nicho)\
                .eq("ciudad", ciudad)\
                .eq("pais", pais)\
                .execute()
            
            if response.data:
                current_data = response.data[0]
                new_page = current_data['current_page'] + 1
                new_total = current_data['total_domains_found'] + domains_found
                
                # Actualizar con los nuevos valores
                self.supabase.table("domain_search_tracking")\
                    .update({
                        "current_page": new_page,
                        "total_domains_found": new_total,
                        "last_searched_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("user_id", user_id)\
                    .eq("nicho", nicho)\
                    .eq("ciudad", ciudad)\
                    .eq("pais", pais)\
                    .execute()
        except Exception as e:
            log.error(f"❌ Error incrementando página: {e}")

    async def _mark_combination_exhausted(self, user_id: str, nicho: str, ciudad: str, pais: str):
        """Marca una combinación como agotada y crea la siguiente."""
        try:
            # Marcar actual como agotada
            self.supabase.table("domain_search_tracking")\
                .update({
                    "is_exhausted": True,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("user_id", user_id)\
                .eq("nicho", nicho)\
                .eq("ciudad", ciudad)\
                .eq("pais", pais)\
                .execute()
            
            # Crear siguiente combinación
            await self._create_next_combination(user_id, nicho, ciudad, pais)
            
        except Exception as e:
            log.error(f"❌ Error marcando combinación como agotada: {e}")

    async def _create_next_combination(self, user_id: str, current_nicho: str, current_ciudad: str, current_pais: str):
        """
        Crea la siguiente combinación para buscar.
        
        ESTRATEGIA DE PROGRESIÓN INFINITA:
        1. Siguiente ciudad en el MISMO país/nicho (completar país ciudad por ciudad)
        2. Si terminó todas las ciudades → Siguiente PAÍS (mismo nicho)
        3. Si terminó todos los países → Siguiente NICHO (primer país, primera ciudad)
        4. Loop infinito: cuando termina todos los nichos, vuelve al primero
        
        Ejemplo de progresión:
        - inmobiliarias | Buenos Aires, Argentina
        - inmobiliarias | Córdoba, Argentina
        - inmobiliarias | Rosario, Argentina
        - ... (350 ciudades de Argentina)
        - inmobiliarias | Ciudad de México, México
        - inmobiliarias | Guadalajara, México
        - ... (300 ciudades de México)
        - ... (todos los países)
        - estudios contables | Buenos Aires, Argentina (siguiente nicho)
        
        Esto genera ~250,000 combinaciones antes de repetir.
        """
        try:
            # 1. Intentar siguiente CIUDAD en el mismo país/nicho
            ciudades = CIUDADES_POR_PAIS.get(current_pais, [])
            current_index = ciudades.index(current_ciudad) if current_ciudad in ciudades else -1
            
            if current_index >= 0 and current_index < len(ciudades) - 1:
                # ✅ Hay más ciudades en este país → Siguiente ciudad
                next_ciudad = ciudades[current_index + 1]
                next_pais = current_pais
                next_nicho = current_nicho
                log.info(f"📍 Progresión: Siguiente ciudad en {current_pais}")
            else:
                # 2. No hay más ciudades → Intentar siguiente PAÍS (mismo nicho)
                pais_index = PAISES.index(current_pais) if current_pais in PAISES else -1
                
                if pais_index >= 0 and pais_index < len(PAISES) - 1:
                    # ✅ Hay más países → Siguiente país, primera ciudad
                    next_pais = PAISES[pais_index + 1]
                    next_ciudad = CIUDADES_POR_PAIS[next_pais][0]
                    next_nicho = current_nicho
                    log.info(f"🌎 Progresión: Completado {current_pais}, pasando a {next_pais}")
                else:
                    # 3. No hay más países → Siguiente NICHO (reiniciar países)
                    nicho_index = NICHOS.index(current_nicho) if current_nicho in NICHOS else -1
                    
                    if nicho_index >= 0 and nicho_index < len(NICHOS) - 1:
                        # ✅ Siguiente nicho
                        next_nicho = NICHOS[nicho_index + 1]
                    else:
                        # ✅ Loop infinito: volver al primer nicho
                        next_nicho = NICHOS[0]
                        log.info(f"🔄 Ciclo completo terminado! Reiniciando desde el primer nicho")
                    
                    next_pais = PAISES[0]  # Primer país (Argentina)
                    next_ciudad = CIUDADES_POR_PAIS[next_pais][0]  # Primera ciudad
                    log.info(f"🎯 Progresión: Completado nicho '{current_nicho}', pasando a '{next_nicho}'")
            
            # Verificar si ya existe (evitar duplicados)
            existing = self.supabase.table("domain_search_tracking")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("nicho", next_nicho)\
                .eq("ciudad", next_ciudad)\
                .eq("pais", next_pais)\
                .execute()
            
            if not existing.data:
                # Crear nueva combinación
                data = {
                    "user_id": user_id,
                    "nicho": next_nicho,
                    "ciudad": next_ciudad,
                    "pais": next_pais,
                    "current_page": 0,
                    "total_domains_found": 0,
                    "is_exhausted": False,
                    "last_searched_at": datetime.utcnow().isoformat()
                }
                
                self.supabase.table("domain_search_tracking")\
                    .insert(data)\
                    .execute()
                
                log.info(f"➕ Nueva: {next_nicho} | {next_ciudad}, {next_pais}")
            else:
                log.info(f"♻️  Ya existe: {next_nicho} | {next_ciudad}, {next_pais}")
            
        except Exception as e:
            log.error(f"❌ Error creando siguiente combinación: {e}")

    async def _reset_all_combinations(self, user_id: str):
        """Resetea todas las combinaciones de un usuario (marca is_exhausted=false, page=0)."""
        try:
            self.supabase.table("domain_search_tracking")\
                .update({
                    "is_exhausted": False,
                    "current_page": 0,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("user_id", user_id)\
                .execute()
            
            log.info(f"🔄 Todas las combinaciones reseteadas para {user_id[:8]}")
            
        except Exception as e:
            log.error(f"❌ Error reseteando combinaciones: {e}")
    
    async def _log_to_user(self, user_id: str, level: str, action: str, domain: str, message: str):
        """Envía un log al usuario en tiempo real."""
        try:
            self.supabase.table("hunter_logs").insert({
                'user_id': user_id,
                'domain': domain,
                'level': level,
                'action': action,
                'message': message,
            }).execute()
        except Exception as e:
            log.error(f"Error enviando log: {e}")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Entry point."""
    # Log muy visible al inicio
    print("\n" + "="*70)
    print("DOMAIN HUNTER WORKER - STARTING UP")
    print("="*70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    env = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    print(f"Environment: {env}")
    print("="*70 + "\n")
    
    worker = DomainHunterWorker()
    await worker.start()


if __name__ == "__main__":
    print("\n*** DOMAIN HUNTER WORKER - ENTRY POINT REACHED ***\n")
    asyncio.run(main())

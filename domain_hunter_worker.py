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

# Batch size: cuántos dominios agregar a la vez
DOMAIN_BATCH_SIZE = 10  # Aumentado de 5 a 10 para mayor throughput

# User Agents para rotar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Blacklist de dominios a ignorar
BLACKLIST_DOMAINS = {
    'google', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
    'mercadolibre', 'olx', 'zonaprop', 'argenprop', 'properati',
    'wikipedia', 'wikidata', 'pinterest', 'tiktok',
}

# =============================================================================
# LISTAS DE ROTACIÓN AUTOMÁTICA
# =============================================================================

# 50+ nichos con potencial de email y ventas
NICHOS = [
    # Servicios profesionales
    "inmobiliarias", "estudios contables", "estudios juridicos", "agencias de marketing",
    "consultoras", "agencias de diseño", "estudios de arquitectura", "desarrolladores web",
    "consultoras IT", "agencias SEO", "agencias de publicidad",
    
    # Servicios locales
    "gimnasios", "centros de estetica", "peluquerias", "spa", "clinicas dentales",
    "clinicas veterinarias", "talleres mecanicos", "lavaderos de autos", "cerrajerias",
    "empresas de limpieza", "empresas de mudanzas", "empresas de seguridad",
    
    # Retail y comercio
    "tiendas de ropa", "joyerias", "opticas", "librerias", "jugueterias",
    "ferreterias", "viveros", "pet shops", "tiendas de deportes",
    
    # Gastronomía
    "restaurantes", "cafeterias", "panaderias", "pizzerias", "hamburgueserias",
    "heladerias", "bares", "catering",
    
    # Salud y bienestar
    "centros medicos", "laboratorios", "kinesiologos", "nutricionistas",
    "psicologos", "centros de yoga", "centros de pilates",
    
    # Educación
    "institutos de idiomas", "academias de arte", "escuelas de musica",
    "centros de capacitacion", "guarderias",
    
    # Otros
    "hoteles", "hostels", "agencias de turismo", "rent a car", "fotografos",
    "organizadores de eventos", "floristas", "imprentas", "graficas"
]

# Ciudades principales de países latinoamericanos de habla hispana
CIUDADES_POR_PAIS = {
    "Argentina": [
        "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "San Miguel de Tucumán",
        "La Plata", "Mar del Plata", "Salta", "Santa Fe", "San Juan",
        "Resistencia", "Neuquén", "Bahía Blanca", "Paraná"
    ],
    "México": [
        "Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana",
        "León", "Juárez", "Zapopan", "Mérida", "Querétaro",
        "San Luis Potosí", "Aguascalientes", "Hermosillo", "Saltillo"
    ],
    "Colombia": [
        "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
        "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Manizales"
    ],
    "Chile": [
        "Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta",
        "Temuco", "Rancagua", "Talca", "Viña del Mar"
    ],
    "Perú": [
        "Lima", "Arequipa", "Trujillo", "Chiclayo", "Cusco",
        "Piura", "Iquitos", "Huancayo", "Tacna"
    ],
    "Ecuador": [
        "Quito", "Guayaquil", "Cuenca", "Ambato", "Manta", "Portoviejo"
    ],
    "Bolivia": [
        "La Paz", "Santa Cruz", "Cochabamba", "Sucre", "Tarija"
    ],
    "Paraguay": [
        "Asunción", "Ciudad del Este", "Encarnación", "Pedro Juan Caballero"
    ],
    "Uruguay": [
        "Montevideo", "Salto", "Paysandú", "Maldonado", "Rivera"
    ],
    "Venezuela": [
        "Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay"
    ],
    "Costa Rica": [
        "San José", "Alajuela", "Cartago", "Heredia", "Limón"
    ],
    "Panamá": [
        "Ciudad de Panamá", "Colón", "David", "La Chorrera"
    ],
    "Guatemala": [
        "Ciudad de Guatemala", "Quetzaltenango", "Escuintla", "Antigua Guatemala"
    ],
    "Honduras": [
        "Tegucigalpa", "San Pedro Sula", "Choloma", "La Ceiba"
    ],
    "El Salvador": [
        "San Salvador", "Santa Ana", "San Miguel", "Soyapango"
    ],
    "Nicaragua": [
        "Managua", "León", "Masaya", "Granada"
    ],
    "República Dominicana": [
        "Santo Domingo", "Santiago", "La Romana", "San Pedro de Macorís"
    ]
}

PAISES = list(CIUDADES_POR_PAIS.keys())

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
        log.info("\n" + "="*60)
        log.info("🔍 DOMAIN HUNTER WORKER - Iniciando")
        log.info("="*60 + "\n")
        
        if not self.serpapi_key:
            log.error("❌ SERPAPI_KEY no configurada en .env")
            log.error("   Consigue tu key gratis en: https://serpapi.com/")
            return
        
        log.info("✅ SerpAPI configurada")
        log.info(f"⏱️  Check de usuarios cada {CHECK_USERS_INTERVAL}s")
        log.info(f"⏱️  Delay entre búsquedas: {MIN_DELAY_BETWEEN_SEARCHES}-{MAX_DELAY_BETWEEN_SEARCHES}s")
        log.info(f"📦 Batch size: {DOMAIN_BATCH_SIZE} dominios\n")
        
        try:
            await self._main_loop()
        except KeyboardInterrupt:
            log.info("\n\n⚠️  Detenido por el usuario")
        finally:
            log.info("✅ Worker cerrado correctamente")
    
    async def _main_loop(self):
        """Loop principal del worker."""
        while True:
            try:
                # 1. Obtener usuarios con bot habilitado
                await self._update_active_users()
                
                if not self.active_users:
                    log.info("😴 No hay usuarios con bot habilitado. Esperando...")
                    await asyncio.sleep(CHECK_USERS_INTERVAL)
                    continue
                
                # 2. Procesar cada usuario activo
                for user_id, config in self.active_users.items():
                    log.info(f"\n🎯 Usuario: {user_id[:8]}... | Rotación automática activada")
                    
                    # Buscar dominios para este usuario
                    domains = await self._search_domains_for_user(user_id, config)
                    
                    if domains:
                        log.info(f"✅ Encontrados {len(domains)} dominios válidos")
                        # Guardar dominios en Supabase
                        await self._save_domains_to_supabase(user_id, domains)
                        
                        # Log de progreso
                        await self._log_to_user(
                            user_id=user_id,
                            level="success",
                            action="domain_added",
                            domain="system",
                            message=f"✅ {len(domains)} dominios nuevos agregados a la cola"
                        )
                    else:
                        log.warning(f"⚠️  No se encontraron dominios válidos en esta búsqueda")
                    
                    # Delay antes de procesar el siguiente usuario
                    await asyncio.sleep(random.randint(5, 15))
                
                # 3. Delay antes de la siguiente ronda
                await asyncio.sleep(CHECK_USERS_INTERVAL)
                
            except Exception as e:
                log.error(f"❌ Error en loop principal: {e}")
                await asyncio.sleep(30)
    
    async def _update_active_users(self):
        """Obtiene usuarios con bot habilitado desde Supabase."""
        try:
            response = self.supabase.table("hunter_configs")\
                .select("*")\
                .eq("bot_enabled", True)\
                .execute()
            
            # Actualizar diccionario de usuarios activos
            self.active_users = {
                config['user_id']: config 
                for config in response.data
            }
            
            if self.active_users:
                log.info(f"👥 {len(self.active_users)} usuario(s) con bot activo")
            
        except Exception as e:
            log.error(f"❌ Error obteniendo usuarios: {e}")
    
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
        
        query = f"{nicho} en {ciudad} {pais}"
        start_result = current_page * 10  # SerpAPI paginación
        
        log.info(f"🎯 Rotación: {nicho} | {ciudad}, {pais} | Página {current_page + 1}")
        log.info(f"🔍 Query SerpAPI: \"{query}\"")
        
        try:
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
                # No hay más resultados - marcar como agotada y avanzar
                await self._mark_combination_exhausted(user_id, nicho, ciudad, pais)
                log.info(f"🏁 Combinación agotada. Rotando a siguiente...")
            else:
                # Hay resultados - incrementar página para próxima búsqueda
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
        """Verifica si un dominio es válido y no está en blacklist."""
        if not domain or len(domain) < 4:
            return False
        
        # Verificar blacklist
        for blacklisted in BLACKLIST_DOMAINS:
            if blacklisted in domain:
                return False
        
        # Verificar que tenga al menos un punto
        if '.' not in domain:
            return False
        
        # Verificar que no sea un link interno de Google
        if 'google' in domain:
            return False
        
        return True
    
    async def _save_domains_to_supabase(self, user_id: str, domains: List[str]):
        """Guarda dominios en la tabla leads del usuario."""
        try:
            leads_data = [
                {
                    'user_id': user_id,
                    'domain': domain,
                    'status': 'pending',
                }
                for domain in domains
            ]
            
            # Upsert para evitar duplicados
            self.supabase.table("leads").upsert(
                leads_data,
                on_conflict='user_id,domain'
            ).execute()
            
            log.info(f"💾 {len(domains)} dominios guardados en Supabase")
            
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
        Estrategia: rotar ciudad dentro del mismo país/nicho, luego país, luego nicho.
        """
        try:
            # Rotar ciudad dentro del mismo país
            ciudades = CIUDADES_POR_PAIS[current_pais]
            current_index = ciudades.index(current_ciudad) if current_ciudad in ciudades else -1
            
            if current_index < len(ciudades) - 1:
                # Siguiente ciudad en el mismo país
                next_ciudad = ciudades[current_index + 1]
                next_pais = current_pais
                next_nicho = current_nicho
            else:
                # Cambiar de país
                pais_index = PAISES.index(current_pais) if current_pais in PAISES else -1
                
                if pais_index < len(PAISES) - 1:
                    # Siguiente país
                    next_pais = PAISES[pais_index + 1]
                    next_ciudad = CIUDADES_POR_PAIS[next_pais][0]  # Primera ciudad del nuevo país
                    next_nicho = current_nicho
                else:
                    # Cambiar de nicho y resetear país
                    nicho_index = NICHOS.index(current_nicho) if current_nicho in NICHOS else -1
                    next_nicho = NICHOS[(nicho_index + 1) % len(NICHOS)]  # Circular
                    next_pais = PAISES[0]
                    next_ciudad = CIUDADES_POR_PAIS[next_pais][0]
            
            # Verificar si ya existe
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
                
                log.info(f"➕ Nueva combinación: {next_nicho} | {next_ciudad}, {next_pais}")
            
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
    worker = DomainHunterWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())

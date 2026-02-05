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
MIN_DELAY_BETWEEN_SEARCHES = 30  # Mínimo 30s entre búsquedas
MAX_DELAY_BETWEEN_SEARCHES = 90  # Máximo 90s entre búsquedas

# Cada cuánto checar por usuarios con bot enabled (en segundos)
CHECK_USERS_INTERVAL = 60  # 1 minuto

# Batch size: cuántos dominios agregar a la vez
DOMAIN_BATCH_SIZE = 5

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
                    log.info(f"\n🎯 Usuario: {user_id[:8]}... | Nicho: {config['nicho']}")
                    
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
        Busca dominios en Google para un usuario específico usando SerpAPI.
        
        Args:
            user_id: ID del usuario
            config: Configuración del usuario (nicho, ciudades, pais)
        
        Returns:
            Lista de dominios encontrados (hasta DOMAIN_BATCH_SIZE)
        """
        nicho = config.get('nicho', 'inmobiliarias')
        ciudades = config.get('ciudades', ['Buenos Aires'])
        pais = config.get('pais', 'Argentina')
        
        # Si ciudades es un string de Postgres array, parsearlo
        if isinstance(ciudades, str):
            ciudades = ciudades.replace('{', '').replace('}', '').split(',')
            ciudades = [c.strip() for c in ciudades if c.strip()]
        
        domains_found: Set[str] = set()
        
        # Generar query de búsqueda
        ciudad = random.choice(ciudades) if ciudades else 'Buenos Aires'
        query = f"{nicho} en {ciudad} {pais}"
        
        # Obtener página actual para esta combinación user+ciudad
        pagination_key = (user_id, ciudad)
        current_page = self.search_pagination.get(pagination_key, 0)
        start_result = current_page * 10  # SerpAPI usa "start" (0, 10, 20, 30...)
        
        log.info(f"🔍 Buscando en Google vía SerpAPI: \"{query}\" (página {current_page + 1})")
        
        try:
            # Configurar búsqueda con SerpAPI
            params = {
                "q": query,
                "location": f"{ciudad}, {pais}",
                "hl": "es",
                "gl": "ar",
                "num": 20,  # Más resultados = más dominios
                "start": start_result,  # Paginación: 0, 10, 20, 30...
                "api_key": self.serpapi_key
            }
            
            # Ejecutar búsqueda (sincrónica, por eso usamos asyncio.to_thread)
            search = await asyncio.to_thread(GoogleSearch(params).get_dict)
            
            # Extraer resultados orgánicos
            organic_results = search.get("organic_results", [])
            log.info(f"📊 SerpAPI devolvió {len(organic_results)} resultados")
            
            total_checked = 0
            total_filtered = 0
            
            for result in organic_results:
                link = result.get("link")
                if not link:
                    continue
                
                total_checked += 1
                
                # Extraer dominio
                domain = self._extract_domain(link)
                if domain:
                    if self._is_valid_domain(domain):
                        domains_found.add(domain)
                        log.info(f"  ✅ {domain}")
                        
                        # Si llegamos al batch size, parar
                        if len(domains_found) >= DOMAIN_BATCH_SIZE:
                            break
                    else:
                        total_filtered += 1
                        log.debug(f"  ❌ Filtrado: {domain}")
            
            log.info(f"📈 Revisados: {total_checked} | Filtrados: {total_filtered} | Válidos: {len(domains_found)}")
            
            # Incrementar página para la próxima búsqueda en esta ciudad
            if len(domains_found) > 0:
                self.search_pagination[pagination_key] = current_page + 1
                log.info(f"📄 Próxima búsqueda en {ciudad}: página {current_page + 2}")
            
            # Delay antes de la siguiente búsqueda
            delay = random.randint(MIN_DELAY_BETWEEN_SEARCHES, MAX_DELAY_BETWEEN_SEARCHES)
            log.info(f"⏳ Delay de {delay}s antes de la siguiente búsqueda...")
            await asyncio.sleep(delay)
            
            return list(domains_found)
            
        except Exception as e:
            log.error(f"❌ Error buscando dominios con SerpAPI: {e}")
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

"""
Domain Hunter - Scraper automático de Google para conseguir dominios 24/7

Este script busca dominios en Google de forma continua con delays largos
para evitar bloqueos. Puede correr durante horas/días acumulando miles de dominios.

Uso:
    python domain_hunter.py --nicho "inmobiliarias" --pais "Argentina" --ciudades "Rosario,Buenos Aires,Córdoba"
    
    O configurar directamente en el código y ejecutar:
    python domain_hunter.py
"""

import asyncio
import argparse
import random
import os
import re
from datetime import datetime
from typing import List, Set
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright, Browser, Page
from dotenv import load_dotenv
from supabase import create_client, Client

from src.utils.logger import log


class DomainHunter:
    """
    Scraper automático de Google para conseguir dominios de forma masiva.
    Diseñado para correr 24/7 con delays largos para evitar bloqueos.
    """
    
    # User agents rotativos para parecer diferentes usuarios
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(
        self,
        nicho: str,
        pais: str = "Argentina",
        ciudades: List[str] = None,
        user_id: str = None,
        min_delay: int = 30,
        max_delay: int = 90,
        max_domains: int = 10000
    ):
        """
        Inicializar el hunter.
        
        Args:
            nicho: Tipo de negocio (ej: "inmobiliarias", "agencias de marketing")
            pais: País a buscar
            ciudades: Lista de ciudades (opcional)
            user_id: ID del usuario en Supabase (para guardar los dominios)
            min_delay: Delay mínimo entre búsquedas (segundos)
            max_delay: Delay máximo entre búsquedas (segundos)
            max_domains: Máximo de dominios a conseguir antes de detenerse
        """
        self.nicho = nicho
        self.pais = pais
        self.ciudades = ciudades or ["Buenos Aires", "Córdoba", "Rosario", "Mendoza"]
        self.user_id = user_id
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_domains = max_domains
        
        # Estado
        self.domains_found: Set[str] = set()
        self.search_count = 0
        self.browser: Browser = None
        
        # Supabase (opcional - para guardar automáticamente)
        self.supabase: Client = None
        if user_id:
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
    
    async def start(self) -> None:
        """Iniciar el hunting de dominios 24/7."""
        log.info("🎯 Domain Hunter iniciado")
        log.info(f"   Nicho: {self.nicho}")
        log.info(f"   País: {self.pais}")
        log.info(f"   Ciudades: {', '.join(self.ciudades)}")
        log.info(f"   Delay: {self.min_delay}-{self.max_delay}s entre búsquedas")
        log.info(f"   Objetivo: {self.max_domains} dominios")
        log.separator()
        
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                await self._run_loop()
            finally:
                await self.browser.close()
    
    async def _run_loop(self) -> None:
        """Loop principal de búsquedas."""
        # Generar variaciones de búsquedas
        search_queries = self._generate_search_queries()
        log.info(f"📝 {len(search_queries)} búsquedas generadas\n")
        
        for query in search_queries:
            if len(self.domains_found) >= self.max_domains:
                log.success(f"\n✅ Objetivo alcanzado: {len(self.domains_found)} dominios conseguidos")
                break
            
            # Realizar búsqueda
            await self._search_google(query)
            
            # Delay aleatorio para parecer humano
            delay = random.randint(self.min_delay, self.max_delay)
            log.info(f"💤 Esperando {delay}s antes de la siguiente búsqueda...")
            log.info(f"   (Progreso: {len(self.domains_found)}/{self.max_domains} dominios)\n")
            await asyncio.sleep(delay)
        
        # Guardar resultados finales
        await self._save_results()
    
    def _generate_search_queries(self) -> List[str]:
        """Generar variaciones de búsquedas para maximizar resultados."""
        queries = []
        
        # Variaciones del nicho
        nicho_variations = [
            self.nicho,
            f"{self.nicho} {self.pais}",
        ]
        
        # Por ciudad
        for ciudad in self.ciudades:
            for nicho_var in nicho_variations:
                queries.append(f"{nicho_var} en {ciudad}")
                queries.append(f"{nicho_var} {ciudad}")
        
        # Sin ciudad (genérico del país)
        for nicho_var in nicho_variations:
            queries.append(f"{nicho_var} {self.pais}")
        
        # Variaciones con palabras clave
        keywords = ["contacto", "servicios", "empresa", "profesional"]
        for keyword in keywords[:2]:  # Solo 2 para no hacer demasiadas
            queries.append(f"{self.nicho} {keyword} {self.pais}")
        
        # Shuffle para variar el orden
        random.shuffle(queries)
        
        return queries
    
    async def _search_google(self, query: str) -> None:
        """
        Realizar una búsqueda en Google y extraer dominios.
        
        Args:
            query: Término de búsqueda
        """
        self.search_count += 1
        log.info(f"🔍 Búsqueda #{self.search_count}: \"{query}\"")
        
        context = await self.browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()
        
        try:
            # Ir a Google
            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=50"
            await page.goto(google_url, timeout=30000, wait_until='load')
            
            # Esperar un poco (simular lectura humana)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Extraer todos los enlaces de resultados
            links = await page.evaluate('''() => {
                const results = document.querySelectorAll('a[href]');
                return Array.from(results)
                    .map(a => a.href)
                    .filter(href => href.includes('/url?q=') || href.startsWith('http'))
                    .slice(0, 50);
            }''')
            
            # Procesar enlaces
            new_domains = 0
            for link in links:
                domain = self._extract_domain_from_google_link(link)
                if domain and self._is_valid_domain(domain):
                    if domain not in self.domains_found:
                        self.domains_found.add(domain)
                        new_domains += 1
                        
                        # Guardar en Supabase inmediatamente (opcional)
                        if self.supabase and self.user_id:
                            await self._save_to_supabase(domain)
            
            log.success(f"   ✓ Encontrados {new_domains} dominios nuevos (Total: {len(self.domains_found)})")
            
        except Exception as e:
            log.error(f"   ✗ Error en búsqueda: {str(e)[:100]}")
        finally:
            await context.close()
    
    def _extract_domain_from_google_link(self, link: str) -> str:
        """Extraer dominio limpio desde un link de Google."""
        try:
            # Links de Google tienen formato: /url?q=https://dominio.com&sa=...
            if '/url?q=' in link:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                if 'q' in params:
                    real_url = params['q'][0]
                    return self._extract_domain(real_url)
            else:
                return self._extract_domain(link)
        except:
            return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extraer solo el dominio de una URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.lower().strip()
            
            # Limpiar
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except:
            return ""
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Verificar que sea un dominio válido y no basura."""
        if not domain or len(domain) < 4:
            return False
        
        # Blacklist de dominios de Google, redes sociales, etc.
        blacklist = [
            'google.com', 'youtube.com', 'facebook.com', 'instagram.com',
            'twitter.com', 'linkedin.com', 'wikipedia.org', 'mercadolibre',
            'olx.com', 'zonaprop.com', 'properati.com', 'trovit',
            'maps.google', 'accounts.google', 'play.google', 'support.google'
        ]
        
        for blocked in blacklist:
            if blocked in domain:
                return False
        
        # Debe tener al menos un punto
        if '.' not in domain:
            return False
        
        # No debe tener espacios ni caracteres raros
        if ' ' in domain or '[' in domain or ']' in domain:
            return False
        
        return True
    
    async def _save_to_supabase(self, domain: str) -> None:
        """Guardar dominio en Supabase (tabla leads)."""
        try:
            self.supabase.table('leads').insert({
                'user_id': self.user_id,
                'domain': domain,
                'status': 'pending'
            }).execute()
            log.info(f"      💾 Guardado en Supabase: {domain}")
        except Exception as e:
            # Probablemente duplicado - ignorar
            if 'duplicate' not in str(e).lower():
                log.warning(f"      ⚠️  Error guardando {domain}: {str(e)[:50]}")
    
    async def _save_results(self) -> None:
        """Guardar todos los dominios en un archivo."""
        filename = f"domains_{self.nicho.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            for domain in sorted(self.domains_found):
                f.write(f"{domain}\n")
        
        log.success(f"\n✅ Resultados guardados en: {filename}")
        log.success(f"✅ Total de dominios únicos: {len(self.domains_found)}")
        log.success(f"✅ Búsquedas realizadas: {self.search_count}")


async def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description='Domain Hunter - Scraper 24/7 de dominios desde Google')
    parser.add_argument('--nicho', type=str, help='Tipo de negocio (ej: inmobiliarias, agencias de marketing)')
    parser.add_argument('--pais', type=str, help='País')
    parser.add_argument('--ciudades', type=str, help='Ciudades separadas por coma (ej: Rosario,Córdoba)')
    parser.add_argument('--user-id', type=str, help='User ID de Supabase (para guardar automáticamente)')
    parser.add_argument('--min-delay', type=int, help='Delay mínimo entre búsquedas (segundos)')
    parser.add_argument('--max-delay', type=int, help='Delay máximo entre búsquedas (segundos)')
    parser.add_argument('--max-domains', type=int, help='Máximo de dominios a conseguir')
    
    args = parser.parse_args()
    
    # Si no se pasaron argumentos, cargar desde config file
    if not args.nicho:
        try:
            from domain_hunter_config import (
                NICHO, PAIS, CIUDADES, USER_ID, 
                MIN_DELAY_SECONDS, MAX_DELAY_SECONDS, MAX_DOMAINS
            )
            print("\n" + "="*60)
            print("📝 Usando configuración de domain_hunter_config.py")
            print("="*60 + "\n")
            
            nicho = NICHO
            pais = PAIS
            ciudades = CIUDADES
            user_id = USER_ID
            min_delay = MIN_DELAY_SECONDS
            max_delay = MAX_DELAY_SECONDS
            max_domains = MAX_DOMAINS
        except ImportError:
            print("\n" + "="*60)
            print("⚠️  No se encontró domain_hunter_config.py")
            print("⚠️  Usando valores por defecto")
            print("="*60 + "\n")
            
            nicho = "inmobiliarias"
            pais = "Argentina"
            ciudades = ["Rosario", "Buenos Aires", "Córdoba", "Mendoza"]
            user_id = None
            min_delay = 30
            max_delay = 90
            max_domains = 5000
    else:
        nicho = args.nicho
        pais = args.pais or "Argentina"
        ciudades = args.ciudades.split(',') if args.ciudades else ["Buenos Aires"]
        user_id = args.user_id
        min_delay = args.min_delay or 30
        max_delay = args.max_delay or 90
        max_domains = args.max_domains or 10000
    
    # Crear y ejecutar el hunter
    hunter = DomainHunter(
        nicho=nicho,
        pais=pais,
        ciudades=ciudades,
        user_id=user_id,
        min_delay=min_delay,
        max_delay=max_delay,
        max_domains=max_domains
    )
    
    try:
        await hunter.start()
    except KeyboardInterrupt:
        log.info("\n\n⚠️  Detenido por el usuario")
        await hunter._save_results()


if __name__ == "__main__":
    asyncio.run(main())

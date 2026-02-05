"""
Scraper Service - Web scraping with Playwright.

This module handles the extraction of contact emails from websites
using Playwright for browser automation and BeautifulSoup for HTML parsing.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple
from uuid import UUID

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from src.domain.models import Lead, ScrapingResult
from src.utils.logger import log


class ScraperService:
    """
    Service for scraping contact information from websites.
    
    Uses Playwright for browser automation with concurrent tab management
    and BeautifulSoup for HTML parsing. Implements smart navigation to
    find contact pages and robust email extraction with junk filtering.
    """

    # Regex pattern for email extraction
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )

    # Patterns to identify junk/invalid emails
    JUNK_PATTERNS = [
        r'\.png',
        r'\.jpg',
        r'\.jpeg',
        r'\.gif',
        r'\.svg',
        r'\.webp',
        r'@2x',
        r'@3x',
        r'sentry',
        r'example\.com',
        r'example\.org',
        r'test\.com',
        r'localhost',
        r'wixpress',
        r'wix\.com',
        r'wordpress',
        r'@sentry',
        r'noreply',
        r'no-reply',
        r'mailer-daemon',
        r'postmaster',
    ]

    # Keywords to identify contact/about pages
    CONTACT_KEYWORDS = [
        'contact', 'contacto', 'kontakt', 'contato',
        'about', 'about-us', 'sobre', 'acerca',
        'team', 'equipo',
        'impressum',  # German legal page, often has contact
        'get-in-touch',
    ]
    
    # Common contact page paths to try for SPAs (Flutter, React, Vue, etc.)
    # These will be tried even if no links are found in the DOM
    COMMON_CONTACT_PATHS = [
        '/contacto',
        '/contact',
        '/contact-us',
        '/about',
        '/about-us',
        '/sobre-nosotros',
        '/nosotros',
        '/empresa',
        '/quienes-somos',
    ]

    def __init__(
        self,
        max_concurrent: int = 10,  # ⚡ Aumentado de 5 a 10
        timeout_seconds: int = 12,  # ⚡ Reducido de 20 a 12 segundos
        debug_mode: bool = False
    ) -> None:
        """
        Initialize the scraper service.
        
        Args:
            max_concurrent: Maximum number of concurrent browser tabs
            timeout_seconds: Timeout for page loads in seconds
            debug_mode: If True, saves HTML content to files for debugging
        """
        self.max_concurrent = max_concurrent
        self.timeout_ms = timeout_seconds * 1000
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._browser: Optional[Browser] = None
        self.debug_mode = debug_mode

    async def _get_browser(self) -> Browser:
        """Get or create the browser instance."""
        if self._browser is None or not self._browser.is_connected():
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
        return self._browser

    async def close(self) -> None:
        """Close the browser instance."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None

    def _save_debug_html(self, domain: str, html: str, page_type: str = "homepage") -> None:
        """
        Save HTML content to a file for debugging.
        
        Args:
            domain: The domain being scraped
            html: The HTML content
            page_type: Type of page (homepage, contact, etc.)
        """
        if not self.debug_mode:
            return
        
        try:
            # Create debug directory if it doesn't exist
            debug_dir = Path("debug_html")
            debug_dir.mkdir(exist_ok=True)
            
            # Sanitize domain for filename
            safe_domain = domain.replace('/', '_').replace(':', '_')
            filename = debug_dir / f"{safe_domain}_{page_type}.html"
            
            # Save HTML
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            log.info(f"🔍 HTML guardado en: {filename}")
        except Exception as e:
            log.warning(f"No se pudo guardar HTML de debug: {str(e)}")

    def _is_junk_email(self, email: str) -> bool:
        """
        Check if an email matches junk patterns.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email is junk, False otherwise
        """
        email_lower = email.lower()
        for pattern in self.JUNK_PATTERNS:
            if re.search(pattern, email_lower):
                return True
        return False

    def _extract_emails(self, html: str) -> Set[str]:
        """
        Extract valid email addresses from HTML content.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Set of valid email addresses (deduplicated)
        """
        # Find all potential emails
        potential_emails = self.EMAIL_PATTERN.findall(html)
        
        # Filter out junk emails
        valid_emails = set()
        for email in potential_emails:
            email = email.lower().strip()
            if not self._is_junk_email(email):
                valid_emails.add(email)
        
        return valid_emails

    async def _extract_emails_from_page(self, page: Page) -> Set[str]:
        """
        Extract emails using multiple strategies for SPAs.
        
        For sites like Flutter, React, Vue that render content dynamically,
        we try multiple approaches:
        1. Get inner text of the entire body
        2. Look for mailto: links
        3. Check aria-labels and other accessibility attributes
        4. Search in loaded JavaScript files (for Flutter CanvasKit)
        
        Args:
            page: Playwright page object
            
        Returns:
            Set of email addresses found
        """
        all_emails: Set[str] = set()
        
        try:
            # Strategy 1: Get all visible text from the page
            body_text = await page.evaluate('''() => {
                return document.body.innerText || document.body.textContent || '';
            }''')
            all_emails.update(self._extract_emails(body_text))
            
            # Strategy 2: Look for mailto: links
            mailto_emails = await page.evaluate('''() => {
                const links = document.querySelectorAll('a[href^="mailto:"]');
                return Array.from(links).map(a => a.href.replace('mailto:', '').split('?')[0]);
            }''')
            for email in mailto_emails:
                email = email.lower().strip()
                if email and not self._is_junk_email(email):
                    all_emails.add(email)
            
            # Strategy 3: Check aria-labels and titles for emails
            aria_text = await page.evaluate('''() => {
                const elements = document.querySelectorAll('[aria-label], [title]');
                let text = '';
                elements.forEach(el => {
                    text += ' ' + (el.getAttribute('aria-label') || '');
                    text += ' ' + (el.getAttribute('title') || '');
                });
                return text;
            }''')
            all_emails.update(self._extract_emails(aria_text))
            
            # Strategy 4: Get full HTML as fallback
            html = await page.content()
            all_emails.update(self._extract_emails(html))
            
            # Strategy 5: For Flutter CanvasKit - search in loaded JS files
            # The compiled Dart code often contains hardcoded strings
            if not all_emails:
                js_emails = await self._extract_emails_from_js(page)
                all_emails.update(js_emails)
            
        except Exception as e:
            log.warning(f"Error en extracción avanzada: {str(e)[:100]}")
        
        return all_emails

    async def _extract_emails_from_js(self, page: Page) -> Set[str]:
        """
        Extract emails from JavaScript source files.
        
        For Flutter CanvasKit sites, the emails are often hardcoded in the
        compiled main.dart.js file. This method fetches and searches it.
        
        Args:
            page: Playwright page object
            
        Returns:
            Set of email addresses found in JS files
        """
        all_emails: Set[str] = set()
        
        try:
            # Find all script sources
            script_urls = await page.evaluate('''() => {
                const scripts = document.querySelectorAll('script[src]');
                return Array.from(scripts)
                    .map(s => s.src)
                    .filter(src => src.includes('.js') && !src.includes('google'));
            }''')
            
            # Also look for the Flutter main.dart.js specifically
            base_url = page.url.rstrip('/').rsplit('/', 1)[0]
            if not any('main.dart.js' in url for url in script_urls):
                script_urls.append(f"{base_url}/main.dart.js")
            
            log.info(f"🔍 Buscando emails en {len(script_urls)} archivos JS...")
            
            for script_url in script_urls[:3]:  # Limit to 3 scripts
                try:
                    # Fetch the JavaScript file content
                    js_content = await page.evaluate('''async (url) => {
                        try {
                            const response = await fetch(url);
                            if (!response.ok) return '';
                            const text = await response.text();
                            // Only return a portion to avoid memory issues
                            // Look for email patterns in chunks
                            return text.substring(0, 500000);
                        } catch (e) {
                            return '';
                        }
                    }''', script_url)
                    
                    if js_content:
                        # Extract emails from JS content
                        js_emails = self._extract_emails(js_content)
                        if js_emails:
                            log.info(f"  ↳ Encontrados {len(js_emails)} emails en JS")
                            all_emails.update(js_emails)
                            
                except Exception:
                    continue
                    
        except Exception as e:
            log.warning(f"Error buscando en JS: {str(e)[:50]}")
        
        return all_emails

    def _is_spa_site(self, html: str) -> bool:
        """
        Detect if a site is a Single Page Application (Flutter, React, Vue, etc.)
        
        Args:
            html: Raw HTML content
            
        Returns:
            True if the site appears to be a SPA
        """
        spa_indicators = [
            'flutter',
            'flt-renderer',
            'canvaskit',
            '__NEXT_DATA__',  # Next.js
            '__NUXT__',       # Nuxt.js
            'ng-version',     # Angular
            'data-reactroot', # React
            'data-v-',        # Vue.js
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in spa_indicators)

    def _extract_title(self, html: str) -> Optional[str]:
        """
        Extract the page title from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Page title or None if not found
        """
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            # Clean up the title
            title = title_tag.string.strip()
            # Truncate if too long
            return title[:200] if len(title) > 200 else title
        return None

    async def _find_contact_links(self, page: Page) -> List[str]:
        """
        Find links to contact/about pages.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of URLs to potential contact pages
        """
        links = []
        try:
            # Get all anchor elements
            anchors = await page.query_selector_all('a[href]')
            
            for anchor in anchors:
                href = await anchor.get_attribute('href')
                text = await anchor.inner_text()
                
                if not href:
                    continue
                
                # Check href and text for contact keywords
                href_lower = href.lower()
                text_lower = text.lower() if text else ''
                
                for keyword in self.CONTACT_KEYWORDS:
                    if keyword in href_lower or keyword in text_lower:
                        # Normalize the URL
                        if href.startswith('/'):
                            base_url = page.url.split('/')[0:3]
                            href = '/'.join(base_url) + href
                        elif not href.startswith('http'):
                            continue
                        
                        if href not in links:
                            links.append(href)
                        break
        except Exception:
            pass
        
        return links[:3]  # Limit to 3 contact pages

    async def _scrape_single(
        self,
        lead: Lead
    ) -> ScrapingResult:
        """
        Scrape a single domain for contact information.
        
        Args:
            lead: Lead object containing the domain to scrape
            
        Returns:
            ScrapingResult with extracted data or error
        """
        async with self.semaphore:
            browser = await self._get_browser()
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            all_emails: Set[str] = set()
            title: Optional[str] = None
            is_spa = False
            
            try:
                # Build the URL - handle domains that might have protocol
                domain = lead.domain
                if domain.startswith('http://') or domain.startswith('https://'):
                    url = domain
                    # Extract clean domain for logging
                    domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
                else:
                    url = f"https://{domain}"
                
                log.scraping(f"Iniciando scraping: {domain}")
                
                # Navigate to homepage
                await page.goto(url, timeout=self.timeout_ms, wait_until='load')  # ⚡ 'load' es más rápido que 'networkidle'
                
                # Wait a bit for any delayed JS
                await asyncio.sleep(0.8)  # ⚡ Reducido de 2s a 0.8s
                
                # Scroll down to trigger lazy loading
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(0.4)  # ⚡ Reducido de 1s a 0.4s
                
                # Scroll back up
                await page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(0.2)  # ⚡ Reducido de 0.5s a 0.2s
                
                # Get homepage content
                html = await page.content()
                self._save_debug_html(domain, html, "homepage")
                
                # Detect if it's a SPA
                is_spa = self._is_spa_site(html)
                if is_spa:
                    log.info(f"🔷 Detectado SPA (Flutter/React/Vue) en {domain}")
                
                # Extract title
                title = self._extract_title(html)
                
                # Use advanced extraction for SPAs, simple for regular sites
                if is_spa:
                    homepage_emails = await self._extract_emails_from_page(page)
                else:
                    homepage_emails = self._extract_emails(html)
                
                all_emails.update(homepage_emails)
                
                log.info(f"Homepage {domain}: encontrados {len(homepage_emails)} emails")
                if self.debug_mode and homepage_emails:
                    log.info(f"Emails en homepage: {', '.join(list(homepage_emails)[:3])}")
                
                # ⚡ Early exit: si encontramos email en homepage, limitar búsqueda en páginas de contacto
                contact_links = []
                if not homepage_emails:
                    # Solo buscar en páginas de contacto si NO encontramos email en homepage
                    contact_links = await self._find_contact_links(page)
                    
                    # If no links found and it's a SPA, try common paths
                    if not contact_links and is_spa:
                        log.info(f"Sin links en SPA, probando rutas comunes...")
                        base_url = url.rstrip('/')
                        contact_links = [f"{base_url}{path}" for path in self.COMMON_CONTACT_PATHS]
                    
                    log.info(f"Probando {len(contact_links)} URLs de contacto en {domain}")
                else:
                    log.info(f"⚡ Email encontrado en homepage, saltando búsqueda de contacto")
                
                for contact_url in contact_links:
                    try:
                        log.info(f"Visitando: {contact_url}")
                        
                        response = await page.goto(
                            contact_url,
                            timeout=self.timeout_ms,
                            wait_until='load'  # ⚡ 'load' es más rápido
                        )
                        
                        # Skip if page returned 404 or error
                        if response and response.status >= 400:
                            log.info(f"  ↳ Página no existe (HTTP {response.status})")
                            continue
                        
                        # Wait for JS
                        await asyncio.sleep(0.6)  # ⚡ Reducido de 1.5s a 0.6s
                        
                        # Scroll to load everything
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(0.2)  # ⚡ Reducido de 0.5s a 0.2s
                        
                        html = await page.content()
                        
                        # Save debug HTML
                        page_name = contact_url.split('/')[-1] or 'contact'
                        self._save_debug_html(domain, html, f"contact_{page_name}")
                        
                        # Use advanced extraction for SPAs
                        if is_spa:
                            contact_emails = await self._extract_emails_from_page(page)
                        else:
                            contact_emails = self._extract_emails(html)
                        
                        all_emails.update(contact_emails)
                        
                        log.info(f"  ↳ Encontrados {len(contact_emails)} emails")
                        if self.debug_mode and contact_emails:
                            log.info(f"  ↳ Emails: {', '.join(list(contact_emails)[:3])}")
                        
                        # Get title from contact page if homepage didn't have one
                        if not title:
                            title = self._extract_title(html)
                        
                        # If we found emails, we can stop looking
                        if contact_emails:
                            break
                            
                    except Exception as e:
                        # SPA navigation might throw errors for non-existent routes
                        if self.debug_mode:
                            log.warning(f"  ↳ Error: {str(e)[:50]}")
                        continue
                
                # Select the best email (prefer non-generic ones)
                best_email = self._select_best_email(all_emails)
                
                if best_email:
                    log.success(f"✉️  Email encontrado en {domain}: {best_email}")
                else:
                    log.warning(f"❌ No se encontró email en {domain} (Total encontrados: {len(all_emails)})")
                
                return ScrapingResult(
                    lead_id=lead.id,
                    domain=lead.domain,
                    success=True,
                    email=best_email,
                    meta_title=title
                )
                
            except PlaywrightTimeout:
                error_msg = f"Timeout al cargar {lead.domain}"
                log.error(error_msg)
                return ScrapingResult(
                    lead_id=lead.id,
                    domain=lead.domain,
                    success=False,
                    error=error_msg
                )
            except Exception as e:
                error_msg = f"Error scraping {lead.domain}: {str(e)}"
                log.error(error_msg)
                return ScrapingResult(
                    lead_id=lead.id,
                    domain=lead.domain,
                    success=False,
                    error=str(e)[:200]
                )
            finally:
                await context.close()

    def _select_best_email(self, emails: Set[str]) -> Optional[str]:
        """
        Select the best email from a set of candidates.
        
        Prioritizes emails that are more likely to be monitored
        (e.g., info@, contact@, hello@).
        
        Args:
            emails: Set of candidate emails
            
        Returns:
            Best email or None if set is empty
        """
        if not emails:
            return None
        
        # Priority prefixes (most likely to be monitored)
        priority_prefixes = [
            'info@', 'contact@', 'hello@', 'hola@',
            'sales@', 'ventas@', 'support@', 'soporte@',
            'admin@', 'office@', 'team@', 'equipo@',
        ]
        
        # Try to find a priority email
        for prefix in priority_prefixes:
            for email in emails:
                if email.startswith(prefix):
                    return email
        
        # Return any email if no priority match
        return next(iter(emails))

    async def scrape_batch(
        self,
        leads: List[Lead]
    ) -> List[ScrapingResult]:
        """
        Scrape multiple domains concurrently.
        
        Args:
            leads: List of Lead objects to scrape
            
        Returns:
            List of ScrapingResult objects
        """
        if not leads:
            return []
        
        log.info(f"Iniciando batch de scraping: {len(leads)} dominios")
        
        # Create tasks for concurrent execution
        tasks = [self._scrape_single(lead) for lead in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ScrapingResult(
                    lead_id=leads[i].id,
                    domain=leads[i].domain,
                    success=False,
                    error=str(result)[:200]
                ))
            else:
                processed_results.append(result)
        
        # Log summary
        successful = sum(1 for r in processed_results if r.success)
        with_email = sum(1 for r in processed_results if r.email)
        log.info(f"Batch completado: {successful}/{len(leads)} exitosos, {with_email} con email")
        
        return processed_results

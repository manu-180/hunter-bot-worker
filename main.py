"""
LeadSniper Worker - Main Orchestrator

This is the entry point for the LeadSniper backend worker.
It runs an infinite loop that:
1. Fetches pending domains from Supabase and scrapes them
2. Fetches emails queued for sending and sends them via Resend
3. Sleeps when there's no work to do

Usage:
    python main.py
"""

import asyncio
import os
import signal
import sys
from time import time
from typing import Optional

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from src.config import BotConfig
from src.infrastructure.supabase_repo import SupabaseRepository
from src.services.scraper import ScraperService
from src.services.mailer import MailerService
from src.services.hunter_logger import HunterLoggerService
from src.utils.logger import log
from src.utils.timezone import is_business_hours, format_argentina_time

# Centralized config (overrideable via env vars)
BUSINESS_HOURS_START = BotConfig.BUSINESS_HOURS_START
BUSINESS_HOURS_END = BotConfig.BUSINESS_HOURS_END
PAUSE_CHECK_INTERVAL = BotConfig.PAUSE_CHECK_INTERVAL


class TTLCache:
    """Simple cache with time-to-live expiration to prevent unbounded growth."""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict = {}
        self._ttl = ttl_seconds
    
    def get(self, key):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = (value, time())
    
    def clear(self):
        self._cache.clear()


class LeadSniperWorker:
    """
    Main orchestrator for the LeadSniper worker.
    
    Coordinates between the Supabase repository, scraper service,
    and mailer service to process leads through the pipeline.
    """

    def __init__(
        self,
        scrape_batch_size: int = BotConfig.SCRAPE_BATCH_SIZE,
        email_batch_size: int = BotConfig.EMAIL_BATCH_SIZE,
        idle_sleep_seconds: int = BotConfig.IDLE_SLEEP_SECONDS,
        heartbeat_interval: int = BotConfig.HEARTBEAT_INTERVAL,
    ) -> None:
        """
        Initialize the worker.
        
        Args:
            scrape_batch_size: Number of domains to scrape per cycle
            email_batch_size: Number of emails to send per cycle
            idle_sleep_seconds: Seconds to sleep when no work is found
            heartbeat_interval: Seconds between heartbeat logs
        """
        self.scrape_batch_size = scrape_batch_size
        self.email_batch_size = email_batch_size
        self.idle_sleep_seconds = idle_sleep_seconds
        self.heartbeat_interval = heartbeat_interval
        
        # Initialize services
        self.repo: Optional[SupabaseRepository] = None
        self.scraper: Optional[ScraperService] = None
        self.mailer: Optional[MailerService] = None
        self.hunter_logger: Optional[HunterLoggerService] = None
        
        # Cache for user configs (with TTL to prevent unbounded growth)
        self._config_cache = TTLCache(ttl_seconds=BotConfig.CONFIG_CACHE_TTL)
        
        # Control flags
        self._running = False

    async def initialize(self) -> None:
        """Initialize all services and connections."""
        log.info("Inicializando servicios...")
        
        try:
            self.repo = SupabaseRepository()
            log.success("Conexión a Supabase establecida")
        except Exception as e:
            log.error(f"Error conectando a Supabase: {e}")
            raise
        
        try:
            # Enable debug mode via environment variable
            debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
            
            self.scraper = ScraperService(
                max_concurrent=self.scrape_batch_size,
                timeout_seconds=BotConfig.SCRAPE_TIMEOUT,
                debug_mode=debug_mode
            )
            if debug_mode:
                log.warning("Modo DEBUG activado - se guardarán archivos HTML")
            log.success("Servicio de scraping inicializado")
        except Exception as e:
            log.error(f"Error inicializando scraper: {e}")
            raise
        
        try:
            self.mailer = MailerService(
                min_delay=BotConfig.EMAIL_MIN_DELAY,
                max_delay=BotConfig.EMAIL_MAX_DELAY,
            )
            log.success("Servicio de email inicializado")
        except Exception as e:
            log.error(f"Error inicializando mailer: {e}")
            raise
        
        try:
            self.hunter_logger = HunterLoggerService(self.repo.client)
            log.success("Servicio de Hunter Logger inicializado")
        except Exception as e:
            log.warning(f"Hunter Logger no disponible: {e}")
            self.hunter_logger = None
        
        log.success("Todos los servicios inicializados correctamente")
        log.separator()

    async def shutdown(self) -> None:
        """Gracefully shutdown all services. Idempotent - safe to call multiple times."""
        if not self._running and self.scraper is None:
            return  # Already shut down
        
        log.info("Cerrando servicios...")
        
        if self.scraper:
            await self.scraper.close()
            self.scraper = None
            log.info("Scraper cerrado")
        
        if self.mailer:
            await self.mailer.close()
            self.mailer = None
            log.info("Mailer cerrado")
        
        self._running = False
        log.success("Worker detenido correctamente")

    async def _process_scraping(self) -> int:
        """
        Process pending domains for scraping (multi-tenant).
        
        Returns:
            Number of domains processed
        """
        # Límite warm-up: solo cuenta envíos a dominios warm-up (warmup-*.getbotlode.com)
        sent_count = self.repo.get_sent_count(warmup_only=True)
        if sent_count >= BotConfig.MAX_TOTAL_EMAILS_SENT:
            return 0
        
        # Fetch pending domains from all users
        pending_leads = self.repo.fetch_pending_domains_all_users(limit=self.scrape_batch_size)
        
        if not pending_leads:
            return 0
        
        log.scraping(f"Procesando {len(pending_leads)} dominios pendientes")
        
        # Mark as scraping and log for each user
        for lead in pending_leads:
            self.repo.mark_as_scraping(lead.id)
            if self.hunter_logger and lead.user_id:
                self.hunter_logger.scrape_start(
                    user_id=str(lead.user_id),
                    domain=lead.domain,
                    lead_id=str(lead.id)
                )
        
        # Scrape all domains
        results = await self.scraper.scrape_batch(pending_leads)
        
        # Build O(1) lookup dict instead of O(n) search per result
        leads_by_id = {l.id: l for l in pending_leads}
        
        # Update database with results and log for each user
        for result in results:
            # Get the lead to access user_id (O(1) lookup)
            lead = leads_by_id.get(result.lead_id)
            user_id = str(lead.user_id) if lead and lead.user_id else None
            
            if result.success:
                self.repo.mark_as_scraped(
                    result.lead_id,
                    result.email,
                    result.meta_title
                )
                
                # Log result for user
                if self.hunter_logger and user_id:
                    if result.email:
                        self.hunter_logger.email_found(
                            user_id=user_id,
                            domain=result.domain,
                            email=result.email,
                            lead_id=str(result.lead_id)
                        )
                    else:
                        self.hunter_logger.email_not_found(
                            user_id=user_id,
                            domain=result.domain,
                            lead_id=str(result.lead_id)
                        )
            else:
                self.repo.mark_as_failed(
                    result.lead_id,
                    result.error or "Unknown scraping error"
                )
                
                if self.hunter_logger and user_id:
                    self.hunter_logger.scrape_error(
                        user_id=user_id,
                        domain=result.domain,
                        error=result.error or "Error desconocido",
                        lead_id=str(result.lead_id)
                    )
        
        return len(pending_leads)

    def _get_user_config(self, user_id: str):
        """Get user config from TTL cache or database."""
        cached = self._config_cache.get(user_id)
        if cached is not None:
            return cached
        config = self.repo.get_user_config(user_id)
        if config is not None:
            self._config_cache.set(user_id, config)
        return config

    async def _process_emails(self) -> int:
        """
        Process queued emails for sending (multi-tenant).
        
        Each user's emails are sent with their own Resend API key.
        
        HORARIO INTELIGENTE: Solo envía emails entre 8 AM - 18:00 (hora Argentina)
        para maximizar tasa de apertura y mantener profesionalismo.
        
        LÍMITE WARM-UP: Si ya se enviaron MAX_TOTAL_EMAILS_SENT (p. ej. 20), no se
        envían más emails para que Outlook/Gmail confíen en el dominio.
        
        Returns:
            Number of emails processed
        """
        # Reencolar leads warm-up enviados hace +24h para volver a enviarles al día siguiente
        self.repo.requeue_old_warmup_leads(hours=24)

        # Límite warm-up: solo cuenta envíos a dominios warm-up (warmup-*.getbotlode.com)
        sent_count = self.repo.get_sent_count(warmup_only=True)
        if sent_count >= BotConfig.MAX_TOTAL_EMAILS_SENT:
            log.info(
                f"⏸️ Límite warm-up alcanzado ({sent_count}/{BotConfig.MAX_TOTAL_EMAILS_SENT} enviados). "
                "No se envían más emails para confianza del dominio."
            )
            return 0
        
        # 🕐 VERIFICAR HORARIO LABORAL (DST-aware)
        if not is_business_hours(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
            log.warning(
                f"⏸️  FUERA DE HORARIO LABORAL (Argentina: {format_argentina_time()}). "
                f"Pausando envío de emails hasta las {BUSINESS_HOURS_START}:00 AM..."
            )
            return 0  # No procesar emails, pero continuar el loop
        
        # Fetch queued emails from all users
        queued_leads = self.repo.fetch_queued_emails_all_users(limit=self.email_batch_size)
        
        if not queued_leads:
            return 0
        
        log.email(f"Procesando {len(queued_leads)} emails en cola")
        
        # Process one at a time with delays
        for lead in queued_leads:
            user_id = str(lead.user_id) if lead.user_id else None
            
            if not user_id:
                log.warning(f"Lead {lead.id} sin user_id, saltando")
                continue
            
            # Get user's config
            config = self._get_user_config(user_id)
            
            if not config or not config.is_configured:
                # User hasn't configured Resend
                log.warning(f"Usuario {user_id} sin configuración de Resend")
                self.repo.mark_as_failed(lead.id, "Resend no configurado")
                
                if self.hunter_logger:
                    self.hunter_logger.config_missing(
                        user_id=user_id,
                        domain=lead.domain,
                        lead_id=str(lead.id)
                    )
                continue
            
            # Mark as sending (optimistic lock)
            if not self.repo.mark_as_sending(lead.id):
                log.info(f"Lead {lead.id} ya siendo procesado, saltando")
                continue  # Skip if already being processed
            
            # Log send start
            if self.hunter_logger:
                self.hunter_logger.send_start(
                    user_id=user_id,
                    domain=lead.domain,
                    email=lead.email or "",
                    lead_id=str(lead.id)
                )
            
            # Send email using user's config
            result = await self.mailer.send_with_config(lead, config)
            
            # Update database and log result
            if result.success:
                self.repo.mark_as_sent(lead.id)
                
                if self.hunter_logger:
                    self.hunter_logger.send_success(
                        user_id=user_id,
                        domain=lead.domain,
                        email=lead.email or "",
                        lead_id=str(lead.id)
                    )
            else:
                self.repo.mark_as_failed(
                    lead.id,
                    result.error or "Unknown email error"
                )
                
                if self.hunter_logger:
                    self.hunter_logger.send_failed(
                        user_id=user_id,
                        domain=lead.domain,
                        email=lead.email or "",
                        error=result.error or "Error desconocido",
                        lead_id=str(lead.id)
                    )
        
        return len(queued_leads)

    async def _log_heartbeat(self) -> None:
        """Log periodic heartbeat with current stats."""
        try:
            stats = self.repo.get_stats()
            pending = stats.get("pending", 0)
            queued = stats.get("queued_for_send", 0)
            log.heartbeat(pending, queued)
        except Exception as e:
            log.warning(f"Error obteniendo estadísticas: {e}")

    async def run(self) -> None:
        """
        Main worker loop.
        
        Continuously processes scraping and email tasks,
        sleeping when no work is available.
        """
        log.startup()
        
        await self.initialize()
        
        self._running = True
        cycles_without_work = 0
        last_heartbeat = 0
        error_streak = 0
        
        # Recover any leads stuck from previous crashes
        try:
            recovered = self.repo.recover_stuck_leads()
            if recovered:
                log.warning(f"Recuperados {recovered} leads stuck de sesión anterior")
        except Exception as e:
            log.warning(f"No se pudieron recuperar leads stuck: {e}")
        
        log.info("Worker iniciado - entrando en loop principal")
        log.separator()
        
        while self._running:
            try:
                work_done = 0
                
                # Process scraping tasks
                scraped = await self._process_scraping()
                work_done += scraped
                
                # Process email tasks
                emailed = await self._process_emails()
                work_done += emailed
                
                # Update heartbeat counter
                last_heartbeat += 1
                
                # Log heartbeat periodically
                if last_heartbeat >= (self.heartbeat_interval // self.idle_sleep_seconds):
                    await self._log_heartbeat()
                    last_heartbeat = 0
                
                # Reset error streak on successful cycle
                error_streak = 0
                
                # Sleep if no work was done
                if work_done == 0:
                    cycles_without_work += 1
                    
                    # Si estamos fuera de horario laboral, dormir más tiempo
                    if not is_business_hours(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
                        if cycles_without_work == 1:
                            log.info(f"⏸️  Fuera de horario laboral ({format_argentina_time()}). "
                                     f"Revisando cada {PAUSE_CHECK_INTERVAL}s...")
                        await asyncio.sleep(PAUSE_CHECK_INTERVAL)
                    else:
                        if cycles_without_work == 1:
                            log.info(f"Sin trabajo pendiente, esperando {self.idle_sleep_seconds}s...")
                        await asyncio.sleep(self.idle_sleep_seconds)
                else:
                    cycles_without_work = 0
                    
            except KeyboardInterrupt:
                log.warning("Interrupción recibida, cerrando...")
                break
            except Exception as e:
                error_streak += 1
                backoff = min(BotConfig.ERROR_BACKOFF_BASE * (2 ** min(error_streak, 5)),
                              BotConfig.ERROR_BACKOFF_MAX)
                log.error(f"Error en loop principal (streak {error_streak}): {e}")
                log.info(f"⏳ Backoff exponencial: {backoff:.0f}s")
                await asyncio.sleep(backoff)
        
        await self.shutdown()


# is_business_hours() imported from src.utils.timezone (handles DST correctly)


async def main() -> None:
    """Entry point for the worker."""
    worker = LeadSniperWorker()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        log.warning("Señal de terminación recibida...")
        worker._running = False
    
    # Register signal handlers (Unix only)
    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        log.warning("Interrupción por teclado")
        # Only shutdown here if run() didn't complete its own shutdown
        await worker.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker detenido por el usuario.")
    except Exception as e:
        print(f"\nError fatal: {e}")
        sys.exit(1)

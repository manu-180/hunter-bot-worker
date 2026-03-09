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
from src.services.wpp_followup_sender import WppFollowupSender
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
        self.wpp_sender: Optional[WppFollowupSender] = None
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

        # WPP follow-up sender es opcional: si faltan credenciales, funciona en modo silencioso
        self.wpp_sender = WppFollowupSender()

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

        if self.wpp_sender:
            await self.wpp_sender.close()
            self.wpp_sender = None
            log.info("WPP Follow-up Sender cerrado")
        
        self._running = False
        log.success("Worker detenido correctamente")

    async def _process_scraping(self) -> int:
        """
        Fase 1: raspa contactos del pool compartido que aún no tienen email.
        Opera sobre `contacts` (sin user_id) → todos los usuarios se benefician.
        """
        contacts_to_scrape = self.repo.fetch_contacts_to_scrape(limit=self.scrape_batch_size)
        if not contacts_to_scrape:
            return 0

        log.scraping(f"Scrapeando {len(contacts_to_scrape)} contactos del pool compartido")

        # Bloqueo optimista: marcar como 'scraping'
        locked = [c for c in contacts_to_scrape if self.repo.mark_contact_scraping(c.id)]
        if not locked:
            return 0

        # El Scraper acepta cualquier objeto con .id y .domain — Contact lo cumple
        results = await self.scraper.scrape_batch(locked)  # type: ignore[arg-type]

        contacts_by_id = {c.id: c for c in locked}

        for result in results:
            contact = contacts_by_id.get(result.lead_id)
            if result.success:
                self.repo.mark_contact_scraped(
                    result.lead_id,
                    result.email,
                    result.wpp_number,
                    result.meta_title,
                )
                if self.hunter_logger:
                    domain = contact.domain if contact else result.domain
                    if result.email:
                        self.hunter_logger.email_found(
                            user_id="shared",
                            domain=domain,
                            email=result.email,
                            lead_id=str(result.lead_id),
                        )
                    else:
                        self.hunter_logger.email_not_found(
                            user_id="shared",
                            domain=domain,
                            lead_id=str(result.lead_id),
                        )
            else:
                self.repo.mark_contact_scrape_failed(
                    result.lead_id,
                    result.error or "Error de scraping",
                )

        return len(locked)

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
        Fase 2 + 3: para cada usuario con bot activo:
          - Encola contactos del pool que aún no recibieron su email (populate_email_queue)
          - Envía los pendientes de email_queue con sus credenciales propias

        Respeta horario laboral (Argentina) y límite warm-up.
        """
        # 🕐 VERIFICAR HORARIO LABORAL (DST-aware)
        if not is_business_hours(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
            log.warning(
                f"⏸️  FUERA DE HORARIO LABORAL (Argentina: {format_argentina_time()}). "
                f"Pausando envío de emails hasta las {BUSINESS_HOURS_START}:00 AM..."
            )
            return 0

        # Obtener todos los usuarios con bot activo y configuración completa
        active_configs = self.repo.get_all_active_configs()
        if not active_configs:
            return 0

        total_sent = 0

        for config in active_configs:
            user_id = str(config.user_id)

            if not config.bot_enabled:
                continue
            if not config.is_configured:
                log.warning(f"[{user_id[:8]}] Sin configuración de Resend, saltando")
                continue

            # Límite warm-up por usuario (dominios warmup-*)
            sent_count = self.repo.get_sent_count(warmup_only=True)
            if sent_count >= BotConfig.MAX_TOTAL_EMAILS_SENT:
                log.info(
                    f"[{user_id[:8]}] Límite warm-up ({sent_count}/{BotConfig.MAX_TOTAL_EMAILS_SENT}), "
                    "saltando envíos."
                )
                continue

            # Encolar nuevos contactos del pool para este usuario (idempotente)
            new_queued = self.repo.populate_email_queue(
                user_id=user_id,
                config=config,
                limit=self.email_batch_size * 5,
            )
            if new_queued:
                log.info(f"[{user_id[:8]}] {new_queued} nuevos contactos encolados para envío")

            # Leer cola de envío de este usuario
            queue_items = self.repo.fetch_email_queue_for_user(
                user_id=user_id,
                limit=self.email_batch_size,
            )
            if not queue_items:
                continue

            log.email(f"[{user_id[:8]}] Enviando {len(queue_items)} emails desde {config.from_email}")

            for item in queue_items:
                contact = item.contact
                if not contact or not contact.email:
                    log.warning(f"[{user_id[:8]}] item {item.id} sin contacto/email, saltando")
                    continue

                # Bloqueo optimista
                if not self.repo.mark_queue_item_sending(item.id):
                    continue

                # Crear Lead temporal para el mailer (duck-typing sobre campos comunes)
                from src.domain.models import Lead, LeadStatus
                fake_lead = Lead(
                    id=item.id,
                    user_id=item.user_id,
                    domain=contact.domain or "",
                    email=contact.email,
                    wpp_number=contact.phone,
                    meta_title=contact.meta_title,
                    status=LeadStatus.QUEUED_FOR_SEND,
                    created_at=item.queued_at,
                    updated_at=item.queued_at,
                )

                if self.hunter_logger:
                    self.hunter_logger.send_start(
                        user_id=user_id,
                        domain=contact.domain or "",
                        email=contact.email,
                        lead_id=str(item.id),
                    )

                result = await self.mailer.send_with_config(fake_lead, config)

                if result.success:
                    self.repo.mark_queue_item_sent(item.id, resend_id=result.resend_id)
                    total_sent += 1

                    if self.hunter_logger:
                        self.hunter_logger.send_success(
                            user_id=user_id,
                            domain=contact.domain or "",
                            email=contact.email,
                            lead_id=str(item.id),
                        )

                    # WPP follow-up: si el contacto tiene teléfono, enviar WPP y registrar
                    if self.wpp_sender and contact.phone:
                        company_name = (
                            contact.meta_title
                            or contact.company_name
                            or (contact.domain or "").split(".")[0].replace("-", " ").title()
                        )
                        from_wpp = config.from_wpp_number or None
                        wpp_sent = await self.wpp_sender.send(
                            contact.phone, company_name, from_number=from_wpp
                        )
                        if wpp_sent:
                            # Registrar el WPP en whatsapp_outbox para que sea visible en Sender Bot
                            self.repo.register_wpp_followup(
                                contact_id=str(contact.id),
                                user_id=user_id,
                                phone=contact.phone,
                                company_name=company_name,
                                from_number=from_wpp or "",
                            )
                        if self.hunter_logger:
                            self.hunter_logger.wpp_followup_sent(
                                user_id=user_id,
                                domain=contact.domain or "",
                                wpp_number=contact.phone,
                                lead_id=str(item.id),
                            )
                else:
                    self.repo.mark_queue_item_failed(
                        item.id,
                        error=result.error or "Error desconocido",
                        attempt_count=item.attempt_count + 1,
                    )
                    if self.hunter_logger:
                        self.hunter_logger.send_failed(
                            user_id=user_id,
                            domain=contact.domain or "",
                            email=contact.email,
                            error=result.error or "Error desconocido",
                            lead_id=str(item.id),
                        )

        return total_sent

    async def _log_heartbeat(self) -> None:
        """Log periodic heartbeat con stats del nuevo modelo contacts + email_queue."""
        try:
            # Pool compartido
            contacts_pending = len(self.repo.fetch_contacts_to_scrape(limit=1000))
            # Cola de envío global (todos los usuarios)
            try:
                r = self.repo.client.table("email_queue").select("id", count="exact").eq("status", "pending").execute()
                email_pending = r.count or 0
            except Exception:
                email_pending = 0
            log.heartbeat(contacts_pending, email_pending)
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
        
        # Recuperar contactos/items stuck de sesiones anteriores
        try:
            rec_contacts = self.repo.recover_stuck_contacts()
            rec_leads = self.repo.recover_stuck_leads()
            if rec_contacts:
                log.warning(f"Recuperados {rec_contacts} contactos stuck (scraping → needs_scraping)")
            if rec_leads:
                log.warning(f"Recuperados {rec_leads} leads stuck (legacy table)")
        except Exception as e:
            log.warning(f"No se pudieron recuperar items stuck: {e}")
        
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
                    if cycles_without_work == 1:
                        if not is_business_hours(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
                            log.info(f"⏸️  Emails pausados (fuera de horario: {format_argentina_time()}). "
                                     f"Scraping sigue activo 24/7.")
                        else:
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

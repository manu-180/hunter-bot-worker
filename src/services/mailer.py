"""
Mailer Service - Email sending with Resend HTTP API.

This module handles sending outreach emails using the Resend HTTP API directly.
Uses httpx for async, thread-safe, per-request API key isolation (multi-tenant safe).
Implements human-like delays between sends to avoid spam flags.
"""

import asyncio
import base64
import html as html_lib
import mimetypes
import os
import random
import re
from pathlib import Path
from typing import List, Optional

import httpx
from dotenv import load_dotenv

from src.config import BotConfig
from src.domain.models import Lead, EmailResult, HunterConfig
from src.utils.logger import log
from src.utils.retry import retry_with_backoff

# Resend HTTP API endpoint
RESEND_API_URL = "https://api.resend.com/emails"

# Email format validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class MailerService:
    """
    Service for sending outreach emails via Resend.
    
    Features:
    - Configurable HTML email template
    - Human-like random delays between sends (10-30 seconds)
    - Error handling for rate limits and API errors
    - Detailed logging of all operations
    """

    # Default email subject (Railway deploy force: 2026-02-05)
    DEFAULT_SUBJECT = "Tu web está perdiendo clientes - Elevá su nivel ahora"
    _METALWAILERS_DOMAIN = "metalwailersinfo.com"

    def __init__(
        self,
        min_delay: int = 10,
        max_delay: int = 30
    ) -> None:
        """
        Initialize the mailer service.
        
        Args:
            min_delay: Minimum seconds to wait between emails
            max_delay: Maximum seconds to wait between emails
        """
        load_dotenv()
        
        self._default_api_key = os.getenv("RESEND_API_KEY")
        if not self._default_api_key:
            raise ValueError("RESEND_API_KEY must be set in environment variables")
        
        # Dominio de envío: getbotlode.com (verificado en Resend)
        _env_from = os.getenv("FROM_EMAIL", "manuel@getbotlode.com")
        self.from_email = self._normalize_from_email(_env_from) or "manuel@getbotlode.com"
        self.from_name = os.getenv("FROM_NAME", "Manuel de Botlode")
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # Reusable HTTP client with connection pooling (thread-safe for async)
        self._http_client = httpx.AsyncClient(timeout=30)
        
        # Modo: "launch" = formato simple (ganar confianza), "full" = formato completo BotLode
        self._email_mode = (os.getenv("HUNTER_EMAIL_MODE") or getattr(BotConfig, "EMAIL_MODE", "launch")).strip().lower()
        if self._email_mode not in ("launch", "full"):
            self._email_mode = "launch"
        self._launch_subject = os.getenv("HUNTER_LAUNCH_SUBJECT") or getattr(BotConfig, "LAUNCH_SUBJECT", "Consulta sobre su sitio web")
        
        # Load template according to mode (launch = simple, full = branded)
        self._template = self._load_template()
        self._metalwailers_image_src = self._resolve_metalwailers_image_src()

    def _load_template(self) -> str:
        """
        Load the email HTML template from external file.
        
        - EMAIL_TEMPLATE_PATH (env): fuerza un archivo concreto.
        - Modo "launch": templates/outreach_launch.html (simple, sin links, reply-bait).
        - Modo "full": templates/outreach.html (formato completo BotLode con CTA).
        """
        base = Path(__file__).parent.parent.parent / "templates"
        if not base.exists():
            base = Path("templates")
        
        # Custom path tiene prioridad
        template_path = os.getenv("EMAIL_TEMPLATE_PATH")
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                log.info(f"Template cargado desde: {template_path}")
                return f.read()
        
        # Según modo: launch (lanzamiento) o full (completo)
        if self._email_mode == "launch":
            for path in [base / "outreach_launch.html", Path("templates") / "outreach_launch.html"]:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        log.info(f"Template LAUNCH cargado: {path}")
                        return f.read()
        else:
            for path in [base / "outreach.html", Path("templates") / "outreach.html"]:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        log.info(f"Template FULL cargado: {path}")
                        return f.read()
        
        log.warning("Template HTML no encontrado, usando fallback mínimo")
        return """<!DOCTYPE html><html><body>
        <p>Hola,</p>
        <p>Soy {{sender_name}}. Vi tu web {{domain}}. ¿Te envío un demo?</p>
        <p>{{sender_name}}, Fundador</p>
        </body></html>"""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format before sending."""
        return bool(EMAIL_REGEX.match(email))

    # Dominio de envío (Resend); assistify.lat es viejo y no se usa
    _FROM_EMAIL_DEFAULT = "manuel@getbotlode.com"

    @classmethod
    def _normalize_from_email(cls, email: Optional[str]) -> str:
        """Asegura que el remitente use getbotlode.com; nunca assistify.lat."""
        if not email or not email.strip():
            return cls._FROM_EMAIL_DEFAULT
        e = email.strip().lower()
        if "assistify.lat" in e or "asstistify.lat" in e:
            return cls._FROM_EMAIL_DEFAULT
        return email.strip()

    @classmethod
    def _is_metalwailers_sender(cls, from_email: str) -> bool:
        email = (from_email or "").strip().lower()
        return email.endswith(f"@{cls._METALWAILERS_DOMAIN}")

    def _resolve_metalwailers_image_src(self) -> str:
        """
        Prioridad:
        1) METALWAILERS_EMAIL_IMAGE_URL (URL pública recomendada)
        2) METALWAILERS_EMAIL_IMAGE_PATH (archivo local convertido a data URI)
        3) Ruta por defecto del flyer en panel_bot/assets/images
        """
        url = (os.getenv("METALWAILERS_EMAIL_IMAGE_URL") or "").strip()
        if url:
            log.info("Metalwailers: usando imagen de email por URL pública")
            return url

        path_env = (os.getenv("METALWAILERS_EMAIL_IMAGE_PATH") or "").strip()
        repo_root = Path(__file__).resolve().parents[3]
        candidates: list[Path] = []
        if path_env:
            candidates.append(Path(path_env))
        candidates.extend([
            repo_root / "panel_bot" / "assets" / "images" / "WhatsApp Image 2026-03-08 at 1.35.07 AM.jpeg",
            Path("panel_bot/assets/images/WhatsApp Image 2026-03-08 at 1.35.07 AM.jpeg"),
        ])

        for path in candidates:
            try:
                if path.exists() and path.is_file():
                    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
                    raw = path.read_bytes()
                    b64 = base64.b64encode(raw).decode("ascii")
                    log.info(f"Metalwailers: imagen de email cargada desde {path}")
                    return f"data:{mime};base64,{b64}"
            except Exception as exc:
                log.warning(f"No se pudo leer imagen de Metalwailers en {path}: {exc}")

        log.warning(
            "Metalwailers: no se encontró imagen local ni URL. "
            "Definí METALWAILERS_EMAIL_IMAGE_URL para asegurar render en todos los clientes."
        )
        return ""

    def _render_metalwailers_image_email(self, sender_name: str, from_email: str) -> str:
        img_src = self._metalwailers_image_src
        if not img_src:
            # Fallback robusto si falta imagen.
            return f"""<!DOCTYPE html>
<html lang="es"><body style="margin:0;padding:24px;font-family:Arial,sans-serif;background:#f6f6f6;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e8e8e8;">
    <tr><td style="padding:24px;">
      <h2 style="margin:0 0 8px 0;color:#111;">{html_lib.escape(sender_name)}</h2>
      <p style="margin:0 0 12px 0;color:#222;">Te comparto información de nuestros servicios metalúrgicos.</p>
      <p style="margin:0;color:#555;font-size:13px;">{html_lib.escape(from_email)}</p>
    </td></tr>
  </table>
</body></html>"""

        return f"""<!DOCTYPE html>
<html lang="es">
<body style="margin:0;padding:0;background:#f3f3f3;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f3f3;">
    <tr>
      <td align="center" style="padding:20px 10px;">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" style="width:100%;max-width:680px;background:#ffffff;border:1px solid #e7e7e7;">
          <tr>
            <td style="padding:0;">
              <img src="{img_src}" alt="Metalwailers - Soluciones metalúrgicas a medida"
                   style="display:block;width:100%;height:auto;border:0;outline:none;text-decoration:none;" />
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # v8: placeholders del template para renderizado eficiente con loop
    _TEMPLATE_PLACEHOLDERS = (
        "{{company_name}}", "{{domain}}", "{{email}}",
        "{{sender_name}}", "{{sender_email}}", "{{calendar_link}}"
    )

    def _render_template(
        self,
        lead: Lead,
        config: Optional[HunterConfig] = None,
        sender_name: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> str:
        """
        Render the email template with lead data, sanitizing all values.
        
        v8: Usa dict mapping + single pass para reducir string allocations.
        Antes: 6 llamadas a .replace() = 6 strings intermedios.
        Ahora: 1 loop con reemplazos directos.
        
        Args:
            lead: Lead object with data to insert
            config: Optional user config for per-user settings
            
        Returns:
            Rendered HTML string
        """
        # Extract company name: prefer meta_title, else domain stem
        raw_domain = lead.domain.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
        company_name = lead.meta_title or raw_domain.split(".")[0].replace("-", " ").title()
        
        # Determine sender settings from config or environment
        if config:
            sender_name = sender_name or config.from_name or os.getenv("SENDER_NAME", self.from_name)
            calendar_link = config.calendar_link or os.getenv("CALENDAR_LINK", "https://www.botrive.com")
            from_email = from_email or self._normalize_from_email(config.from_email or self.from_email) or self.from_email
        else:
            sender_name = sender_name or os.getenv("SENDER_NAME", self.from_name)
            calendar_link = os.getenv("CALENDAR_LINK", "https://www.botrive.com")
            from_email = from_email or self.from_email

        # Template especial para Metalwailers: flyer de imagen completa.
        if self._is_metalwailers_sender(from_email):
            return self._render_metalwailers_image_email(sender_name, from_email)
        
        # v8: dict mapping para renderizado eficiente
        # NOTE: calendar_link usa quote=False porque va en href y & no debe escaparse
        replacements = {
            "{{company_name}}": html_lib.escape(company_name),
            "{{domain}}": html_lib.escape(lead.domain),
            "{{email}}": html_lib.escape(lead.email or ""),
            "{{sender_name}}": html_lib.escape(sender_name),
            "{{sender_email}}": html_lib.escape(from_email),
            "{{calendar_link}}": html_lib.escape(calendar_link, quote=False),
        }
        
        html = self._template
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, value)
        
        return html

    async def _send_email_http(self, params: dict, api_key: str) -> dict:
        """
        Send email via Resend HTTP API with per-request API key.
        
        Thread-safe and multi-tenant safe: each request carries
        its own Authorization header via the shared connection-pooled client.
        Includes automatic retry for 429 (rate limit) and 5xx (server error).
        
        Args:
            params: Email parameters (from, to, subject, html)
            api_key: Resend API key for this specific request
            
        Returns:
            Response JSON from Resend API
        """
        max_retries = 3
        for attempt in range(max_retries):
            response = await self._http_client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=params,
            )
            
            if response.status_code == 429:
                # Rate limited — respect Retry-After header or default to 60s
                retry_after = int(response.headers.get("Retry-After", 60))
                log.warning(f"Resend 429 rate limit. Esperando {retry_after}s (intento {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_after)
                continue
            
            if response.status_code >= 500 and attempt < max_retries - 1:
                # Server error — short backoff and retry
                wait = 5 * (attempt + 1)
                log.warning(f"Resend {response.status_code} error. Retry en {wait}s (intento {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait)
                continue
            
            response.raise_for_status()
            return response.json()
        
        # If we exhausted retries, raise the last error
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        await self._http_client.aclose()

    async def _send_single(self, lead: Lead, api_key: Optional[str] = None,
                           config: Optional[HunterConfig] = None) -> EmailResult:
        """
        Send a single email to a lead via Resend HTTP API.
        
        Args:
            lead: Lead object with email to send to
            api_key: Optional API key override (for multi-tenant)
            config: Optional user config for template personalization
            
        Returns:
            EmailResult with success status
        """
        if not lead.email:
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error="No email address available"
            )
        
        if not self.is_valid_email(lead.email):
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error=f"Formato de email inválido: {lead.email}"
            )
        
        key = api_key or self._default_api_key
        
        try:
            log.email(f"Enviando email a: {lead.email} ({lead.domain})")
            
            # Determine sender info
            if config:
                from_email = self._normalize_from_email(config.from_email or self.from_email) or self.from_email
                from_name = config.from_name or self.from_name
                subject = config.email_subject or self._get_subject(lead)
            else:
                from_email = self.from_email
                from_name = self.from_name
                subject = self._get_subject(lead)

            # Render template (puede elegir HTML especial por remitente/dominio)
            html_content = self._render_template(
                lead,
                config,
                sender_name=from_name,
                from_email=from_email,
            )
            
            # Prepare email params
            params = {
                "from": f"{from_name} <{from_email}>",
                "to": [lead.email],
                "subject": subject,
                "html": html_content,
            }
            
            # Send via Resend HTTP API with retry for transient failures
            response = await retry_with_backoff(
                self._send_email_http,
                params, key,
                max_retries=2,
                base_delay=2.0,
                exceptions=(httpx.TransportError, httpx.TimeoutException),
                on_retry=lambda e, attempt: log.warning(
                    f"Retry {attempt}/2 enviando a {lead.email}: {str(e)[:80]}"
                ),
            )
            
            # Check for success
            if response and response.get("id"):
                log.success(f"Email enviado exitosamente a {lead.email}")
                return EmailResult(
                    lead_id=lead.id,
                    success=True,
                    resend_id=response["id"]
                )
            else:
                error_msg = "Respuesta inesperada de Resend API"
                log.error(f"Error enviando a {lead.email}: {error_msg}")
                return EmailResult(
                    lead_id=lead.id,
                    success=False,
                    error=error_msg
                )
                
        except Exception as e:
            error_msg = str(e)[:200]
            log.error(f"Error enviando a {lead.email}: {error_msg}")
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error=error_msg
            )

    def _owner_name_from_lead(self, lead: Lead) -> str:
        """
        Derive a friendly owner/recipient name from the lead (e.g. from email).
        Used to personalize the subject line.
        """
        if not lead.email or "@" not in lead.email:
            return ""
        local = lead.email.split("@")[0].strip()
        # Remove numbers and common suffixes, keep letters/dots/hyphens
        parts = "".join(c for c in local if c.isalpha() or c in ".-_ ").split(".") or [local]
        # First part as name: capitalize, replace separators with space
        name = (parts[0] if parts else local).replace("-", " ").replace("_", " ").strip()
        if not name:
            return ""
        return name.title()

    def _get_subject(self, lead: Lead) -> str:
        """
        Generate email subject.
        - Modo "launch": asunto aburrido/humano para no activar filtros (reply-bait).
        - Modo "full": asunto con nombre o el default marketinero.
        """
        # Modo lanzamiento: asunto simple que parezca escrito por un humano
        if self._email_mode == "launch":
            return self._launch_subject

        owner_name = self._owner_name_from_lead(lead)
        custom_subject = os.getenv("EMAIL_SUBJECT")
        if custom_subject:
            subject = custom_subject
            company_name = lead.meta_title or lead.domain.split('.')[0].title()
            subject = subject.replace("{{company_name}}", company_name)
            subject = subject.replace("{{domain}}", lead.domain)
            subject = subject.replace("{{owner_name}}", owner_name)
            return subject
        if owner_name:
            return f"{owner_name}, tu web está perdiendo clientes - Elevá su nivel"
        return self.DEFAULT_SUBJECT

    async def _human_delay(self) -> None:
        """Wait between emails (cooldown). Si min==max==600, logea '10 min'."""
        delay = random.randint(self.min_delay, self.max_delay)
        if delay >= 60:
            log.info(f"Cooldown: esperando {delay // 60} min antes del próximo email...")
        else:
            log.info(f"Esperando {delay}s antes del próximo envío...")
        await asyncio.sleep(delay)

    async def send_batch(self, leads: List[Lead]) -> List[EmailResult]:
        """
        Send emails to a batch of leads with human-like delays.
        
        Args:
            leads: List of Lead objects to email
            
        Returns:
            List of EmailResult objects
        """
        if not leads:
            return []
        
        log.info(f"Iniciando batch de envío: {len(leads)} emails")
        results: List[EmailResult] = []
        
        for i, lead in enumerate(leads):
            # Send email
            result = await self._send_single(lead)
            results.append(result)
            
            # Add human delay between emails (except for the last one)
            if i < len(leads) - 1:
                await self._human_delay()
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        log.info(f"Batch completado: {successful}/{len(leads)} enviados exitosamente")
        
        return results

    async def send_single_with_delay(self, lead: Lead) -> EmailResult:
        """
        Send a single email and wait for human delay.
        
        Useful for processing one email at a time from a queue.
        
        Args:
            lead: Lead object to email
            
        Returns:
            EmailResult with success status
        """
        result = await self._send_single(lead)
        await self._human_delay()
        return result

    async def send_with_config(self, lead: Lead, config: HunterConfig) -> EmailResult:
        """
        Send an email using a specific user's HunterConfig.
        
        Thread-safe: uses per-request API key via HTTP header,
        no global state is mutated.
        
        v8: Solo aplica human delay si el envío fue exitoso.
        Antes esperaba 10-30s incluso si fallaba.
        
        Args:
            lead: Lead object to email
            config: User's HunterConfig with their Resend credentials
            
        Returns:
            EmailResult with success status
        """
        if not config.resend_api_key:
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error="Resend API key not configured"
            )
        
        # Delegate to unified _send_single with per-user API key and config
        result = await self._send_single(lead, api_key=config.resend_api_key, config=config)
        
        # v8: solo delay si el envío fue exitoso (no desperdiciar tiempo en fallos)
        if result.success:
            await self._human_delay()
        
        return result

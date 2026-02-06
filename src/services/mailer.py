"""
Mailer Service - Email sending with Resend.

This module handles sending outreach emails using the Resend API.
Implements human-like delays between sends to avoid spam flags.
"""

import asyncio
import os
import random
from typing import List, Optional

import resend
from dotenv import load_dotenv

from src.domain.models import Lead, EmailResult, HunterConfig
from src.utils.logger import log


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
        
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            raise ValueError("RESEND_API_KEY must be set in environment variables")
        
        resend.api_key = api_key
        
        self.from_email = os.getenv("FROM_EMAIL", "manuel@botlode.com")
        self.from_name = os.getenv("FROM_NAME", "Manuel de Botlode")
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # Load custom template or use default
        self._template = self._load_template()

    def _load_template(self) -> str:
        """
        Load the email HTML template.
        
        Returns:
            HTML template string with placeholders
        """
        # Check for custom template file
        template_path = os.getenv("EMAIL_TEMPLATE_PATH")
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Default template
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.7;
            color: #1a1a1a;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background: #0a0a0a;
        }
        .container {
            background: #ffffff;
            margin: 20px;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(255, 193, 7, 0.15);
        }
        .header {
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 50%, #F57C00 100%);
            color: #000;
            padding: 40px 30px;
            text-align: center;
            position: relative;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 800;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .emoji-bot {
            font-size: 64px;
            margin-bottom: 10px;
            animation: float 3s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        .content {
            padding: 40px 35px;
            background: #ffffff;
        }
        .hook {
            font-size: 20px;
            font-weight: 700;
            color: #F57C00;
            margin-bottom: 20px;
            line-height: 1.4;
        }
        .highlight-box {
            background: linear-gradient(135deg, #FFF9C4 0%, #FFE082 100%);
            border-left: 4px solid #FFC107;
            padding: 20px;
            margin: 25px 0;
            border-radius: 8px;
        }
        .highlight-box p {
            margin: 0;
            font-size: 16px;
            color: #1a1a1a;
        }
        .benefits {
            margin: 25px 0;
        }
        .benefit-item {
            display: flex;
            align-items: flex-start;
            margin: 15px 0;
            padding: 12px;
            background: #FFFDE7;
            border-radius: 8px;
            transition: transform 0.2s;
        }
        .benefit-item:hover {
            transform: translateX(5px);
        }
        .benefit-icon {
            font-size: 24px;
            margin-right: 12px;
            min-width: 30px;
        }
        .benefit-text {
            font-size: 15px;
            line-height: 1.5;
            color: #333;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #FFC107 0%, #FF9800 100%);
            color: #000 !important;
            padding: 18px 40px;
            text-decoration: none !important;
            border-radius: 50px;
            margin: 25px 0;
            font-weight: 800;
            font-size: 16px;
            box-shadow: 0 8px 20px rgba(255, 193, 7, 0.4);
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .cta-button:hover {
            box-shadow: 0 12px 28px rgba(255, 193, 7, 0.6);
            transform: translateY(-2px);
        }
        .urgency {
            background: #000;
            color: #FFC107;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin: 25px 0;
            font-weight: 700;
            font-size: 14px;
        }
        .free-trial-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-radius: 16px;
            padding: 35px 25px;
            margin: 30px 0;
            text-align: center;
            border: 1px solid rgba(255, 193, 7, 0.2);
        }
        .free-trial-badge {
            display: inline-block;
            background: linear-gradient(135deg, #FFC107, #FF9800);
            color: #000;
            padding: 6px 18px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 15px;
        }
        .free-trial-title {
            color: #ffffff;
            font-size: 26px;
            font-weight: 800;
            margin: 0 0 6px 0;
            line-height: 1.3;
        }
        .free-trial-title span {
            color: #FFC107;
        }
        .free-trial-sub {
            color: #b0b0b0;
            font-size: 15px;
            margin: 0 0 22px 0;
            line-height: 1.5;
        }
        .code-window {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            margin: 0 auto 18px auto;
            max-width: 500px;
            text-align: left;
            overflow: hidden;
        }
        .code-titlebar {
            background: #161b22;
            padding: 10px 14px;
            border-bottom: 1px solid #30363d;
        }
        .code-dot {
            display: inline-block;
            width: 11px;
            height: 11px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .code-filename {
            color: #8b949e;
            font-size: 12px;
            float: right;
            margin-top: 2px;
        }
        .code-body {
            padding: 14px 16px;
            font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
            font-size: 11px;
            color: #c9d1d9;
            line-height: 1.7;
            word-break: break-all;
            white-space: pre-wrap;
        }
        .code-tag {
            color: #ff7b72;
        }
        .code-attr {
            color: #79c0ff;
        }
        .code-val {
            color: #a5d6ff;
        }
        .free-trial-steps {
            margin: 18px 0 0 0;
            padding: 0;
        }
        .step-item {
            display: inline-block;
            color: #e0e0e0;
            font-size: 13px;
            margin: 4px 8px;
        }
        .step-num {
            display: inline-block;
            background: #FFC107;
            color: #000;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            font-size: 12px;
            font-weight: 800;
            line-height: 22px;
            text-align: center;
            margin-right: 5px;
        }
        .free-trial-note {
            color: #6e7681;
            font-size: 12px;
            margin: 18px 0 0 0;
            font-style: italic;
        }
        .cta-invite {
            background: linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%);
            border: 2px solid #FFE082;
            border-radius: 12px;
            padding: 24px 28px;
            margin: 28px 0 20px 0;
            text-align: center;
        }
        .cta-invite-text {
            margin: 0 0 6px 0;
            font-size: 18px;
            font-weight: 700;
            color: #1a1a1a;
        }
        .cta-invite-sub {
            margin: 0;
            font-size: 16px;
            color: #333;
        }
        .signature {
            margin-top: 35px;
            padding-top: 25px;
            border-top: 2px solid #FFE082;
        }
        .signature p {
            margin: 5px 0;
        }
        .footer {
            background: #0a0a0a;
            color: #999;
            text-align: center;
            padding: 25px;
            font-size: 12px;
            line-height: 1.6;
        }
        .footer a {
            color: #FFC107;
            text-decoration: none;
        }
        .ps {
            margin-top: 25px;
            padding: 15px;
            background: #FFF3E0;
            border-radius: 8px;
            font-style: italic;
            font-size: 14px;
            color: #E65100;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji-bot">🤖</div>
            <h1>Tu Competencia Ya Tiene un Empleado que Nunca Duerme</h1>
        </div>
        
        <div class="content">
            <p>Hola, {{company_name}}.</p>
            
            <p>Estuve en tu web {{domain}} y vi que no tenés un asistente virtual como este.</p>
            
            <div class="hook">
                ¿Cuántos clientes perdés mientras dormís? ¿Y los fines de semana?
            </div>
            
            <p>Mientras leés esto, hay empresas como la tuya que ya tienen un <strong>bot con inteligencia artificial</strong> trabajando 24/7, 365 días al año.</p>
            
            <div class="highlight-box">
                <p><strong>🎯 Y lo mejor:</strong> Este bot no solo responde preguntas. Te avisa cuando un visitante muestra interés concreto y te notifica al instante para que cierres la venta cuando importa. Es como tener un vendedor que nunca descansa y sabe exactamente cuándo actuar.</p>
            </div>
            
            <div class="benefits">
                <div class="benefit-item">
                    <div class="benefit-icon">💰</div>
                    <div class="benefit-text"><strong>Se paga solo:</strong> Cada lead que captura vale más que su costo mensual.</div>
                </div>
                
                <div class="benefit-item">
                    <div class="benefit-icon">🎨</div>
                    <div class="benefit-text"><strong>Tiene personalidad:</strong> Cambia de color según el modo (vendedor, técnico, enojado, feliz…).</div>
                </div>
                
                <div class="benefit-item">
                    <div class="benefit-icon">⚡</div>
                    <div class="benefit-text"><strong>Te sirve los clientes en bandeja:</strong> Cuando recopila un contacto, te manda toda la info por mail en tiempo real.</div>
                </div>
                
                <div class="benefit-item">
                    <div class="benefit-icon">🚀</div>
                    <div class="benefit-text"><strong>Tu web gana presencia:</strong> El bot sigue el mouse con la cabeza y capta la atención del visitante desde el primer segundo.</div>
                </div>
                
                <div class="benefit-item">
                    <div class="benefit-icon">📋</div>
                    <div class="benefit-text"><strong>Historial y monitoreo:</strong> Cuenta con historial de todos los chats y monitoreo en tiempo real.</div>
                </div>
            </div>
            
            <div class="highlight-box" style="margin-top: 20px;">
                <p style="font-size: 15px;">Un empleado que trabaja todo el día por vos, sin descanso, respondiendo mensajes y agendando reuniones.</p>
            </div>
            
            <div class="urgency">
                ⏰ TUS COMPETIDORES YA LO ESTÁN USANDO
            </div>
            
            <!-- SECCION PRUEBA GRATIS - EFECTO WOW -->
            <div class="free-trial-section">
                <div class="free-trial-badge">100% GRATIS</div>
                <div style="font-size: 48px; margin-bottom: 8px;">🎁</div>
                <h2 class="free-trial-title">Probalo <span>GRATIS</span> en tu web</h2>
                <p class="free-trial-sub">Copiá este código y pegalo en tu web antes del cierre <code style="background: rgba(255,193,7,0.2); color: #FFC107; padding: 2px 6px; border-radius: 4px; font-size: 13px;">&lt;/body&gt;</code></p>
                
                <div class="code-window">
                    <div class="code-titlebar">
                        <span class="code-dot" style="background: #ff5f56;"></span>
                        <span class="code-dot" style="background: #ffbd2e;"></span>
                        <span class="code-dot" style="background: #27c93f;"></span>
                        <span class="code-filename">tu-web.html</span>
                    </div>
                    <div class="code-body"><span class="code-tag">&lt;iframe</span> <span class="code-attr">src</span>=<span class="code-val">"https://botlode-player.vercel.app?botId=0038971a-da75-4ddc-8663-d52a6b8f2936&amp;v=2.5"</span> <span class="code-attr">style</span>=<span class="code-val">"position:fixed;bottom:16px;right:16px;width:140px;height:140px;border:none;z-index:9999"</span> <span class="code-attr">allow</span>=<span class="code-val">"clipboard-write"</span><span class="code-tag">&gt;&lt;/iframe&gt;</span></div>
                </div>
                
                <div class="free-trial-steps">
                    <span class="step-item"><span class="step-num">1</span> Copiá el código</span>
                    <span class="step-item"><span class="step-num">2</span> Pegalo en tu web</span>
                    <span class="step-item"><span class="step-num">3</span> ¡Listo! Ya tenés tu bot</span>
                </div>
                
                <p class="free-trial-note">Sin registro. Sin tarjeta. Solo 1 línea de código y en 30 segundos está funcionando.</p>
            </div>
            
            <div class="cta-invite">
                <p class="cta-invite-text">¿Querés verlo en acción primero?</p>
                <p class="cta-invite-sub">Mirá cómo funciona en mi página.</p>
            </div>
            
            <center>
                <a href="{{calendar_link}}" class="cta-button" style="color: #000 !important; text-decoration: none;">VER DEMO EN VIVO</a>
            </center>
            
            <div class="signature">
                <p><strong>{{sender_name}}</strong></p>
                <p style="color: #666; font-size: 14px;">Founder @ BotLode</p>
                <p style="color: #999; font-size: 13px;">El bot que vende mientras dormís</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Este email fue enviado a <strong>{{email}}</strong> desde <strong>{{domain}}</strong></p>
            <p>Si no deseas recibir más correos, respondé a este email con la palabra REMOVER.</p>
            <p style="margin-top: 15px; color: #666;">🤖 Powered by BotLode - <a href="https://www.botlode.com">www.botlode.com</a></p>
        </div>
    </div>
</body>
</html>
"""

    def _render_template(self, lead: Lead) -> str:
        """
        Render the email template with lead data.
        
        Args:
            lead: Lead object with data to insert
            
        Returns:
            Rendered HTML string
        """
        # Extract company name: prefer meta_title (often has company name), else domain stem
        raw_domain = lead.domain.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
        company_name = lead.meta_title or raw_domain.split(".")[0].replace("-", " ").title()
        
        # Replace placeholders
        html = self._template
        html = html.replace("{{company_name}}", company_name)
        html = html.replace("{{domain}}", lead.domain)
        html = html.replace("{{email}}", lead.email or "")
        html = html.replace("{{sender_name}}", os.getenv("SENDER_NAME", "El equipo de BotLode"))
        html = html.replace("{{sender_email}}", self.from_email)
        html = html.replace("{{calendar_link}}", os.getenv("CALENDAR_LINK", "https://www.botlode.com"))
        
        return html

    async def _send_single(self, lead: Lead) -> EmailResult:
        """
        Send a single email to a lead.
        
        Args:
            lead: Lead object with email to send to
            
        Returns:
            EmailResult with success status
        """
        if not lead.email:
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error="No email address available"
            )
        
        try:
            log.email(f"Enviando email a: {lead.email} ({lead.domain})")
            
            # Render the template
            html_content = self._render_template(lead)
            
            # Prepare email params
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [lead.email],
                "subject": self._get_subject(lead),
                "html": html_content,
            }
            
            # Send via Resend
            response = resend.Emails.send(params)
            
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
        Generate email subject, optionally personalized.
        Includes owner/recipient name when available (from email).
        """
        owner_name = self._owner_name_from_lead(lead)

        custom_subject = os.getenv("EMAIL_SUBJECT")
        if custom_subject:
            # Replace placeholders in custom subject
            subject = custom_subject
            company_name = lead.meta_title or lead.domain.split('.')[0].title()
            subject = subject.replace("{{company_name}}", company_name)
            subject = subject.replace("{{domain}}", lead.domain)
            subject = subject.replace("{{owner_name}}", owner_name)
            return subject

        # Default subject with recipient name when available
        if owner_name:
            return f"{owner_name}, tu web está perdiendo clientes - Elevá su nivel"
        return self.DEFAULT_SUBJECT

    async def _human_delay(self) -> None:
        """Wait a random human-like delay between emails."""
        delay = random.randint(self.min_delay, self.max_delay)
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
        
        This method temporarily uses the user's Resend API key and
        email settings to send the email.
        
        Args:
            lead: Lead object to email
            config: User's HunterConfig with their Resend credentials
            
        Returns:
            EmailResult with success status
        """
        if not lead.email:
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error="No email address available"
            )
        
        if not config.resend_api_key:
            return EmailResult(
                lead_id=lead.id,
                success=False,
                error="Resend API key not configured"
            )
        
        try:
            log.email(f"Enviando email a: {lead.email} ({lead.domain}) con config de usuario")
            
            # Temporarily set user's API key
            resend.api_key = config.resend_api_key
            
            # Use user's email settings
            from_email = config.from_email or self.from_email
            from_name = config.from_name or self.from_name
            
            # Render the template with user's calendar link
            html_content = self._render_template_with_config(lead, config)
            
            # Get subject (from config or default)
            subject = config.email_subject or self._get_subject(lead)
            
            # Prepare email params
            params = {
                "from": f"{from_name} <{from_email}>",
                "to": [lead.email],
                "subject": subject,
                "html": html_content,
            }
            
            # Send via Resend
            response = resend.Emails.send(params)
            
            # Wait human delay
            await self._human_delay()
            
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

    def _render_template_with_config(self, lead: Lead, config: HunterConfig) -> str:
        """
        Render the email template with lead data and user config.
        
        Args:
            lead: Lead object with data to insert
            config: User's HunterConfig with their settings
            
        Returns:
            Rendered HTML string
        """
        # Extract company name
        raw_domain = lead.domain.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
        company_name = lead.meta_title or raw_domain.split(".")[0].replace("-", " ").title()
        
        # Use user's settings
        sender_name = config.from_name or os.getenv("SENDER_NAME", "El equipo de BotLode")
        calendar_link = config.calendar_link or os.getenv("CALENDAR_LINK", "https://www.botlode.com")
        from_email = config.from_email or self.from_email
        
        # Replace placeholders
        html = self._template
        html = html.replace("{{company_name}}", company_name)
        html = html.replace("{{domain}}", lead.domain)
        html = html.replace("{{email}}", lead.email or "")
        html = html.replace("{{sender_name}}", sender_name)
        html = html.replace("{{sender_email}}", from_email)
        html = html.replace("{{calendar_link}}", calendar_link)
        
        return html

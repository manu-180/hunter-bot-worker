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
        
        # Default template - BotLode branded, iframe matches botlode_web/index.html
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
            max-width: 620px;
            margin: 0 auto;
            padding: 0;
            background: #050505;
        }
        .wrapper {
            background: #050505;
            padding: 20px 12px;
        }
        .container {
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 40px rgba(255, 192, 0, 0.12);
        }

        /* ── HEADER ── */
        .header {
            background: linear-gradient(135deg, #050505 0%, #111 100%);
            padding: 36px 30px 32px;
            text-align: center;
            border-bottom: 3px solid #FFC000;
        }
        .brand-name {
            font-size: 36px;
            font-weight: 900;
            color: #FFC000;
            letter-spacing: -1px;
            margin: 0 0 4px 0;
        }
        .brand-sub {
            font-size: 12px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #888;
            margin: 0;
        }
        .header-title {
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            margin: 20px 0 0 0;
            line-height: 1.35;
        }

        /* ── CONTENT ── */
        .content {
            padding: 36px 32px;
            background: #ffffff;
        }
        .greeting {
            font-size: 16px;
            color: #333;
            margin: 0 0 18px 0;
        }
        .hook {
            font-size: 19px;
            font-weight: 700;
            color: #D48800;
            margin: 24px 0 16px 0;
            line-height: 1.4;
        }
        .body-text {
            font-size: 15px;
            color: #444;
            margin: 0 0 16px 0;
            line-height: 1.7;
        }

        /* ── HIGHLIGHT BOX ── */
        .highlight-box {
            background: #FFFBEB;
            border-left: 4px solid #FFC000;
            padding: 18px 20px;
            margin: 24px 0;
            border-radius: 0 8px 8px 0;
        }
        .highlight-box p {
            margin: 0;
            font-size: 15px;
            color: #1a1a1a;
            line-height: 1.6;
        }

        /* ── BENEFITS ── */
        .benefits {
            margin: 28px 0;
        }
        .benefit-item {
            display: flex;
            align-items: flex-start;
            margin: 0 0 12px 0;
            padding: 14px 16px;
            background: #FAFAFA;
            border-radius: 10px;
            border: 1px solid #F0F0F0;
        }
        .benefit-icon {
            font-size: 22px;
            margin-right: 14px;
            min-width: 28px;
            line-height: 1;
        }
        .benefit-text {
            font-size: 14px;
            line-height: 1.5;
            color: #333;
        }
        .benefit-text strong {
            color: #1a1a1a;
        }

        /* ── URGENCY BANNER ── */
        .urgency {
            background: #050505;
            color: #FFC000;
            padding: 14px 20px;
            border-radius: 10px;
            text-align: center;
            margin: 28px 0;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 0.5px;
        }

        /* ── FREE TRIAL SECTION ── */
        .free-trial-section {
            background: linear-gradient(135deg, #050505 0%, #0D1117 50%, #050505 100%);
            border-radius: 16px;
            padding: 36px 24px;
            margin: 28px 0;
            text-align: center;
            border: 1px solid #222;
        }
        .trial-badge {
            display: inline-block;
            background: rgba(255, 192, 0, 0.15);
            border: 1px solid rgba(255, 192, 0, 0.4);
            color: #FFC000;
            padding: 6px 18px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }
        .trial-emoji {
            font-size: 48px;
            margin: 10px 0 14px 0;
        }
        .trial-title {
            color: #ffffff;
            font-size: 24px;
            font-weight: 800;
            margin: 0 0 10px 0;
            line-height: 1.3;
        }
        .trial-title-gold {
            color: #FFC000;
        }
        .trial-sub {
            color: #999;
            font-size: 14px;
            margin: 0 0 24px 0;
            line-height: 1.5;
        }
        .trial-sub code {
            background: rgba(255, 192, 0, 0.15);
            color: #FFC000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            border: 1px solid rgba(255, 192, 0, 0.3);
        }

        /* ── CODE CARD ── */
        .code-card {
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px auto;
            max-width: 520px;
            text-align: left;
        }
        .code-bar {
            background: #161B22;
            padding: 10px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363D;
        }
        .code-bar-left {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .code-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        .code-dot-green { background: #3FB950; }
        .code-dot-yellow { background: #FFC000; }
        .code-dot-red { background: #F85149; }
        .code-bar-label {
            color: #8B949E;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }
        .code-bar-copy {
            color: #FFC000;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: rgba(255, 192, 0, 0.12);
            padding: 3px 10px;
            border-radius: 4px;
            border: 1px solid rgba(255, 192, 0, 0.25);
        }
        .code-body {
            padding: 14px 16px;
            font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
            font-size: 10.5px;
            color: #C9D1D9;
            line-height: 1.7;
            word-break: break-all;
            overflow-x: auto;
        }
        .code-comment { color: #8B949E; }
        .code-tag { color: #FF7B72; }
        .code-attr { color: #79C0FF; }
        .code-val { color: #A5D6FF; }
        .code-str { color: #FFC000; }
        .code-steps {
            background: #161B22;
            padding: 12px 14px;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            border-top: 1px solid #30363D;
        }
        .code-step {
            color: #8B949E;
            font-size: 11px;
            font-weight: 600;
        }
        .code-step-num {
            color: #FFC000;
            font-weight: 800;
            margin-right: 4px;
        }

        /* ── RESULTS ROW ── */
        .results-row {
            display: flex;
            justify-content: center;
            gap: 28px;
            margin: 24px 0;
            flex-wrap: wrap;
        }
        .result-item {
            text-align: center;
        }
        .result-icon {
            font-size: 26px;
            margin-bottom: 4px;
        }
        .result-text {
            color: #ccc;
            font-size: 11px;
            font-weight: 600;
        }
        .trial-note {
            color: #666;
            font-size: 12px;
            margin: 18px 0 0 0;
            line-height: 1.5;
            padding: 10px 14px;
            background: rgba(255, 192, 0, 0.06);
            border-radius: 6px;
            border: 1px solid #222;
        }

        /* ── CTA SECTION ── */
        .cta-section {
            text-align: center;
            margin: 28px 0 8px 0;
        }
        .cta-question {
            font-size: 18px;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0 0 6px 0;
        }
        .cta-sub {
            font-size: 15px;
            color: #666;
            margin: 0 0 20px 0;
        }
        .cta-button {
            display: inline-block;
            background: #FFC000;
            color: #000 !important;
            padding: 16px 44px;
            text-decoration: none !important;
            border-radius: 50px;
            font-weight: 800;
            font-size: 15px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* ── SIGNATURE ── */
        .signature {
            margin-top: 32px;
            padding-top: 24px;
            border-top: 2px solid #F5F5F5;
        }
        .sig-name {
            font-weight: 700;
            font-size: 15px;
            color: #1a1a1a;
            margin: 0 0 2px 0;
        }
        .sig-role {
            color: #888;
            font-size: 13px;
            margin: 0 0 2px 0;
        }
        .sig-tagline {
            color: #FFC000;
            font-size: 12px;
            font-weight: 600;
            margin: 4px 0 0 0;
        }

        /* ── FOOTER ── */
        .footer {
            background: #050505;
            color: #666;
            text-align: center;
            padding: 24px 20px;
            font-size: 11px;
            line-height: 1.7;
        }
        .footer a {
            color: #FFC000;
            text-decoration: none;
        }
        .footer-brand {
            color: #FFC000;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: -0.5px;
        }
    </style>
</head>
<body>
    <div class="wrapper">
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <p class="brand-name">BotLode</p>
            <p class="brand-sub">Fabrica de Bots IA</p>
            <p class="header-title">Tu competencia ya tiene un empleado<br>que nunca duerme</p>
        </div>
        
        <!-- CONTENT -->
        <div class="content">
            <p class="greeting">Hola, <strong>{{company_name}}</strong>.</p>
            
            <p class="body-text">Estuve en tu web <strong>{{domain}}</strong> y noté que no tenés un asistente virtual con inteligencia artificial.</p>
            
            <p class="hook">¿Cuántos clientes perdés mientras dormís?<br>¿Y los fines de semana?</p>
            
            <p class="body-text">Mientras leés esto, hay empresas de tu rubro que ya tienen un <strong>bot con IA</strong> trabajando 24/7, 365 días al año, cerrando ventas sin descanso.</p>
            
            <div class="highlight-box">
                <p><strong>Lo mejor:</strong> Este bot no solo responde preguntas. Te avisa al instante cuando un visitante muestra interés real para que cierres la venta en el momento justo.</p>
            </div>
            
            <!-- BENEFITS -->
            <div class="benefits">
                <div class="benefit-item">
                    <div class="benefit-icon">💰</div>
                    <div class="benefit-text"><strong>Se paga solo.</strong> Cada lead que captura vale más que su costo mensual.</div>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">🎨</div>
                    <div class="benefit-text"><strong>Tiene personalidad.</strong> Cambia de color según el modo: vendedor, técnico, enojado, feliz.</div>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">⚡</div>
                    <div class="benefit-text"><strong>Te sirve clientes en bandeja.</strong> Captura contactos y te manda la info por mail en tiempo real.</div>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">👀</div>
                    <div class="benefit-text"><strong>Capta la atención.</strong> Sigue el mouse con la cabeza y engancha al visitante desde el segundo 1.</div>
                </div>
                <div class="benefit-item">
                    <div class="benefit-icon">📊</div>
                    <div class="benefit-text"><strong>Historial completo.</strong> Todos los chats guardados con monitoreo en tiempo real.</div>
                </div>
            </div>
            
            <div class="urgency">⏰ TUS COMPETIDORES YA LO ESTÁN USANDO</div>
            
            <!-- FREE TRIAL SECTION -->
            <div class="free-trial-section">
                <div class="trial-badge">⚡ PRUEBA GRATIS ⚡</div>
                
                <div class="trial-emoji">🤖</div>
                
                <h2 class="trial-title">Integralo en tu web en <span class="trial-title-gold">30 segundos</span></h2>
                
                <p class="trial-sub">Copiá este código y pegalo antes del <code>&lt;/body&gt;</code> de tu sitio</p>
                
                <!-- CODE CARD - iframe + script idéntico a botlode_web/index.html -->
                <div class="code-card">
                    <div class="code-bar">
                        <div class="code-bar-left">
                            <span class="code-dot code-dot-red"></span>
                            <span class="code-dot code-dot-yellow"></span>
                            <span class="code-dot code-dot-green"></span>
                            <span class="code-bar-label">botlode-player.html</span>
                        </div>
                        <span class="code-bar-copy">COPIAR</span>
                    </div>
                    
                    <div class="code-body">
                        <span class="code-comment">&lt;!-- BotLode Player --&gt;</span><br>
                        <span class="code-tag">&lt;iframe</span>
                        <span class="code-attr"> id</span>=<span class="code-val">"botlode-player"</span><br>
                        &nbsp;&nbsp;<span class="code-attr">src</span>=<span class="code-str">"https://botlode-player.vercel.app?botId=0038971a-da75-4ddc-8663-d52a6b8f2936"</span><br>
                        &nbsp;&nbsp;<span class="code-attr">style</span>=<span class="code-val">"position:fixed;bottom:16px;right:16px;width:140px;height:140px;border:none;z-index:9999;pointer-events:auto;background:transparent;"</span><br>
                        &nbsp;&nbsp;<span class="code-attr">allow</span>=<span class="code-val">"clipboard-write"</span>
                        <span class="code-attr"> loading</span>=<span class="code-val">"lazy"</span><span class="code-tag">&gt;&lt;/iframe&gt;</span><br>
                        <br>
                        <span class="code-comment">&lt;!-- Auto-resize del chat --&gt;</span><br>
                        <span class="code-tag">&lt;script&gt;</span><br>
                        <span class="code-val">!function(){var e=document.getElementById</span><br>
                        <span class="code-val">("botlode-player");e&amp;&amp;window.addEventListener</span><br>
                        <span class="code-val">("message",function(t){"CMD_OPEN"===t.data?</span><br>
                        <span class="code-val">(e.style.width="450px",e.style.height=</span><br>
                        <span class="code-val">"calc(100vh - 32px)"):"CMD_CLOSE"===t.data?</span><br>
                        <span class="code-val">(e.style.width="140px",e.style.height="140px"</span><br>
                        <span class="code-val">):"CMD_HOVER_START"===t.data?(e.style.width=</span><br>
                        <span class="code-val">"350px",e.style.height="140px"):"CMD_HOVER_END"</span><br>
                        <span class="code-val">===t.data&amp;&amp;(e.style.width="140px",</span><br>
                        <span class="code-val">e.style.height="140px")})}();</span><br>
                        <span class="code-tag">&lt;/script&gt;</span>
                    </div>
                    
                    <div class="code-steps">
                        <span class="code-step"><span class="code-step-num">1.</span> Seleccioná todo</span>
                        <span class="code-step"><span class="code-step-num">2.</span> Copiá (Ctrl+C)</span>
                        <span class="code-step"><span class="code-step-num">3.</span> Pegá en tu HTML</span>
                    </div>
                </div>
                
                <div class="results-row">
                    <div class="result-item">
                        <div class="result-icon">⚡</div>
                        <div class="result-text">Activo al instante</div>
                    </div>
                    <div class="result-item">
                        <div class="result-icon">🎨</div>
                        <div class="result-text">Diseño pro incluido</div>
                    </div>
                    <div class="result-item">
                        <div class="result-icon">🔒</div>
                        <div class="result-text">Sin registro</div>
                    </div>
                </div>
                
                <p class="trial-note">El bot se integra automáticamente y comienza a interactuar con tus visitantes.</p>
            </div>
            
            <!-- CTA -->
            <div class="cta-section">
                <p class="cta-question">¿Querés verlo en acción primero?</p>
                <p class="cta-sub">Mirá cómo funciona en mi página.</p>
                <a href="{{calendar_link}}" class="cta-button" style="color: #000 !important; text-decoration: none;">VER DEMO EN VIVO</a>
            </div>
            
            <!-- SIGNATURE -->
            <div class="signature">
                <p class="sig-name">{{sender_name}}</p>
                <p class="sig-role">Founder @ BotLode</p>
                <p class="sig-tagline">El bot que vende mientras dormís 🤖</p>
            </div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            <p class="footer-brand">BotLode</p>
            <p style="margin: 8px 0;">Email enviado a <strong>{{email}}</strong> desde <strong>{{domain}}</strong></p>
            <p>Si no querés recibir más correos, respondé con la palabra <strong>REMOVER</strong>.</p>
            <p style="margin-top: 12px;"><a href="https://www.botlode.com">www.botlode.com</a></p>
        </div>
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

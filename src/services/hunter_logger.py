"""
Hunter Logger Service - Logs para tiempo real en la UI.

Este módulo maneja la inserción de logs en la tabla hunter_logs
para que la UI de Botslode los muestre en tiempo real.
"""

import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from supabase import create_client, Client
from dotenv import load_dotenv


class LogLevel(str, Enum):
    """Niveles de log."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class LogAction(str, Enum):
    """Tipos de acciones que generan logs."""
    SCRAPE_START = "scrape_start"
    SCRAPE_END = "scrape_end"
    EMAIL_FOUND = "email_found"
    EMAIL_NOT_FOUND = "email_not_found"
    SEND_START = "send_start"
    SEND_SUCCESS = "send_success"
    SEND_FAILED = "send_failed"
    CONFIG_MISSING = "config_missing"
    DOMAIN_ADDED = "domain_added"
    SYSTEM_INFO = "system_info"


def _friendly_error(error: str) -> str:
    """
    Convierte errores técnicos en mensajes amigables para el usuario.
    """
    error_lower = error.lower() if error else ""
    
    # Errores de red/DNS
    if "err_name_not_resolved" in error_lower:
        return "El sitio web no existe o no está disponible"
    if "err_connection_refused" in error_lower:
        return "El servidor rechazó la conexión"
    if "err_connection_timed_out" in error_lower:
        return "Tiempo de espera agotado al conectar"
    if "err_cert" in error_lower or "ssl" in error_lower:
        return "Error de certificado SSL (sitio no seguro)"
    if "err_too_many_redirects" in error_lower:
        return "Demasiadas redirecciones"
    if "err_empty_response" in error_lower:
        return "El servidor no respondió"
    
    # Timeouts
    if "timeout" in error_lower:
        # Extraer el dominio si está en el mensaje
        return "Timeout: el sitio tardó demasiado en cargar"
    
    # Errores HTTP
    if "403" in error_lower:
        return "Acceso bloqueado por el sitio (403)"
    if "404" in error_lower:
        return "Página no encontrada (404)"
    if "500" in error_lower or "502" in error_lower or "503" in error_lower:
        return "Error del servidor (sitio caído)"
    
    # Resend errors
    if "resend" in error_lower:
        if "api key" in error_lower or "unauthorized" in error_lower:
            return "API Key de Resend inválida"
        if "domain" in error_lower and "verified" in error_lower:
            return "Dominio no verificado en Resend"
        if "rate limit" in error_lower:
            return "Límite de envíos alcanzado, esperando..."
    
    # Si es muy largo, acortar
    if len(error) > 80:
        # Intentar extraer solo la parte útil
        if "Page.goto:" in error:
            error = error.split("Page.goto:")[-1].strip()
        if "Call log:" in error:
            error = error.split("Call log:")[0].strip()
        error = error[:80] + "..." if len(error) > 80 else error
    
    return error if error else "Error desconocido"


class HunterLoggerService:
    """
    Servicio para insertar logs en hunter_logs.
    
    Los logs se insertan directamente en Supabase para que
    la UI de Botslode los reciba en tiempo real via Realtime.
    """
    
    def __init__(self, supabase_client: Optional[Client] = None) -> None:
        """
        Inicializa el servicio de logging.
        
        Args:
            supabase_client: Cliente de Supabase opcional.
                             Si no se proporciona, se crea uno nuevo.
        """
        if supabase_client:
            self.client = supabase_client
        else:
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
            self.client = create_client(supabase_url, supabase_key)
        
        self.table_name = "hunter_logs"
    
    def log(
        self,
        user_id: str,
        domain: str,
        level: LogLevel,
        action: LogAction,
        message: str,
        lead_id: Optional[str] = None
    ) -> bool:
        """
        Inserta un log en la tabla hunter_logs.
        
        Args:
            user_id: ID del usuario propietario
            domain: Dominio relacionado
            level: Nivel de severidad
            action: Tipo de acción
            message: Mensaje descriptivo
            lead_id: ID del lead (opcional)
            
        Returns:
            True si se insertó correctamente
        """
        try:
            data = {
                "user_id": user_id,
                "domain": domain,
                "level": level.value,
                "action": action.value,
                "message": message,
            }
            
            if lead_id:
                data["lead_id"] = lead_id
            
            self.client.table(self.table_name).insert(data).execute()
            return True
        except Exception as e:
            print(f"Error insertando log: {e}")
            return False
    
    # Métodos de conveniencia para cada tipo de log
    
    def scrape_start(self, user_id: str, domain: str, lead_id: Optional[str] = None) -> bool:
        """Log de inicio de scraping."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.INFO,
            action=LogAction.SCRAPE_START,
            message=f"Iniciando scraping de {domain}...",
            lead_id=lead_id
        )
    
    def scrape_end(self, user_id: str, domain: str, lead_id: Optional[str] = None) -> bool:
        """Log de fin de scraping."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.INFO,
            action=LogAction.SCRAPE_END,
            message=f"Scraping de {domain} completado",
            lead_id=lead_id
        )
    
    def scrape_error(self, user_id: str, domain: str, error: str, lead_id: Optional[str] = None) -> bool:
        """Log de error en scraping con mensaje amigable."""
        friendly_msg = _friendly_error(error)
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.ERROR,
            action=LogAction.SCRAPE_END,
            message=friendly_msg,
            lead_id=lead_id
        )
    
    def email_found(self, user_id: str, domain: str, email: str, lead_id: Optional[str] = None) -> bool:
        """Log de email encontrado."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.SUCCESS,
            action=LogAction.EMAIL_FOUND,
            message=f"Email encontrado: {email}",
            lead_id=lead_id
        )
    
    def email_not_found(self, user_id: str, domain: str, lead_id: Optional[str] = None) -> bool:
        """Log de email no encontrado."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.WARNING,
            action=LogAction.EMAIL_NOT_FOUND,
            message=f"No se encontró email en {domain}",
            lead_id=lead_id
        )
    
    def send_start(self, user_id: str, domain: str, email: str, lead_id: Optional[str] = None) -> bool:
        """Log de inicio de envío de email."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.INFO,
            action=LogAction.SEND_START,
            message=f"Enviando email a {email}...",
            lead_id=lead_id
        )
    
    def send_success(self, user_id: str, domain: str, email: str, lead_id: Optional[str] = None) -> bool:
        """Log de email enviado exitosamente."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.SUCCESS,
            action=LogAction.SEND_SUCCESS,
            message=f"¡Email enviado a {email}!",
            lead_id=lead_id
        )
    
    def send_failed(self, user_id: str, domain: str, email: str, error: str, lead_id: Optional[str] = None) -> bool:
        """Log de error en envío de email con mensaje amigable."""
        friendly_msg = _friendly_error(error)
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.ERROR,
            action=LogAction.SEND_FAILED,
            message=f"Error enviando a {email}: {friendly_msg}",
            lead_id=lead_id
        )
    
    def config_missing(self, user_id: str, domain: str, lead_id: Optional[str] = None) -> bool:
        """Log de configuración faltante."""
        return self.log(
            user_id=user_id,
            domain=domain,
            level=LogLevel.WARNING,
            action=LogAction.CONFIG_MISSING,
            message="Configura Resend en Ajustes para enviar emails",
            lead_id=lead_id
        )
    
    def domains_added(self, user_id: str, count: int) -> bool:
        """Log de dominios agregados."""
        msg = f"{count} dominio agregado a la cola" if count == 1 else f"{count} dominios agregados a la cola"
        return self.log(
            user_id=user_id,
            domain="system",
            level=LogLevel.INFO,
            action=LogAction.DOMAIN_ADDED,
            message=msg
        )
    
    def system_info(self, user_id: str, message: str) -> bool:
        """Log de información del sistema."""
        return self.log(
            user_id=user_id,
            domain="system",
            level=LogLevel.INFO,
            action=LogAction.SYSTEM_INFO,
            message=message
        )

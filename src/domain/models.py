"""
Domain Models - Pydantic definitions para Contact Engine.

Pool compartido de contactos (contacts) + cola por usuario (email_queue).
Los modelos Lead/LeadStatus se mantienen por compatibilidad temporal.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LeadStatus(str, Enum):
    """
    Enumeration of all possible lead states in the pipeline.
    
    Flow: pending -> scraping -> scraped -> queued_for_send -> sending -> sent
    Any state can transition to 'failed' on error.
    """
    PENDING = "pending"
    SCRAPING = "scraping"
    SCRAPED = "scraped"
    QUEUED_FOR_SEND = "queued_for_send"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class LeadBase(BaseModel):
    """Base model with common lead attributes."""
    domain: str = Field(..., description="The target domain to scrape")
    
    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Normalize and validate domain format."""
        # Remove protocol if present
        v = v.lower().strip()
        if v.startswith('http://'):
            v = v[7:]
        elif v.startswith('https://'):
            v = v[8:]
        # Remove trailing slash
        v = v.rstrip('/')
        # Remove www. prefix for consistency
        if v.startswith('www.'):
            v = v[4:]
        return v


class Lead(LeadBase):
    """
    Complete Lead model representing a row in the database.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Owner's user ID (for multi-tenant support)
        domain: Target domain to scrape
        email: Extracted contact email (if found)
        wpp_number: Extracted WhatsApp number (if found), used for WPP follow-up
        meta_title: Page title extracted from the website
        status: Current state in the pipeline
        error_message: Error details if status is 'failed'
        created_at: When the lead was added
        updated_at: Last modification timestamp
        scraped_at: When scraping was completed
        sent_at: When email was sent
    """
    id: UUID
    user_id: Optional[UUID] = None  # For multi-tenant support
    email: Optional[str] = None
    wpp_number: Optional[str] = None  # WhatsApp number for follow-up after email
    meta_title: Optional[str] = None
    status: LeadStatus = LeadStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True  # Enable ORM mode for Supabase results


class HunterConfig(BaseModel):
    """
    Configuration for HunterBot per user.
    
    Stores Resend API credentials, email settings, and bot control.
    """
    id: UUID
    user_id: UUID
    resend_api_key: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = "Mi Empresa"
    from_wpp_number: Optional[str] = None  # WhatsApp de seguimiento (ej. whatsapp:+5491125330794)
    calendar_link: Optional[str] = None
    email_subject: Optional[str] = None
    is_active: bool = False
    # Cooldown entre emails (segundos). NULL = default del worker (300). 600 = 10 min para Metalwailers.
    email_cooldown_seconds: Optional[int] = None

    # Bot control
    bot_enabled: bool = False
    # Si es None (no configurado en DB), populate_email_queue usa todos los contactos del pool.
    # Si tiene valor, filtra contactos por industry. NO usar default "inmobiliarias" para no filtrar sin querer.
    nicho: Optional[str] = None
    ciudades: list[str] = Field(default_factory=lambda: ["Buenos Aires", "Córdoba", "Rosario"])
    pais: str = "Argentina"
    
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_configured(self) -> bool:
        """Check if the config has required fields for sending emails."""
        return bool(self.resend_api_key and self.from_email)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class LeadCreate(LeadBase):
    """
    Model for creating a new lead.
    
    Only requires the domain - other fields are set by the system.
    """
    pass


class LeadUpdate(BaseModel):
    """
    Model for updating an existing lead.
    
    All fields are optional - only provided fields will be updated.
    """
    email: Optional[str] = None
    meta_title: Optional[str] = None
    status: Optional[LeadStatus] = None
    error_message: Optional[str] = None
    scraped_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        # Exclude None values when converting to dict for updates
        exclude_none = True


class ScrapingResult(BaseModel):
    """
    Result of a scraping operation for a single domain.
    
    Attributes:
        lead_id: The UUID of the lead that was scraped
        domain: The domain that was scraped
        success: Whether scraping was successful
        email: Extracted email (if found)
        wpp_number: Extracted WhatsApp number (if found)
        meta_title: Page title (if found)
        error: Error message if scraping failed
    """
    lead_id: UUID
    domain: str
    success: bool
    email: Optional[str] = None
    wpp_number: Optional[str] = None  # WhatsApp number for follow-up
    meta_title: Optional[str] = None
    error: Optional[str] = None


class EmailResult(BaseModel):
    """Result of an email sending operation."""
    lead_id: UUID
    success: bool
    resend_id: Optional[str] = None
    error: Optional[str] = None


# ── Nuevos modelos: pool compartido ──────────────────────────────────────────

class ContactScrapeStatus(str, Enum):
    NEEDS_SCRAPING = "needs_scraping"
    SCRAPING       = "scraping"
    DONE           = "done"       # email encontrado
    NO_EMAIL       = "no_email"   # scrapeado, sin email
    FAILED         = "failed"


class Contact(BaseModel):
    """Empresa en el pool compartido (sin user_id)."""
    id:            UUID
    company_name:  Optional[str] = None
    domain:        Optional[str] = None
    email:         Optional[str] = None
    phone:         Optional[str] = None
    meta_title:    Optional[str] = None
    industry:      Optional[str] = None
    city:          Optional[str] = None
    country:       str = "Argentina"
    scrape_status: ContactScrapeStatus = ContactScrapeStatus.NEEDS_SCRAPING
    scrape_error:  Optional[str] = None
    source:        str = "finder"
    created_at:    datetime
    updated_at:    datetime
    scraped_at:    Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailQueueStatus(str, Enum):
    PENDING  = "pending"
    SENDING  = "sending"
    SENT     = "sent"
    FAILED   = "failed"
    BOUNCED  = "bounced"


class EmailQueueItem(BaseModel):
    """Ítem de la cola de envío de un usuario (uno por empresa por usuario)."""
    id:            UUID
    contact_id:    UUID
    user_id:       UUID
    from_email:    Optional[str] = None
    status:        EmailQueueStatus = EmailQueueStatus.PENDING
    resend_id:     Optional[str] = None
    error_msg:     Optional[str] = None
    attempt_count: int = 0
    queued_at:     datetime
    sent_at:       Optional[datetime] = None
    # Joined from contacts (populated by repo when needed)
    contact:       Optional[Contact] = None

    class Config:
        from_attributes = True


class ContactSegment(BaseModel):
    """Filtro de prioridad: qué empresas del pool le interesan a un usuario."""
    id:         UUID
    user_id:    UUID
    name:       str
    industries: Optional[List[str]] = None
    cities:     Optional[List[str]] = None
    countries:  Optional[List[str]] = None
    has_domain: Optional[bool] = None
    priority:   int = 0
    is_active:  bool = True
    created_at: datetime

    class Config:
        from_attributes = True

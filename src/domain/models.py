"""
Domain Models - Pydantic definitions for LeadSniper.

This module contains all the data models used throughout the application,
providing validation and serialization capabilities.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator


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
    calendar_link: Optional[str] = None
    email_subject: Optional[str] = None
    is_active: bool = False
    
    # Bot control
    bot_enabled: bool = False
    nicho: str = "inmobiliarias"
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
        meta_title: Page title (if found)
        error: Error message if scraping failed
    """
    lead_id: UUID
    domain: str
    success: bool
    email: Optional[str] = None
    meta_title: Optional[str] = None
    error: Optional[str] = None


class EmailResult(BaseModel):
    """
    Result of an email sending operation.
    
    Attributes:
        lead_id: The UUID of the lead
        success: Whether the email was sent successfully
        resend_id: The ID returned by Resend API (if successful)
        error: Error message if sending failed
    """
    lead_id: UUID
    success: bool
    resend_id: Optional[str] = None
    error: Optional[str] = None

"""
Supabase Repository - Database interaction layer.

This module provides an abstraction layer for all Supabase database operations,
implementing the Repository pattern for clean separation of concerns.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from supabase import create_client, Client
from dotenv import load_dotenv

from src.domain.models import Lead, LeadStatus, LeadUpdate, ScrapingResult, HunterConfig


class SupabaseRepository:
    """
    Repository class for handling all Supabase database operations.
    
    This class abstracts the database layer, providing clean methods
    for CRUD operations on the leads table.
    
    Supports multi-tenant mode where each user has their own leads and config.
    """

    def __init__(self) -> None:
        """
        Initialize the Supabase client.
        
        Loads credentials from environment variables.
        
        Raises:
            ValueError: If required environment variables are not set.
        """
        load_dotenv()
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = "leads"
        self.config_table = "hunter_configs"

    def fetch_pending_domains(self, limit: int = 10) -> List[Lead]:
        """
        Fetch domains that are pending scraping.
        
        Args:
            limit: Maximum number of leads to fetch (default: 10)
            
        Returns:
            List of Lead objects with status 'pending'
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.PENDING.value)
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def fetch_queued_emails(self, limit: int = 10) -> List[Lead]:
        """
        Fetch leads that are ready for email sending.
        
        Args:
            limit: Maximum number of leads to fetch (default: 10)
            
        Returns:
            List of Lead objects with status 'queued_for_send'
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.QUEUED_FOR_SEND.value)
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def mark_as_scraping(self, lead_id: UUID) -> bool:
        """
        Mark a lead as currently being scraped (optimistic lock).
        
        Args:
            lead_id: UUID of the lead to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            response = (
                self.client.table(self.table_name)
                .update({"status": LeadStatus.SCRAPING.value})
                .eq("id", str(lead_id))
                .eq("status", LeadStatus.PENDING.value)  # Optimistic lock
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def mark_as_scraped(
        self,
        lead_id: UUID,
        email: Optional[str],
        meta_title: Optional[str]
    ) -> bool:
        """
        Update a lead with scraped data and mark as scraped.
        
        If an email was found, status changes to 'queued_for_send'.
        If no email was found, status changes to 'scraped' (no further action).
        
        Args:
            lead_id: UUID of the lead to update
            email: Extracted email address (or None if not found)
            meta_title: Page title (or None if not found)
            
        Returns:
            True if update was successful, False otherwise
        """
        # If we found an email, queue it for sending; otherwise just mark as scraped
        new_status = (
            LeadStatus.QUEUED_FOR_SEND.value 
            if email 
            else LeadStatus.SCRAPED.value
        )
        
        update_data = {
            "email": email,
            "meta_title": meta_title,
            "status": new_status,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", str(lead_id))
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def mark_as_sending(self, lead_id: UUID) -> bool:
        """
        Mark a lead as currently sending email (optimistic lock).
        
        Args:
            lead_id: UUID of the lead to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            response = (
                self.client.table(self.table_name)
                .update({"status": LeadStatus.SENDING.value})
                .eq("id", str(lead_id))
                .eq("status", LeadStatus.QUEUED_FOR_SEND.value)  # Optimistic lock
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def mark_as_sent(self, lead_id: UUID) -> bool:
        """
        Mark a lead as successfully sent.
        
        Args:
            lead_id: UUID of the lead to update
            
        Returns:
            True if update was successful, False otherwise
        """
        update_data = {
            "status": LeadStatus.SENT.value,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", str(lead_id))
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def mark_as_failed(self, lead_id: UUID, error_message: str) -> bool:
        """
        Mark a lead as failed and log the error.
        
        Args:
            lead_id: UUID of the lead to update
            error_message: Description of what went wrong
            
        Returns:
            True if update was successful, False otherwise
        """
        update_data = {
            "status": LeadStatus.FAILED.value,
            "error_message": error_message[:500],  # Truncate long errors
        }
        
        try:
            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", str(lead_id))
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def update_lead(self, lead_id: UUID, data: LeadUpdate) -> bool:
        """
        Generic update method for a lead.
        
        Args:
            lead_id: UUID of the lead to update
            data: LeadUpdate object with fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        # Convert to dict, excluding None values
        update_dict = data.model_dump(exclude_none=True)
        
        # Convert enum to string if present
        if "status" in update_dict and isinstance(update_dict["status"], LeadStatus):
            update_dict["status"] = update_dict["status"].value
        
        if not update_dict:
            return True  # Nothing to update
        
        try:
            response = (
                self.client.table(self.table_name)
                .update(update_dict)
                .eq("id", str(lead_id))
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    def get_lead_by_id(self, lead_id: UUID) -> Optional[Lead]:
        """
        Fetch a single lead by its ID.
        
        Args:
            lead_id: UUID of the lead to fetch
            
        Returns:
            Lead object if found, None otherwise
        """
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", str(lead_id))
                .single()
                .execute()
            )
            return Lead(**response.data) if response.data else None
        except Exception:
            return None

    def insert_lead(self, domain: str) -> Optional[Lead]:
        """
        Insert a new lead with the given domain.
        
        Args:
            domain: The domain to add
            
        Returns:
            The created Lead object, or None if insert failed
        """
        try:
            response = (
                self.client.table(self.table_name)
                .insert({"domain": domain})
                .execute()
            )
            return Lead(**response.data[0]) if response.data else None
        except Exception:
            return None

    def get_stats(self, user_id: Optional[str] = None) -> dict:
        """
        Get statistics about leads in each status.
        
        Args:
            user_id: Optional user ID for multi-tenant filtering
        
        Returns:
            Dictionary with counts for each status
        """
        stats = {}
        for status in LeadStatus:
            query = (
                self.client.table(self.table_name)
                .select("id", count="exact")
                .eq("status", status.value)
            )
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.execute()
            stats[status.value] = response.count or 0
        return stats

    # =========================================================================
    # Multi-tenant / Hunter Config methods
    # =========================================================================

    def get_user_config(self, user_id: str) -> Optional[HunterConfig]:
        """
        Get the HunterBot configuration for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            HunterConfig object if found, None otherwise
        """
        try:
            response = (
                self.client.table(self.config_table)
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return HunterConfig(**response.data) if response.data else None
        except Exception:
            return None

    def get_lead_with_user(self, lead_id: UUID) -> Optional[Lead]:
        """
        Fetch a lead including its user_id for multi-tenant processing.
        
        Args:
            lead_id: UUID of the lead
            
        Returns:
            Lead object with user_id populated
        """
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", str(lead_id))
                .single()
                .execute()
            )
            return Lead(**response.data) if response.data else None
        except Exception:
            return None

    def fetch_pending_domains_all_users(self, limit: int = 10) -> List[Lead]:
        """
        Fetch pending domains from ALL users (for global worker).
        
        This method processes leads from all users, returning leads
        with their user_id so we can fetch their specific config.
        
        Args:
            limit: Maximum number of leads to fetch
            
        Returns:
            List of Lead objects with user_id populated
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.PENDING.value)
            .not_.is_("user_id", "null")  # Only process leads with user_id
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def fetch_queued_emails_all_users(self, limit: int = 10) -> List[Lead]:
        """
        Fetch queued emails from ALL users (for global worker).
        
        Args:
            limit: Maximum number of leads to fetch
            
        Returns:
            List of Lead objects with user_id populated
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.QUEUED_FOR_SEND.value)
            .not_.is_("user_id", "null")  # Only process leads with user_id
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def get_all_active_configs(self) -> List[HunterConfig]:
        """
        Get all active HunterBot configurations.
        
        Returns:
            List of active HunterConfig objects
        """
        try:
            response = (
                self.client.table(self.config_table)
                .select("*")
                .eq("is_active", True)
                .execute()
            )
            return [HunterConfig(**row) for row in response.data]
        except Exception:
            return []

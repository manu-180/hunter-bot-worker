"""
Supabase Repository - Database interaction layer.

This module provides an abstraction layer for all Supabase database operations,
implementing the Repository pattern for clean separation of concerns.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from supabase import create_client, Client
from dotenv import load_dotenv

from src.domain.models import (
    Lead, LeadStatus, LeadUpdate, ScrapingResult, HunterConfig,
    Contact, ContactScrapeStatus, EmailQueueItem, EmailQueueStatus, ContactSegment,
)
from src.utils.logger import log

# Maximum time a lead can stay in a transient state before being considered stuck
STUCK_LEAD_TIMEOUT_MINUTES = 15


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
        except Exception as e:
            log.error(f"Error en mark_as_scraping({lead_id}): {e}")
            return False

    def mark_as_scraped(
        self,
        lead_id: UUID,
        email: Optional[str],
        meta_title: Optional[str],
        wpp_number: Optional[str] = None,
    ) -> bool:
        """
        Update a lead with scraped data and mark as scraped.
        
        If an email was found, status changes to 'queued_for_send'.
        If no email was found, status changes to 'scraped' (no further action).
        
        Args:
            lead_id: UUID of the lead to update
            email: Extracted email address (or None if not found)
            meta_title: Page title (or None if not found)
            wpp_number: Extracted WhatsApp number (or None if not found)
            
        Returns:
            True if update was successful, False otherwise
        """
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
        if wpp_number:
            update_data["wpp_number"] = wpp_number

        try:
            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", str(lead_id))
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            log.error(f"Error en mark_as_scraped({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en mark_as_sending({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en mark_as_sent({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en mark_as_failed({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en update_lead({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en get_lead_by_id({lead_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en insert_lead({domain}): {e}")
            return None

    def get_stats(self, user_id: Optional[str] = None) -> dict:
        """
        Get statistics about leads in the most important statuses.
        
        Only queries pending and queued_for_send (the actionable ones)
        to minimize database load.
        
        Args:
            user_id: Optional user ID for multi-tenant filtering
        
        Returns:
            Dictionary with counts for each status
        """
        try:
            stats = {status.value: 0 for status in LeadStatus}
            
            for status in [LeadStatus.PENDING, LeadStatus.QUEUED_FOR_SEND]:
                q = (
                    self.client.table(self.table_name)
                    .select("id", count="exact")
                    .eq("status", status.value)
                )
                if user_id:
                    q = q.eq("user_id", user_id)
                response = q.execute()
                stats[status.value] = response.count or 0
            
            return stats
        except Exception as e:
            log.error(f"Error en get_stats: {e}")
            return {status.value: 0 for status in LeadStatus}

    def get_sent_count(self, user_id: Optional[str] = None, warmup_only: bool = False) -> int:
        """
        Total de emails ya enviados (status='sent').
        
        Se usa para el límite de warm-up: una vez alcanzado MAX_TOTAL_EMAILS_SENT
        en leads de warm-up, el bot deja de enviar más emails de warm-up (el resto
        de dominios no se ve afectado).
        
        Args:
            user_id: Si se pasa, cuenta solo los de ese usuario; si None, cuenta global.
            warmup_only: Si True, solo cuenta leads con domain LIKE 'warmup-%'.
        
        Returns:
            Número de leads con status 'sent'
        """
        try:
            q = (
                self.client.table(self.table_name)
                .select("id", count="exact")
                .eq("status", LeadStatus.SENT.value)
            )
            if user_id:
                q = q.eq("user_id", user_id)
            if warmup_only:
                q = q.like("domain", "warmup-%")
            response = q.execute()
            return response.count or 0
        except Exception as e:
            log.error(f"Error en get_sent_count: {e}")
            return 0

    def requeue_old_warmup_leads(self, hours: int = 24) -> int:
        """
        Vuelve a encolar los leads warm-up (dominio warmup-*.getbotlode.com) que
        fueron enviados hace más de `hours` horas. Así se les reenvía cada día
        sin correr el SQL a mano.
        
        Returns:
            Número de leads reencolados
        """
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            response = (
                self.client.table(self.table_name)
                .update({
                    "status": LeadStatus.QUEUED_FOR_SEND.value,
                    "sent_at": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": None,
                })
                .eq("status", LeadStatus.SENT.value)
                .like("domain", "warmup-%")
                .lt("sent_at", cutoff)
                .execute()
            )
            count = len(response.data) if response.data else 0
            if count > 0:
                log.info(f"🔄 Reencolados {count} leads warm-up (enviados hace +{hours}h)")
            return count
        except Exception as e:
            log.error(f"Error en requeue_old_warmup_leads: {e}")
            return 0

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
        except Exception as e:
            log.error(f"Error en get_user_config({user_id}): {e}")
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
        except Exception as e:
            log.error(f"Error en get_lead_with_user({lead_id}): {e}")
            return None

    def fetch_pending_domains_all_users(self, limit: int = 10) -> List[Lead]:
        """
        Fetch pending domains from ALL users (for global worker).
        
        This method processes leads from all users, returning leads
        with their user_id so we can fetch their specific config.
        Ordered by created_at ASC for FIFO processing.
        
        Args:
            limit: Maximum number of leads to fetch
            
        Returns:
            List of Lead objects with user_id populated
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.PENDING.value)
            .not_.is_("user_id", "null")
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def fetch_queued_emails_all_users(self, limit: int = 10) -> List[Lead]:
        """
        Fetch queued emails from ALL users (for global worker).
        Ordered by scraped_at ASC for FIFO processing.
        
        Args:
            limit: Maximum number of leads to fetch
            
        Returns:
            List of Lead objects with user_id populated
        """
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", LeadStatus.QUEUED_FOR_SEND.value)
            .not_.is_("user_id", "null")
            .order("scraped_at", desc=False)
            .limit(limit)
            .execute()
        )
        
        return [Lead(**row) for row in response.data]

    def recover_stuck_leads(self) -> int:
        """
        Recover leads stuck in transient states (scraping, sending).
        
        If a worker crashes mid-operation, leads can get stuck in
        'scraping' or 'sending' state indefinitely. This method
        resets them back to their previous actionable state if they've
        been stuck longer than STUCK_LEAD_TIMEOUT_MINUTES.
        
        Returns:
            Number of leads recovered
        """
        recovered = 0
        cutoff = (
            datetime.now(timezone.utc) - timedelta(minutes=STUCK_LEAD_TIMEOUT_MINUTES)
        ).isoformat()
        
        for stuck_status, recovery_status in [
            (LeadStatus.SCRAPING, LeadStatus.PENDING),
            (LeadStatus.SENDING, LeadStatus.QUEUED_FOR_SEND),
        ]:
            try:
                response = (
                    self.client.table(self.table_name)
                    .update({"status": recovery_status.value})
                    .eq("status", stuck_status.value)
                    .lt("updated_at", cutoff)
                    .execute()
                )
                count = len(response.data)
                if count > 0:
                    log.warning(
                        f"Recuperados {count} leads stuck en '{stuck_status.value}' "
                        f"→ '{recovery_status.value}'"
                    )
                    recovered += count
            except Exception as e:
                log.error(f"Error recuperando leads stuck ({stuck_status.value}): {e}")
        
        return recovered

    def get_all_active_configs(self) -> List[HunterConfig]:
        """
        Get all Hunter configs with contact engine ON (is_active + bot_enabled).
        Solo estos usuarios reciben envío desde email_queue.
        """
        try:
            response = (
                self.client.table(self.config_table)
                .select("*")
                .eq("is_active", True)
                .eq("bot_enabled", True)
                .execute()
            )
            return [HunterConfig(**row) for row in response.data]
        except Exception as e:
            log.error(f"Error en get_all_active_configs: {e}")
            return []

    # =========================================================================
    # Contacts: pool compartido (Opción A)
    # =========================================================================

    def fetch_contacts_to_scrape(self, limit: int = 10) -> List[Contact]:
        """Contactos con dominio que aún no tienen email (needs_scraping)."""
        try:
            r = (
                self.client.table("contacts")
                .select("*")
                .eq("scrape_status", ContactScrapeStatus.NEEDS_SCRAPING.value)
                .not_.is_("domain", "null")
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            return [Contact(**row) for row in r.data]
        except Exception as e:
            log.error(f"Error en fetch_contacts_to_scrape: {e}")
            return []

    def mark_contact_scraping(self, contact_id: UUID) -> bool:
        """Bloqueo optimista: marca el contacto como siendo scrapeado."""
        try:
            r = (
                self.client.table("contacts")
                .update({"scrape_status": ContactScrapeStatus.SCRAPING.value})
                .eq("id", str(contact_id))
                .eq("scrape_status", ContactScrapeStatus.NEEDS_SCRAPING.value)
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_contact_scraping({contact_id}): {e}")
            return False

    def mark_contact_scraped(
        self,
        contact_id: UUID,
        email: Optional[str],
        phone: Optional[str] = None,
        meta_title: Optional[str] = None,
    ) -> bool:
        """Actualiza el contacto con los datos scrapeados."""
        from datetime import timezone
        new_status = (
            ContactScrapeStatus.DONE.value if email
            else ContactScrapeStatus.NO_EMAIL.value
        )
        payload = {
            "email": email,
            "meta_title": meta_title,
            "scrape_status": new_status,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        if phone:
            payload["phone"] = phone
        try:
            r = (
                self.client.table("contacts")
                .update(payload)
                .eq("id", str(contact_id))
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_contact_scraped({contact_id}): {e}")
            return False

    def mark_contact_scrape_failed(self, contact_id: UUID, error: str) -> bool:
        try:
            r = (
                self.client.table("contacts")
                .update({
                    "scrape_status": ContactScrapeStatus.FAILED.value,
                    "scrape_error": error[:500],
                })
                .eq("id", str(contact_id))
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_contact_scrape_failed({contact_id}): {e}")
            return False

    def recover_stuck_contacts(self) -> int:
        """Contactos que quedaron en 'scraping' más de 15 min → vuelven a needs_scraping."""
        try:
            from datetime import timezone
            cutoff = (
                datetime.now(timezone.utc) - timedelta(minutes=STUCK_LEAD_TIMEOUT_MINUTES)
            ).isoformat()
            r = (
                self.client.table("contacts")
                .update({"scrape_status": ContactScrapeStatus.NEEDS_SCRAPING.value})
                .eq("scrape_status", ContactScrapeStatus.SCRAPING.value)
                .lt("updated_at", cutoff)
                .execute()
            )
            return len(r.data)
        except Exception as e:
            log.error(f"Error en recover_stuck_contacts: {e}")
            return 0

    # =========================================================================
    # Email Queue: cola de envío por usuario (Opción A)
    # =========================================================================

    def populate_email_queue(self, user_id: str, config: HunterConfig, limit: int = 200) -> int:
        """
        Encola contactos del pool compartido para este usuario:
        - Con email encontrado (scrape_status = done)
        - Que no hayan sido enviados por este usuario aún
        - Opcionalmente filtrados por nicho/ciudades del usuario (contact_segments o hunter_configs)
        Devuelve la cantidad de nuevos ítems encolados.
        """
        try:
            # Buscar segmentos del usuario (si tiene).
            # Defensive: si la tabla no existe en el proyecto, se ignora y se sigue sin filtro.
            segments = []
            try:
                seg_r = (
                    self.client.table("contact_segments")
                    .select("industries, cities, has_domain")
                    .eq("user_id", user_id)
                    .eq("is_active", True)
                    .order("priority", desc=True)
                    .limit(10)
                    .execute()
                )
                segments = seg_r.data or []
            except Exception:
                segments = []  # tabla no existe o error → sin filtro por segmento

            # Construir query base: contactos con email listo
            q = (
                self.client.table("contacts")
                .select("id")
                .eq("scrape_status", ContactScrapeStatus.DONE.value)
                .not_.is_("email", "null")
                .not_.is_("domain", "null")
            )

            # Filtro por segmentos (industries, cities, has_domain) o por config.nicho
            if segments:
                # Usar el segmento de mayor prioridad para filtrar
                seg = segments[0]
                industries = seg.get("industries")
                cities = seg.get("cities")
                has_domain = seg.get("has_domain")
                if industries:
                    q = q.in_("industry", industries)
                if cities:
                    q = q.in_("city", cities)
                if has_domain is not None:
                    if has_domain:
                        q = q.not_.is_("domain", "null")
                    else:
                        q = q.is_("domain", "null")
            elif config.nicho:
                q = q.eq("industry", config.nicho)

            contacts_r = q.limit(limit * 3).execute()  # buscar más para compensar exclusiones
            all_contact_ids = [row["id"] for row in (contacts_r.data or [])]
            if not all_contact_ids:
                return 0

            # Excluir los que ya están en la queue de este usuario
            existing_r = (
                self.client.table("email_queue")
                .select("contact_id")
                .eq("user_id", user_id)
                .in_("contact_id", all_contact_ids)
                .execute()
            )
            already_queued = {row["contact_id"] for row in (existing_r.data or [])}
            new_ids = [cid for cid in all_contact_ids if cid not in already_queued][:limit]

            if not new_ids:
                return 0

            from datetime import timezone
            now = datetime.now(timezone.utc).isoformat()
            rows = [
                {
                    "contact_id": cid,
                    "user_id": user_id,
                    "from_email": config.from_email,
                    "status": EmailQueueStatus.PENDING.value,
                    "queued_at": now,
                }
                for cid in new_ids
            ]

            # Insertar en lotes pequeños para evitar payloads grandes y detectar
            # errores individuales. Ya pre-filtramos duplicados, así que usamos
            # insert simple en vez de upsert (el upsert requiere que el constraint
            # exista en la BD, lo que puede fallar si la migración no se aplicó).
            inserted = 0
            CHUNK = 20
            for i in range(0, len(rows), CHUNK):
                chunk = rows[i : i + CHUNK]
                try:
                    self.client.table("email_queue").insert(chunk).execute()
                    inserted += len(chunk)
                except Exception as chunk_err:
                    err_str = str(chunk_err)
                    # Puede haber un duplicado por race condition → intentar uno a uno
                    if "duplicate" in err_str.lower() or "unique" in err_str.lower() or "23505" in err_str:
                        for row in chunk:
                            try:
                                self.client.table("email_queue").insert(row).execute()
                                inserted += 1
                            except Exception:
                                pass  # ya estaba en cola, ignorar
                    else:
                        log.error(f"Error insertando chunk email_queue(user={user_id[:8]}): {chunk_err}")
            return inserted
        except Exception as e:
            log.error(f"Error en populate_email_queue(user={user_id}): {e}")
            return 0

    def fetch_email_queue_for_user(self, user_id: str, limit: int = 10) -> List[EmailQueueItem]:
        """Lee emails pendientes de un usuario desde email_queue, con datos del contacto."""
        try:
            r = (
                self.client.table("email_queue")
                .select("*, contacts(*)")
                .eq("user_id", user_id)
                .eq("status", EmailQueueStatus.PENDING.value)
                .order("queued_at", desc=False)
                .limit(limit)
                .execute()
            )
            items = []
            for row in (r.data or []):
                contact_data = row.pop("contacts", None)
                item = EmailQueueItem(**row)
                if contact_data:
                    item = item.model_copy(update={"contact": Contact(**contact_data)})
                items.append(item)
            return items
        except Exception as e:
            log.error(f"Error en fetch_email_queue_for_user(user={user_id}): {e}")
            return []

    def mark_queue_item_sending(self, queue_id: UUID) -> bool:
        try:
            r = (
                self.client.table("email_queue")
                .update({"status": EmailQueueStatus.SENDING.value})
                .eq("id", str(queue_id))
                .eq("status", EmailQueueStatus.PENDING.value)
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_queue_item_sending({queue_id}): {e}")
            return False

    def mark_queue_item_sent(self, queue_id: UUID, resend_id: Optional[str] = None) -> bool:
        from datetime import timezone
        payload = {
            "status": EmailQueueStatus.SENT.value,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        if resend_id:
            payload["resend_id"] = resend_id
        try:
            r = (
                self.client.table("email_queue")
                .update(payload)
                .eq("id", str(queue_id))
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_queue_item_sent({queue_id}): {e}")
            return False

    def mark_queue_item_failed(self, queue_id: UUID, error: str, attempt_count: int = 1) -> bool:
        try:
            r = (
                self.client.table("email_queue")
                .update({
                    "status": EmailQueueStatus.FAILED.value,
                    "error_msg": error[:500],
                    "attempt_count": attempt_count,
                })
                .eq("id", str(queue_id))
                .execute()
            )
            return len(r.data) > 0
        except Exception as e:
            log.error(f"Error en mark_queue_item_failed({queue_id}): {e}")
            return False

    def register_wpp_followup(
        self,
        contact_id: str,
        user_id: str,
        phone: str,
        company_name: str,
        from_number: str,
    ) -> None:
        """
        Inserta el WPP de seguimiento en whatsapp_outbox para que quede visible
        en el Sender Bot como un mensaje enviado por el usuario.
        """
        try:
            from datetime import timezone
            self.client.table("whatsapp_outbox").upsert(
                {
                    "user_id": user_id,
                    "source": "contacts",
                    "source_id": contact_id,
                    "nombre": company_name,
                    "telefono": phone,
                    "from_number": from_number,
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "origin": "wpp_followup_after_email",
                },
                on_conflict="source,source_id,user_id",
                ignore_duplicates=True,
            ).execute()
        except Exception as e:
            log.warning(f"No se pudo registrar WPP follow-up en outbox: {e}")

    def insert_contact(
        self,
        domain: Optional[str],
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        country: str = "Argentina",
        source: str = "finder",
    ) -> Optional[str]:
        """
        Inserta un contacto en el pool compartido. Silencia duplicados (por domain).
        Devuelve el id del contacto insertado o None.
        """
        try:
            row: dict = {
                "scrape_status": (
                    ContactScrapeStatus.NEEDS_SCRAPING.value
                    if domain else ContactScrapeStatus.NO_EMAIL.value
                ),
                "source": source,
                "country": country,
            }
            if domain:
                row["domain"] = domain.strip().lower()
            if phone:
                row["phone"] = phone
            if company_name:
                row["company_name"] = company_name
            if industry:
                row["industry"] = industry
            if city:
                row["city"] = city

            r = self.client.table("contacts").insert(row).execute()
            if r.data and len(r.data) > 0:
                return r.data[0].get("id")
            return None
        except Exception as e:
            if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                log.error(f"Error en insert_contact(domain={domain}): {e}")
            return None

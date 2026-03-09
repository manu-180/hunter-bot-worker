#!/usr/bin/env python3
"""
Envía un email de prueba a un destinatario, SIN respetar horario laboral.

Uso:
    python send_test_email.py manunv97@gmail.com
    python send_test_email.py manunv97@gmail.com metalwailers   # desde contacto@metalwailersinfo.com

Requiere las mismas variables de entorno que el worker (SUPABASE_URL, etc.)
para cargar la config de hunter_configs.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from dotenv import load_dotenv

load_dotenv()

from src.infrastructure.supabase_repo import SupabaseRepository
from src.services.mailer import MailerService
from src.domain.models import Lead, LeadStatus, HunterConfig

# User IDs conocidos
DEFAULT_USER_ID = "38152119-7da4-442e-9826-20901c65f42e"   # Manuel / getbotlode
METALWAILERS_USER_ID = "a18aa369-a8b7-45e4-9f73-cae2df5b0c78"


def resolve_sender_user_id(arg: Optional[str]) -> str:
    if not arg:
        return DEFAULT_USER_ID
    a = arg.strip().lower()
    if a in ("metalwailers", "metalwailersinfo", "metal"):
        return METALWAILERS_USER_ID
    if len(a) == 36 and a.count("-") == 4:
        return a
    return DEFAULT_USER_ID


def create_test_lead(to_email: str, user_id: str) -> Lead:
    """Crea un Lead ficticio para el test."""
    now = datetime.utcnow()
    return Lead(
        id=uuid4(),
        user_id=UUID(user_id),
        domain="test-verificacion-email-manunv.com",
        email=to_email,
        meta_title="Test de envío Hunter Bot",
        status=LeadStatus.QUEUED_FOR_SEND,
        created_at=now,
        updated_at=now,
    )


async def main() -> None:
    to_email = (sys.argv[1] if len(sys.argv) > 1 else "manunv97@gmail.com").strip()
    sender_arg = sys.argv[2].strip() if len(sys.argv) > 2 else None
    if not to_email or "@" not in to_email:
        print("Uso: python send_test_email.py <email_destino> [metalwailers|user_id]")
        print("  Ejemplo: python send_test_email.py manunv97@gmail.com metalwailers")
        sys.exit(1)

    user_id = resolve_sender_user_id(sender_arg)
    print(f"Enviando email de prueba a: {to_email}")
    print("(ignorando horario laboral)")

    repo = SupabaseRepository()
    config = repo.get_user_config(user_id)
    if not config or not config.is_configured:
        print(f"ERROR: No hay config de Resend para user_id={user_id}. Verificá hunter_configs (from_email, resend_api_key).")
        sys.exit(1)

    print(f"Remitente: {config.from_name} <{config.from_email}>")

    mailer = MailerService()
    lead = create_test_lead(to_email, user_id)

    result = await mailer.send_with_config(lead, config)
    await mailer.close()

    if result.success:
        print(f"✅ Email enviado correctamente a {to_email}")
        print(f"   Resend ID: {result.resend_id}")
    else:
        print(f"❌ Error: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

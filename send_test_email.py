#!/usr/bin/env python3
"""
Envía un email de prueba a un destinatario, SIN respetar horario laboral.

Uso:
    python send_test_email.py manunv97@gmail.com

Requiere las mismas variables de entorno que el worker (SUPABASE_URL, etc.)
para cargar la config de hunter_configs.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4, UUID

from dotenv import load_dotenv

load_dotenv()

from src.infrastructure.supabase_repo import SupabaseRepository
from src.services.mailer import MailerService
from src.domain.models import Lead, LeadStatus, HunterConfig

# User ID por defecto (inmobiliarias)
DEFAULT_USER_ID = "38152119-7da4-442e-9826-20901c65f42e"


def create_test_lead(to_email: str) -> Lead:
    """Crea un Lead ficticio para el test."""
    now = datetime.utcnow()
    return Lead(
        id=uuid4(),
        user_id=UUID(DEFAULT_USER_ID),
        domain="test-verificacion-email-manunv.com",
        email=to_email,
        meta_title="Test de envío Hunter Bot",
        status=LeadStatus.QUEUED_FOR_SEND,
        created_at=now,
        updated_at=now,
    )


async def main() -> None:
    to_email = (sys.argv[1] if len(sys.argv) > 1 else "manunv97@gmail.com").strip()
    if not to_email or "@" not in to_email:
        print("Uso: python send_test_email.py <email>")
        sys.exit(1)

    print(f"Enviando email de prueba a: {to_email}")
    print("(ignorando horario laboral)")

    repo = SupabaseRepository()
    config = repo.get_user_config(DEFAULT_USER_ID)
    if not config or not config.is_configured:
        print("ERROR: No hay config de Resend para el usuario. Verificá hunter_configs.")
        sys.exit(1)

    mailer = MailerService()
    lead = create_test_lead(to_email)

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

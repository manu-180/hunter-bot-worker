"""
Verificación estricta de "sin web" — confirma que un negocio realmente NO tiene sitio web.

Lógica: busca el nombre del negocio en Google Web. Si encuentra un dominio propio
(no directorio, no red social, no Google Maps), marca como "has_web".
Si no encuentra nada → "verified_no_web" con alta confianza.

Configurable vía env vars:
    STRICT_NO_WEB_CHECK=1              Activar verificación (default: 1)
    STRICT_NO_WEB_MAX_VERIFICATIONS=10 Máximo de verificaciones por lote
    STRICT_NO_WEB_MIN_CONFIDENCE=70    Confianza mínima para guardar
    STRICT_NO_WEB_TIMEOUT=20           Timeout SerpAPI (segundos)
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

log = logging.getLogger("domain_hunter")

# ─── Config ──────────────────────────────────────────────────────────────────

STRICT_NO_WEB_CHECK = os.getenv("STRICT_NO_WEB_CHECK", "1").strip().lower() in ("1", "true", "yes")
STRICT_NO_WEB_MAX_VERIFICATIONS = int(os.getenv("STRICT_NO_WEB_MAX_VERIFICATIONS", "10"))
STRICT_NO_WEB_MIN_CONFIDENCE = int(os.getenv("STRICT_NO_WEB_MIN_CONFIDENCE", "70"))
STRICT_NO_WEB_TIMEOUT = int(os.getenv("STRICT_NO_WEB_TIMEOUT", "20"))

# ─── Dominios de plataformas (NO son sitio web propio del negocio) ────────────
# Si el negocio aparece SÓLO en estos dominios, se confirma "sin web".
# Si aparece en CUALQUIER OTRO dominio → probablemente tiene web propia.

_PLATFORM_KEYWORDS = frozenset({
    # Redes sociales
    "facebook", "instagram", "twitter", "linkedin", "youtube",
    "tiktok", "pinterest", "whatsapp", "telegram", "snapchat",
    "threads", "reddit",
    # Google
    "google", "goo.gl", "googleapis",
    # Directorios y reviews
    "yelp", "tripadvisor", "foursquare", "paginasamarillas",
    "guialocal", "cylex", "infoisinfo", "tupalo", "hotfrog",
    "brownbook", "tuugo", "findglocal", "yellowpages",
    "whitepages", "superpages", "citysearch", "kompass",
    "europages", "manta", "bbb.org", "chamberofcommerce",
    "alignable", "merchantcircle", "showmelocal",
    # Portales inmobiliarios
    "zonaprop", "argenprop", "properati", "inmuebles24",
    "metrocuadrado", "fincaraiz", "lamudi",
    # Marketplaces
    "mercadolibre", "olx", "ebay", "amazon",
    # Booking / viajes
    "booking", "airbnb", "despegar", "expedia", "trivago",
    "almundo", "decolar",
    # Delivery / transporte
    "pedidosya", "rappi", "uber", "cabify", "didi",
    # Directorios médicos
    "doctoralia", "doctoranytime", "topdoctors", "zocdoc", "practo",
    # Noticias
    "clarin", "lanacion", "infobae", "pagina12", "lavoz",
    "telam", "perfil", "ambito", "cronista",
    # Referencia
    "wikipedia", "wikidata",
    # Empleo
    "zonajobs", "computrabajo", "bumeran", "indeed", "glassdoor",
})

# Dominios gubernamentales / educativos
_GOV_EDU_PATTERNS = (".gob.", ".gov.", ".edu.", ".mil.", ".ac.")


def _extract_domain(url: str) -> Optional[str]:
    """Extrae el dominio de una URL."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = (parsed.hostname or "").lower().strip(".")
        if host.startswith("www."):
            host = host[4:]
        return host if host and "." in host else None
    except Exception:
        return None


def _is_platform_domain(domain: str) -> bool:
    """True si el dominio pertenece a una plataforma conocida (no es web propia)."""
    dl = domain.lower()
    for kw in _PLATFORM_KEYWORDS:
        if kw in dl:
            return True
    for pat in _GOV_EDU_PATTERNS:
        if pat in dl:
            return True
    return False


def _name_matches_domain(name: str, domain: str) -> bool:
    """Heurística: ¿el dominio parece pertenecer a este negocio?
    
    No es necesario que coincida perfectamente — si encontramos un dominio
    que NO es plataforma, ya es fuerte señal de que el negocio tiene web.
    Esta función da un boost de confianza extra si el nombre coincide.
    """
    name_lower = re.sub(r"[^a-záéíóúñü0-9\s]", "", name.lower())
    name_words = [w for w in name_lower.split() if len(w) > 3]
    domain_parts = domain.lower().replace("-", " ").replace(".", " ")
    return any(word in domain_parts for word in name_words)


async def verify_no_website(
    api_key: str,
    name: str,
    city: str,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verifica si un negocio realmente NO tiene sitio web.
    
    Hace una búsqueda Google Web por nombre + ciudad y analiza resultados.
    
    Returns:
        {
            "status": "verified_no_web" | "has_web",
            "confidence": 0-100,
            "found_domain": str | None,
            "details": str
        }
    """
    from serpapi import GoogleSearch

    query = f'"{name}" {city}'
    params = {
        "engine": "google",
        "q": query,
        "hl": "es",
        "num": 10,
        "api_key": api_key,
    }

    try:
        search_obj = GoogleSearch(params)
        results = await asyncio.wait_for(
            asyncio.to_thread(search_obj.get_dict),
            timeout=STRICT_NO_WEB_TIMEOUT,
        )
    except asyncio.TimeoutError:
        return {
            "status": "verified_no_web",
            "confidence": 50,
            "found_domain": None,
            "details": "timeout en búsqueda de verificación",
        }
    except Exception as e:
        return {
            "status": "verified_no_web",
            "confidence": 50,
            "found_domain": None,
            "details": f"error verificación: {str(e)[:80]}",
        }

    # 1) Knowledge Graph — señal más fuerte
    kg = results.get("knowledge_graph", {})
    kg_website = kg.get("website")
    if kg_website:
        domain = _extract_domain(kg_website)
        if domain and not _is_platform_domain(domain):
            return {
                "status": "has_web",
                "confidence": 5,
                "found_domain": domain,
                "details": f"KG website: {domain}",
            }

    # 2) Local results en búsqueda web (a veces Maps devuelve website aquí)
    local_results = results.get("local_results", [])
    if isinstance(local_results, dict):
        local_results = local_results.get("places", [])
    if isinstance(local_results, list):
        for lr in local_results:
            if not isinstance(lr, dict):
                continue
            lr_web = lr.get("website") or lr.get("link")
            if lr_web:
                domain = _extract_domain(lr_web)
                if domain and not _is_platform_domain(domain):
                    title = (lr.get("title") or "").lower()
                    name_lower = name.lower()
                    if any(w in title for w in name_lower.split() if len(w) > 2):
                        return {
                            "status": "has_web",
                            "confidence": 10,
                            "found_domain": domain,
                            "details": f"local_result website: {domain}",
                        }

    # 3) Organic results — buscar dominios propios
    organic = results.get("organic_results", [])
    own_domains: List[str] = []
    for result in organic:
        link = result.get("link", "")
        domain = _extract_domain(link)
        if not domain or _is_platform_domain(domain):
            continue
        own_domains.append(domain)
        title = (result.get("title") or "").lower()
        snippet = (result.get("snippet") or "").lower()
        combined_text = f"{title} {snippet}"
        name_lower = name.lower()
        significant_words = [w for w in name_lower.split() if len(w) > 3]
        if significant_words and any(w in combined_text for w in significant_words):
            return {
                "status": "has_web",
                "confidence": 15,
                "found_domain": domain,
                "details": f"organic match: {domain} — {title[:50]}",
            }

    # 4) Si hay dominios no-plataforma pero sin match de nombre, dar confianza media
    if own_domains:
        return {
            "status": "verified_no_web",
            "confidence": 60,
            "found_domain": None,
            "details": f"dominios encontrados sin match nombre: {', '.join(own_domains[:3])}",
        }

    # 5) Solo plataformas o sin resultados → alta confianza
    confidence = 95 if not organic else 85
    return {
        "status": "verified_no_web",
        "confidence": confidence,
        "found_domain": None,
        "details": f"{len(organic)} resultados, todos plataformas/directorios",
    }


async def batch_verify(
    api_key: str,
    candidates: List[Dict[str, Any]],
    delay_between: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    Verifica un lote de candidatos "sin web".
    
    Cada candidato debe tener: nombre, ciudad, telefono (opcional).
    Respeta STRICT_NO_WEB_MAX_VERIFICATIONS.
    
    Returns: lista de candidatos con campos de verificación agregados:
        verification_status, confidence_no_web, verified_at, verification_details
    """
    if not STRICT_NO_WEB_CHECK:
        now = datetime.now(timezone.utc).isoformat()
        for c in candidates:
            c["verification_status"] = "pending"
            c["confidence_no_web"] = 0
            c["verified_at"] = None
            c["verification_details"] = None
        return candidates

    verified = []
    count = 0
    now = datetime.now(timezone.utc).isoformat()

    for candidate in candidates:
        if count >= STRICT_NO_WEB_MAX_VERIFICATIONS:
            candidate["verification_status"] = "pending"
            candidate["confidence_no_web"] = 0
            candidate["verified_at"] = None
            candidate["verification_details"] = "límite de verificaciones por lote"
            verified.append(candidate)
            continue

        name = candidate.get("nombre", "")
        city = candidate.get("ciudad", "")
        phone = candidate.get("telefono")

        result = await verify_no_website(api_key, name, city, phone)
        count += 1

        candidate["verification_status"] = result["status"]
        candidate["confidence_no_web"] = result["confidence"]
        candidate["verified_at"] = now
        candidate["verification_details"] = result.get("details")

        if result.get("found_domain"):
            details = candidate.get("verification_details", "")
            candidate["verification_details"] = f"{details} | dominio: {result['found_domain']}"

        verified.append(candidate)

        if count < STRICT_NO_WEB_MAX_VERIFICATIONS and count < len(candidates):
            await asyncio.sleep(delay_between)

    return verified

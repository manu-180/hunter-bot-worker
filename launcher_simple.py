"""
Launcher que ejecuta ambos workers en el MISMO proceso usando asyncio.gather.

Esto es mucho más confiable que multiprocessing o shell scripts en containers Docker/Railway:
- No depende de shell scripts (evita problemas de CRLF, permisos, buffering)
- No depende de multiprocessing (evita problemas de stdout en containers)
- Ambos workers comparten el mismo event loop y los logs se ven directamente
"""
import asyncio
import sys
import signal
from datetime import datetime


async def run_all():
    """Ejecuta ambos workers como tareas asyncio concurrentes."""
    print("\n" + "="*70, flush=True)
    print("HUNTERBOT - ASYNC LAUNCHER v3", flush=True)
    print("="*70, flush=True)
    print(f"Timestamp: {datetime.utcnow().isoformat()} UTC", flush=True)
    print("Modo: asyncio.gather (mismo proceso, mismo event loop)", flush=True)
    print("="*70 + "\n", flush=True)

    # Importar módulos
    print("[LAUNCHER] Importando domain_hunter_worker...", flush=True)
    try:
        import domain_hunter_worker
        print("[LAUNCHER] OK - domain_hunter_worker importado", flush=True)
    except Exception as e:
        print(f"[LAUNCHER] ERROR FATAL importando domain_hunter_worker: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("[LAUNCHER] Importando main (LeadSniper)...", flush=True)
    try:
        import main as leadsniper_main
        print("[LAUNCHER] OK - main (LeadSniper) importado", flush=True)
    except Exception as e:
        print(f"[LAUNCHER] ERROR FATAL importando main: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Setup signal handlers para shutdown graceful
    loop = asyncio.get_event_loop()
    if sys.platform != "win32":
        def signal_handler():
            print("\n[LAUNCHER] Señal de terminación recibida. Deteniendo workers...", flush=True)
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    # Ejecutar ambos workers concurrentemente
    print("\n[LAUNCHER] Iniciando ambos workers con asyncio.gather...", flush=True)
    print("[LAUNCHER] 1. DOMAIN-HUNTER: Busca dominios en Google (SerpAPI)", flush=True)
    print("[LAUNCHER] 2. LEADSNIPER: Scrapea emails y envía", flush=True)
    print("[LAUNCHER] " + "="*70 + "\n", flush=True)

    try:
        await asyncio.gather(
            domain_hunter_worker.main(),
            leadsniper_main.main(),
        )
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Interrumpido por el usuario", flush=True)
    except Exception as e:
        print(f"\n[LAUNCHER] Error fatal: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n*** HUNTERBOT LAUNCHER - ENTRY POINT ***\n", flush=True)
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Detenido por el usuario")
    except Exception as e:
        print(f"\n[LAUNCHER] Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

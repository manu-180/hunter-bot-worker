"""
Launcher del Hunter Bot (Opción A).

Ejecuta solo el worker LeadSniper: scraping de contactos (pool compartido)
y envío de emails por usuario desde email_queue. El discovery (SerpAPI)
está en el Finder Bot; este proceso no usa la tabla leads ni SerpAPI.
"""
import asyncio
import sys
import signal
from datetime import datetime, timezone


MAX_RESTARTS = 10  # Máximo de restarts antes de abortar


async def run_with_restart(worker_coro_factory, name: str):
    """Ejecuta un worker con restart automático y backoff exponencial."""
    restarts = 0
    while restarts < MAX_RESTARTS:
        try:
            print(f"[LAUNCHER] {name}: Iniciando (restart #{restarts})...", flush=True)
            await worker_coro_factory()
            print(f"[LAUNCHER] {name}: Terminó normalmente", flush=True)
            break
        except KeyboardInterrupt:
            print(f"\n[LAUNCHER] {name}: Interrumpido por el usuario", flush=True)
            break
        except Exception as e:
            restarts += 1
            backoff = min(5 * (2 ** min(restarts, 5)), 120)
            print(
                f"[LAUNCHER] {name}: CRASH #{restarts}/{MAX_RESTARTS}: {e}",
                flush=True,
            )
            if restarts < MAX_RESTARTS:
                print(
                    f"[LAUNCHER] {name}: Reiniciando en {backoff}s...",
                    flush=True,
                )
                await asyncio.sleep(backoff)
            else:
                print(
                    f"[LAUNCHER] {name}: MÁXIMO DE RESTARTS ALCANZADO. Detenido.",
                    flush=True,
                )


async def run_all():
    """Ejecuta el worker LeadSniper (contacts + email_queue)."""
    print("\n" + "=" * 70, flush=True)
    print("HUNTER BOT - LeadSniper (Opción A: solo scraping + envío)", flush=True)
    print("=" * 70, flush=True)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()} UTC", flush=True)
    print("Discovery: Finder Bot. Este proceso: contacts + email_queue.", flush=True)
    print("=" * 70 + "\n", flush=True)

    print("[LAUNCHER] Importando main (LeadSniper)...", flush=True)
    try:
        import main as leadsniper_main
        print("[LAUNCHER] OK - main (LeadSniper) importado", flush=True)
    except Exception as e:
        print(f"[LAUNCHER] ERROR FATAL importando main: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    loop = asyncio.get_event_loop()
    if sys.platform != "win32":
        def signal_handler():
            print("\n[LAUNCHER] Señal de terminación recibida. Deteniendo...", flush=True)
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    print("[LAUNCHER] Iniciando LeadSniper (scrape contacts + send emails)...", flush=True)
    print(f"[LAUNCHER] Max restarts: {MAX_RESTARTS}", flush=True)
    print("[LAUNCHER] " + "=" * 70 + "\n", flush=True)

    try:
        await run_with_restart(leadsniper_main.main, "LEADSNIPER")
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

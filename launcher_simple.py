"""
Launcher que ejecuta ambos workers en el MISMO proceso usando asyncio.gather.

Optimizado v2:
- Restart automático por worker individual (si uno crashea, no mata al otro)
- Backoff exponencial en restarts
- Logging mejorado con timestamps
"""
import asyncio
import sys
import signal
from datetime import datetime, timezone


MAX_RESTARTS = 10  # Máximo de restarts por worker antes de abortar


async def run_with_restart(worker_coro_factory, name: str):
    """
    Ejecuta un worker con restart automático y backoff exponencial.
    
    Si un worker crashea, se reinicia automáticamente sin afectar al otro.
    
    Args:
        worker_coro_factory: Callable que retorna la coroutine del worker
        name: Nombre del worker para logging
    """
    restarts = 0
    while restarts < MAX_RESTARTS:
        try:
            print(f"[LAUNCHER] {name}: Iniciando (restart #{restarts})...", flush=True)
            await worker_coro_factory()
            # Si termina sin error, salir del loop
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
    """Ejecuta ambos workers como tareas asyncio concurrentes con restart."""
    print("\n" + "=" * 70, flush=True)
    print("HUNTERBOT - ASYNC LAUNCHER v4 (con restart automático)", flush=True)
    print("=" * 70, flush=True)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()} UTC", flush=True)
    print("Modo: asyncio.gather (mismo proceso, restart individual)", flush=True)
    print("=" * 70 + "\n", flush=True)

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

    # Ejecutar ambos workers concurrentemente con restart individual
    print("\n[LAUNCHER] Iniciando ambos workers con restart automático...", flush=True)
    print("[LAUNCHER] 1. DOMAIN-HUNTER: Busca dominios en Google (SerpAPI)", flush=True)
    print("[LAUNCHER] 2. LEADSNIPER: Scrapea emails y envía", flush=True)
    print(f"[LAUNCHER] Max restarts por worker: {MAX_RESTARTS}", flush=True)
    print("[LAUNCHER] " + "=" * 70 + "\n", flush=True)

    try:
        await asyncio.gather(
            run_with_restart(domain_hunter_worker.main, "DOMAIN-HUNTER"),
            run_with_restart(leadsniper_main.main, "LEADSNIPER"),
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

"""
Launcher simple que ejecuta ambos workers en paralelo usando multiprocessing.
Más robusto que subprocess para contenedores Docker.
"""
import multiprocessing
import sys
from datetime import datetime


def run_domain_hunter():
    """Ejecuta el domain hunter worker."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DOMAIN-HUNTER] Iniciando...\n", flush=True)
    try:
        import domain_hunter_worker
        import asyncio
        asyncio.run(domain_hunter_worker.main())
    except Exception as e:
        print(f"\n[DOMAIN-HUNTER] ERROR FATAL: {e}\n", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_leadsniper():
    """Ejecuta el leadsniper worker."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [LEADSNIPER] Iniciando...\n", flush=True)
    try:
        import main
        import asyncio
        asyncio.run(main.main())
    except Exception as e:
        print(f"\n[LEADSNIPER] ERROR FATAL: {e}\n", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("HUNTERBOT - LAUNCHER SIMPLE v2")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Iniciando ambos workers en paralelo usando multiprocessing...")
    print("="*70 + "\n")
    
    # Crear procesos
    p1 = multiprocessing.Process(target=run_domain_hunter, name="DOMAIN-HUNTER")
    p2 = multiprocessing.Process(target=run_leadsniper, name="LEADSNIPER")
    
    # Iniciar ambos
    p1.start()
    p2.start()
    
    print(f"[MANAGER] Domain Hunter PID: {p1.pid}")
    print(f"[MANAGER] LeadSniper PID: {p2.pid}")
    print(f"[MANAGER] Ambos workers iniciados correctamente\n")
    
    try:
        # Esperar a que terminen (nunca deberían terminar en condiciones normales)
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print("\n[MANAGER] Interrupcion recibida. Deteniendo workers...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()
        print("[MANAGER] Workers detenidos correctamente")
        sys.exit(0)

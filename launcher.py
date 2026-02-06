#!/usr/bin/env python3
"""
Launcher - Corre ambos workers en paralelo
"""
import asyncio
import sys

async def run_main():
    """Corre main.py (LeadSniper)"""
    from main import main
    await main()

async def run_hunter():
    """Corre domain_hunter_worker.py"""
    from domain_hunter_worker import main
    await main()

async def launcher():
    """Lanza ambos workers en paralelo"""
    await asyncio.gather(
        run_main(),
        run_hunter()
    )

if __name__ == "__main__":
    try:
        asyncio.run(launcher())
    except KeyboardInterrupt:
        print("\nWorkers detenidos")
        sys.exit(0)

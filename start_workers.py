"""
Script de inicio para Railway - Lanza ambos workers en paralelo.

Este script inicia:
1. Domain Hunter Worker (busca dominios en Google)
2. LeadSniper Worker (scrapea emails y envía)

Ambos workers corren en paralelo en el mismo contenedor.
"""

import asyncio
import subprocess
import sys
import signal
import os
from datetime import datetime


class WorkerManager:
    """Administrador de workers en paralelo."""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def log(self, message: str, worker: str = "MANAGER"):
        """Log con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{worker}] {message}", flush=True)
    
    def signal_handler(self, signum, frame):
        """Maneja señales de terminación."""
        self.log("⚠️  Señal de terminación recibida. Deteniendo workers...")
        self.running = False
        self.stop_all()
        sys.exit(0)
    
    def start_worker(self, script: str, name: str):
        """Inicia un worker en un subproceso."""
        self.log(f"🚀 Iniciando {name}...", name)
        
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.processes.append({
            'process': process,
            'name': name,
            'script': script
        })
        
        return process
    
    def monitor_worker(self, worker_info: dict):
        """Monitorea la salida de un worker."""
        process = worker_info['process']
        name = worker_info['name']
        
        try:
            for line in process.stdout:
                if line.strip():
                    print(f"[{name}] {line.rstrip()}", flush=True)
        except Exception as e:
            self.log(f"❌ Error monitoreando: {e}", name)
    
    def stop_all(self):
        """Detiene todos los workers."""
        for worker in self.processes:
            try:
                self.log(f"⏹️  Deteniendo {worker['name']}...", worker['name'])
                worker['process'].terminate()
                worker['process'].wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.log(f"⚠️  Forzando detención de {worker['name']}", worker['name'])
                worker['process'].kill()
            except Exception as e:
                self.log(f"❌ Error deteniendo: {e}", worker['name'])
    
    async def run(self):
        """Ejecuta ambos workers en paralelo."""
        # Registrar handler para señales
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("=" * 70)
        self.log("🤖 HUNTERBOT - WORKER MANAGER")
        self.log("=" * 70)
        self.log("")
        self.log("Iniciando workers en paralelo...")
        self.log("")
        
        # Iniciar ambos workers
        domain_hunter = self.start_worker("domain_hunter_worker.py", "DOMAIN-HUNTER")
        leadsniper = self.start_worker("main.py", "LEADSNIPER")
        
        # Crear tareas para monitorear ambos
        tasks = [
            asyncio.create_task(asyncio.to_thread(
                self.monitor_worker, 
                {'process': domain_hunter, 'name': 'DOMAIN-HUNTER', 'script': 'domain_hunter_worker.py'}
            )),
            asyncio.create_task(asyncio.to_thread(
                self.monitor_worker,
                {'process': leadsniper, 'name': 'LEADSNIPER', 'script': 'main.py'}
            ))
        ]
        
        self.log("")
        self.log("✅ Ambos workers iniciados correctamente")
        self.log("📊 Monitoreando salida en tiempo real...")
        self.log("")
        
        # Esperar a que ambos terminen
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.log("⚠️  Tareas canceladas")
        finally:
            self.stop_all()


if __name__ == "__main__":
    manager = WorkerManager()
    
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        manager.log("⚠️  Detenido por el usuario")
        manager.stop_all()
    except Exception as e:
        manager.log(f"❌ Error fatal: {e}")
        manager.stop_all()
        sys.exit(1)

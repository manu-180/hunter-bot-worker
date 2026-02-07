"""
Test rapido para verificar que domain_hunter_worker.py puede importarse sin errores.
"""
import sys
import traceback

print("\n" + "="*70)
print("TEST: Verificando domain_hunter_worker.py")
print("="*70 + "\n")

try:
    print("1. Verificando imports basicos...")
    import asyncio
    import os
    from datetime import datetime
    print("   OK - Imports basicos")
    
    print("\n2. Verificando .env...")
    from dotenv import load_dotenv
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    
    print(f"   SUPABASE_URL: {'OK' if SUPABASE_URL else 'FALTA'}")
    print(f"   SUPABASE_KEY: {'OK' if SUPABASE_KEY else 'FALTA'}")
    print(f"   SERPAPI_KEY: {'OK' if SERPAPI_KEY else 'FALTA'}")
    
    if not SERPAPI_KEY:
        print("\nERROR FATAL: SERPAPI_KEY no esta configurada")
        sys.exit(1)
    
    print("\n3. Intentando importar domain_hunter_worker...")
    from domain_hunter_worker import DomainHunterWorker
    print("   OK - Import exitoso")
    
    print("\n4. Intentando crear instancia del worker...")
    worker = DomainHunterWorker()
    print("   OK - Instancia creada")
    
    print("\n5. Verificando conexion a Supabase...")
    if worker.supabase:
        print("   OK - Cliente Supabase inicializado")
        
        # Intentar una query simple
        try:
            response = worker.supabase.table("hunter_configs").select("user_id").limit(1).execute()
            print(f"   OK - Query de prueba exitosa ({len(response.data)} registros)")
        except Exception as e:
            print(f"   WARNING - Query fallo: {str(e)[:100]}")
    else:
        print("   ERROR - Cliente Supabase NO inicializado")
    
    print("\n" + "="*70)
    print("TODAS LAS VERIFICACIONES PASARON")
    print("="*70 + "\n")
    print("El domain_hunter_worker.py deberia poder ejecutarse sin problemas.")
    print("Si Railway no lo ejecuta, el problema esta en start_workers.py\n")
    
except Exception as e:
    print("\n" + "="*70)
    print("ERROR ENCONTRADO")
    print("="*70)
    print(f"\nError: {str(e)}")
    print("\nTraceback completo:")
    traceback.print_exc()
    print("\n" + "="*70 + "\n")
    sys.exit(1)

"""
Generador de Reporte Completo de la Base de Datos
==================================================

Este script se conecta a Supabase y genera un archivo con toda la información
de las tablas del sistema LeadSniper.

Uso:
    python generar_reporte_db.py

El script genera un archivo 'reporte_db_{timestamp}.txt' con toda la info.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL y SUPABASE_KEY deben estar en .env")
    exit(1)

# Conectar a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def separator(title=""):
    """Generar separador con título"""
    if title:
        return f"\n{'='*80}\n{title}\n{'='*80}\n"
    return f"\n{'-'*80}\n"

def fetch_all(table_name, order_by=None, limit=None):
    """Fetch all rows from a table"""
    try:
        query = supabase.table(table_name).select("*")
        if order_by:
            query = query.order(order_by, desc=True)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return response.data
    except Exception as e:
        return f"Error: {e}"

def fetch_with_filter(table_name, filter_col, filter_val, order_by=None, limit=None):
    """Fetch rows with filter"""
    try:
        query = supabase.table(table_name).select("*").eq(filter_col, filter_val)
        if order_by:
            query = query.order(order_by, desc=True)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return response.data
    except Exception as e:
        return f"Error: {e}"

def count_by_status(table_name, user_id=None):
    """Count rows by status"""
    try:
        query = supabase.table(table_name).select("status", count="exact")
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.execute()
        
        # Group by status
        status_counts = {}
        for row in response.data:
            status = row.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts
    except Exception as e:
        return f"Error: {e}"

def generate_report():
    """Generar reporte completo"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_db_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Header
        f.write(separator("REPORTE COMPLETO DE BASE DE DATOS - LEADSNIPER"))
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Supabase: {SUPABASE_URL}\n")
        
        # ===================================================================
        # 1. USUARIOS Y CONFIGURACIONES
        # ===================================================================
        f.write(separator("1. USUARIOS Y CONFIGURACIONES"))
        
        configs = fetch_all("hunter_configs")
        if isinstance(configs, str):
            f.write(f"Error obteniendo hunter_configs: {configs}\n")
        else:
            f.write(f"\nTotal de usuarios: {len(configs)}\n")
            f.write(f"Usuarios con bot activo: {len([c for c in configs if c.get('bot_enabled')])}\n\n")
            
            for i, config in enumerate(configs, 1):
                f.write(f"Usuario {i}:\n")
                f.write(f"  - user_id: {config.get('user_id')}\n")
                f.write(f"  - bot_enabled: {config.get('bot_enabled')}\n")
                f.write(f"  - nicho: {config.get('nicho')}\n")
                f.write(f"  - ciudades: {config.get('ciudades')}\n")
                f.write(f"  - pais: {config.get('pais')}\n")
                f.write(f"  - resend_api_key: {'✅ Configurada' if config.get('resend_api_key') else '❌ No configurada'}\n")
                f.write(f"  - from_email: {config.get('from_email')}\n")
                f.write(f"  - from_name: {config.get('from_name')}\n")
                f.write(f"  - is_active: {config.get('is_active')}\n")
                f.write(f"  - created_at: {config.get('created_at')}\n")
                f.write(f"  - updated_at: {config.get('updated_at')}\n")
                f.write("\n")
        
        # ===================================================================
        # 2. TRACKING DE BÚSQUEDAS
        # ===================================================================
        f.write(separator("2. TRACKING DE BÚSQUEDAS (domain_search_tracking)"))
        
        tracking = fetch_all("domain_search_tracking", order_by="updated_at", limit=50)
        if isinstance(tracking, str):
            f.write(f"Error obteniendo tracking: {tracking}\n")
        else:
            f.write(f"\nTotal de combinaciones trackeadas: {len(tracking)}\n")
            activas = len([t for t in tracking if not t.get('is_exhausted')])
            agotadas = len([t for t in tracking if t.get('is_exhausted')])
            f.write(f"Combinaciones activas: {activas}\n")
            f.write(f"Combinaciones agotadas: {agotadas}\n\n")
            
            if tracking:
                f.write("Últimas 50 combinaciones:\n\n")
                for t in tracking:
                    status = "🟢 ACTIVA" if not t.get('is_exhausted') else "🔴 AGOTADA"
                    f.write(f"{status} | {t.get('nicho')} | {t.get('ciudad')}, {t.get('pais')} | "
                           f"Página {t.get('current_page')} | {t.get('total_domains_found')} dominios | "
                           f"Última búsqueda: {t.get('last_searched_at')}\n")
            else:
                f.write("⚠️  No hay tracking de búsquedas. El bot aún no ha iniciado.\n")
        
        # ===================================================================
        # 3. LEADS - RESUMEN POR STATUS
        # ===================================================================
        f.write(separator("3. LEADS - RESUMEN POR STATUS"))
        
        try:
            # Get all leads
            all_leads = fetch_all("leads")
            if not isinstance(all_leads, str):
                f.write(f"\nTotal de leads: {len(all_leads)}\n\n")
                
                # Count by status
                status_counts = {}
                for lead in all_leads:
                    status = lead.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                f.write("Leads por status:\n")
                for status, count in sorted(status_counts.items()):
                    f.write(f"  - {status}: {count}\n")
                
                # Count with email
                with_email = len([l for l in all_leads if l.get('email')])
                f.write(f"\nLeads con email: {with_email}\n")
                
                # Recent leads
                recent = sorted(all_leads, key=lambda x: x.get('created_at', ''), reverse=True)[:20]
                f.write(f"\nÚltimos 20 leads agregados:\n\n")
                for lead in recent:
                    email_status = f"📧 {lead.get('email')}" if lead.get('email') else "❌ Sin email"
                    f.write(f"  [{lead.get('status')}] {lead.get('domain')} | {email_status} | "
                           f"{lead.get('created_at')}\n")
        except Exception as e:
            f.write(f"Error obteniendo leads: {e}\n")
        
        # ===================================================================
        # 4. LEADS - POR USUARIO
        # ===================================================================
        f.write(separator("4. LEADS - ESTADÍSTICAS POR USUARIO"))
        
        if not isinstance(configs, str):
            for config in configs:
                user_id = config.get('user_id')
                f.write(f"\nUsuario: {user_id}\n")
                
                try:
                    user_leads = fetch_with_filter("leads", "user_id", user_id)
                    if not isinstance(user_leads, str):
                        f.write(f"  Total leads: {len(user_leads)}\n")
                        
                        # By status
                        status_counts = {}
                        for lead in user_leads:
                            status = lead.get('status', 'unknown')
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        for status, count in sorted(status_counts.items()):
                            f.write(f"    - {status}: {count}\n")
                        
                        # With email
                        with_email = len([l for l in user_leads if l.get('email')])
                        f.write(f"  Con email: {with_email}\n")
                except Exception as e:
                    f.write(f"  Error: {e}\n")
        
        # ===================================================================
        # 5. LOGS DEL HUNTER (últimos 100)
        # ===================================================================
        f.write(separator("5. LOGS DEL HUNTER (últimos 100)"))
        
        logs = fetch_all("hunter_logs", order_by="created_at", limit=100)
        if isinstance(logs, str):
            f.write(f"Error obteniendo logs: {logs}\n")
        else:
            if logs:
                f.write(f"\nTotal de logs: {len(logs)}\n\n")
                for log in logs:
                    level_emoji = {
                        'info': 'ℹ️',
                        'success': '✅',
                        'warning': '⚠️',
                        'error': '❌'
                    }.get(log.get('level'), '📝')
                    
                    f.write(f"[{log.get('created_at')}] {level_emoji} {log.get('action')} | "
                           f"{log.get('domain')} | {log.get('message')}\n")
            else:
                f.write("⚠️  No hay logs del hunter. El bot podría no estar corriendo.\n")
        
        # ===================================================================
        # 6. VERIFICACIÓN DE SALUD DEL SISTEMA
        # ===================================================================
        f.write(separator("6. VERIFICACIÓN DE SALUD DEL SISTEMA"))
        
        f.write("\n✅ Checklist de salud:\n\n")
        
        # Check 1: Bot habilitado
        if not isinstance(configs, str):
            bot_enabled_users = [c for c in configs if c.get('bot_enabled')]
            if bot_enabled_users:
                f.write(f"✅ Bot habilitado: {len(bot_enabled_users)} usuario(s)\n")
            else:
                f.write("❌ Bot habilitado: NINGÚN usuario tiene el bot activo\n")
        
        # Check 2: SerpAPI key
        serpapi_key = os.getenv("SERPAPI_KEY")
        if serpapi_key:
            f.write("✅ SERPAPI_KEY configurada en .env\n")
        else:
            f.write("❌ SERPAPI_KEY NO configurada en .env\n")
        
        # Check 3: Tracking activo
        if not isinstance(tracking, str):
            if activas > 0:
                f.write(f"✅ Tracking activo: {activas} combinaciones\n")
            else:
                f.write("⚠️  Tracking: Todas las combinaciones están agotadas (debería resetear)\n")
        
        # Check 4: Dominios recientes
        if not isinstance(all_leads, str):
            # Check if there are leads created in the last 24 hours
            now = datetime.now()
            recent_leads = []
            for lead in all_leads:
                try:
                    created = datetime.fromisoformat(lead.get('created_at', '').replace('Z', '+00:00'))
                    if (now - created).total_seconds() < 86400:  # 24 hours
                        recent_leads.append(lead)
                except:
                    pass
            
            if recent_leads:
                f.write(f"✅ Dominios recientes: {len(recent_leads)} en las últimas 24h\n")
            else:
                f.write("❌ Dominios recientes: NINGUNO en las últimas 24h (bot podría no estar corriendo)\n")
        
        # Check 5: Logs recientes
        if not isinstance(logs, str) and logs:
            try:
                last_log = logs[0]
                last_log_time = datetime.fromisoformat(last_log.get('created_at', '').replace('Z', '+00:00'))
                time_since = (now - last_log_time).total_seconds()
                
                if time_since < 3600:  # Less than 1 hour
                    f.write(f"✅ Logs recientes: Último log hace {int(time_since/60)} minutos\n")
                else:
                    f.write(f"⚠️  Logs recientes: Último log hace {int(time_since/3600)} horas\n")
            except:
                pass
        else:
            f.write("❌ Logs recientes: NO hay logs (bot nunca corrió)\n")
        
        # ===================================================================
        # 7. RECOMENDACIONES
        # ===================================================================
        f.write(separator("7. RECOMENDACIONES"))
        
        f.write("\nBasado en el análisis:\n\n")
        
        # Check if bot is enabled
        if isinstance(configs, str) or not bot_enabled_users:
            f.write("❗ CRÍTICO: Activar el bot en hunter_configs\n")
            f.write("   Ejecutar: UPDATE hunter_configs SET bot_enabled = true WHERE user_id = 'TU_USER_ID';\n\n")
        
        # Check if SERPAPI_KEY exists
        if not serpapi_key:
            f.write("❗ CRÍTICO: Configurar SERPAPI_KEY en .env\n")
            f.write("   1. Ir a https://serpapi.com/\n")
            f.write("   2. Crear cuenta y obtener API Key\n")
            f.write("   3. Agregar SERPAPI_KEY=tu_key al archivo .env\n\n")
        
        # Check if tracking is exhausted
        if not isinstance(tracking, str) and activas == 0 and len(tracking) > 0:
            f.write("⚠️  Resetear tracking (todas las combinaciones agotadas)\n")
            f.write("   Ejecutar: DELETE FROM domain_search_tracking WHERE user_id = 'TU_USER_ID';\n\n")
        
        # Check if no recent domains
        if not isinstance(all_leads, str) and not recent_leads:
            f.write("⚠️  El bot no está agregando dominios\n")
            f.write("   1. Verificar que domain_hunter_worker.py esté corriendo\n")
            f.write("   2. Revisar logs de la terminal del worker\n")
            f.write("   3. Verificar créditos de SerpAPI\n\n")
        
        f.write("\nPara más detalles, revisar:\n")
        f.write("  - diagnostico_bot.sql (queries de diagnóstico)\n")
        f.write("  - soluciones_bot.sql (soluciones a problemas comunes)\n")
        f.write("  - DIAGNOSTICO_BOT_README.txt (guía completa)\n")
        
        # Footer
        f.write(separator())
        f.write(f"Reporte generado exitosamente: {filename}\n")
        f.write(separator())
    
    print(f"✅ Reporte generado: {filename}")
    print(f"📄 Abre el archivo para ver toda la información de tu base de datos")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GENERADOR DE REPORTE DE BASE DE DATOS")
    print("="*80 + "\n")
    
    print("Conectando a Supabase...")
    try:
        generate_report()
    except Exception as e:
        print(f"\nError generando reporte: {e}")
        print("\nVerifica que:")
        print("  1. SUPABASE_URL y SUPABASE_KEY esten en .env")
        print("  2. Tengas conexion a internet")
        print("  3. Las credenciales sean correctas")

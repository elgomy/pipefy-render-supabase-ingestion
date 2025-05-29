#!/usr/bin/env python3
"""
Script para probar el endpoint de debug en Render y verificar configuración
"""

import requests
import json

def test_debug_endpoint():
    """Prueba un endpoint de debug para verificar la configuración en Render"""
    
    # Primero probar el health endpoint
    try:
        print("🔍 Probando endpoint /health...")
        response = requests.get("https://pipefy-render-supabase-ingestion.onrender.com/health", timeout=30)
        response.raise_for_status()
        
        health_data = response.json()
        print("✅ Health endpoint:")
        print(f"   Status: {health_data.get('status')}")
        print(f"   Supabase configurado: {health_data.get('supabase_configured')}")
        print(f"   Pipefy configurado: {health_data.get('pipefy_configured')}")
        print(f"   Storage bucket: {health_data.get('storage_bucket')}")
        
        if not health_data.get('pipefy_configured'):
            print("❌ PROBLEMA: Pipefy no está configurado en Render!")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar health endpoint: {e}")
        return False
    
    # Probar endpoint de debug específico para attachments
    try:
        print("\n🔍 Probando debug de attachments...")
        debug_url = "https://pipefy-render-supabase-ingestion.onrender.com/debug/attachments/1131156124"
        
        response = requests.get(debug_url, timeout=60)
        
        if response.status_code == 404:
            print("⚠️  Endpoint de debug no existe - esto es normal")
            return True
        
        response.raise_for_status()
        debug_data = response.json()
        
        print("✅ Debug de attachments:")
        print(json.dumps(debug_data, indent=2, ensure_ascii=False))
        
        attachments_count = debug_data.get('attachments_count', 0)
        if attachments_count > 0:
            print(f"✅ Se encontraron {attachments_count} attachments")
            return True
        else:
            print("❌ No se encontraron attachments")
            return False
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("⚠️  Endpoint de debug no existe - esto es normal")
            return True
        else:
            print(f"❌ Error HTTP al probar debug endpoint: {e}")
            return False
    except Exception as e:
        print(f"❌ Error al probar debug endpoint: {e}")
        return False

def test_manual_attachment_call():
    """Hace una llamada manual al webhook para debug"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    payload = {
        "data": {
            "card": {
                "id": "1131156124",
                "title": "pepe",
                "current_phase": {
                    "id": "338000020",
                    "name": "Agent - Open Banking"
                }
            },
            "action": "card.move"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Debug-Test/1.0"
    }
    
    try:
        print("\n🧪 Probando webhook para debug...")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Respuesta del webhook:")
        
        # Extraer información detallada
        message = result.get('message', '')
        crewai_response = result.get('crewai_trigger_response', {})
        documents_processed = crewai_response.get('documents_processed', 0)
        
        print(f"   Message: {message}")
        print(f"   Documents processed: {documents_processed}")
        
        # Analizar el mensaje para extraer información
        if "anexos manuseados" in message:
            # Extraer número de anexos del mensaje
            import re
            match = re.search(r'(\d+) anexos manuseados', message)
            if match:
                anexos_encontrados = int(match.group(1))
                print(f"   Anexos encontrados: {anexos_encontrados}")
                
                if anexos_encontrados == 0:
                    print("❌ PROBLEMA: No se encontraron anexos")
                    print("   🔍 Posibles causas:")
                    print("     - Token de Pipefy no configurado en Render")
                    print("     - Error en la consulta GraphQL")
                    print("     - Problema de conectividad")
                    return False
                else:
                    print(f"✅ Se encontraron {anexos_encontrados} anexos")
                    return True
        
        return documents_processed > 0
        
    except Exception as e:
        print(f"❌ Error al probar webhook: {e}")
        return False

if __name__ == "__main__":
    print("🔧 DEBUG DE CONFIGURACIÓN EN RENDER")
    print("=" * 60)
    
    # Probar health endpoint
    health_ok = test_debug_endpoint()
    
    # Probar webhook
    webhook_ok = test_manual_attachment_call()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print(f"   Health endpoint: {'✅' if health_ok else '❌'}")
    print(f"   Webhook funcional: {'✅' if webhook_ok else '❌'}")
    
    if not health_ok:
        print("\n💥 Problema de configuración en Render")
        print("🔧 Acciones requeridas:")
        print("   1. Verificar variables de entorno en Render")
        print("   2. Asegurar que PIPEFY_TOKEN esté configurado")
        print("   3. Verificar conectividad con APIs externas")
    elif not webhook_ok:
        print("\n⚠️  Configuración OK pero webhook no procesa documentos")
        print("🔍 Revisar logs de Render para más detalles")
    else:
        print("\n🎉 ¡Todo funcionando correctamente!") 
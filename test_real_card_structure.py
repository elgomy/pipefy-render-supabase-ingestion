#!/usr/bin/env python3
"""
Script para probar el webhook con la estructura exacta del card
"""

import requests
import json
from datetime import datetime
import time

def get_fresh_card_data():
    """Obtiene datos frescos del card para tener URLs no expiradas"""
    PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"
    
    query = """
    query GetCard($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            current_phase {
                id
                name
            }
            fields {
                name
                value
            }
        }
    }
    """
    
    variables = {"cardId": "1131156124"}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", 
                               json={"query": query, "variables": variables}, 
                               headers=headers)
        response.raise_for_status()
        data = response.json()
        
        card = data.get("data", {}).get("card")
        if card:
            print("✅ Datos frescos del card obtenidos:")
            print(f"   ID: {card.get('id')}")
            print(f"   Título: {card.get('title')}")
            print(f"   Fase: {card.get('current_phase', {}).get('name')}")
            
            # Mostrar campos con documentos
            for field in card.get('fields', []):
                if field.get('value') and 'http' in str(field.get('value', '')):
                    print(f"   📎 {field.get('name')}: {field.get('value')}")
            
            return card
        else:
            print("❌ No se pudo obtener el card")
            return None
            
    except Exception as e:
        print(f"❌ Error al obtener card: {e}")
        return None

def test_webhook_with_fresh_data(card_data):
    """Prueba el webhook con datos frescos del card"""
    webhook_url = "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy"
    
    # Crear payload con la estructura exacta
    payload = {
        "data": {
            "card": card_data,
            "action": "card.move"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        print("\n🚀 Enviando payload con datos frescos al webhook...")
        print(f"   URL: {webhook_url}")
        
        # Mostrar el payload que se enviará
        print("\n📦 Payload a enviar:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("\n✅ Respuesta del webhook:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        
        if 'crewai_trigger_response' in result:
            crewai = result['crewai_trigger_response']
            print(f"\n📊 Respuesta de CrewAI:")
            print(f"   Status: {crewai.get('status')}")
            print(f"   Documents processed: {crewai.get('documents_processed')}")
            print(f"   Checklist URL: {crewai.get('checklist_url')}")
            print(f"   Simulation: {crewai.get('simulation')}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("⏰ Timeout: El webhook tardó más de 120 segundos")
        return False
    except Exception as e:
        print(f"❌ Error al probar webhook: {e}")
        if hasattr(e, 'response'):
            try:
                error_data = e.response.json()
                print(f"   Detalles del error: {error_data}")
            except:
                print(f"   Respuesta del servidor: {e.response.text}")
        return False

def check_url_expiration(url_string):
    """Verifica si una URL tiene expiración y si está vencida"""
    try:
        if 'expires_on=' in url_string:
            # Extraer timestamp de expiración
            expires_part = url_string.split('expires_on=')[1].split('&')[0]
            expires_timestamp = int(expires_part)
            expires_datetime = datetime.fromtimestamp(expires_timestamp)
            current_datetime = datetime.now()
            
            print(f"   🕐 URL expira: {expires_datetime}")
            print(f"   🕐 Hora actual: {current_datetime}")
            
            if current_datetime > expires_datetime:
                print(f"   ❌ URL EXPIRADA (hace {current_datetime - expires_datetime})")
                return False
            else:
                print(f"   ✅ URL válida (expira en {expires_datetime - current_datetime})")
                return True
        else:
            print(f"   ℹ️  URL sin expiración")
            return True
            
    except Exception as e:
        print(f"   ⚠️  Error al verificar expiración: {e}")
        return True

if __name__ == "__main__":
    print("🔍 Probando webhook con estructura real del card...")
    print("=" * 70)
    
    # Obtener datos frescos del card
    print("\n1️⃣ Obteniendo datos frescos del card...")
    card_data = get_fresh_card_data()
    
    if not card_data:
        print("💥 No se pudieron obtener los datos del card")
        exit(1)
    
    # Verificar expiración de URLs
    print("\n2️⃣ Verificando expiración de URLs...")
    for field in card_data.get('fields', []):
        field_value = field.get('value', '')
        if field_value and 'http' in str(field_value):
            print(f"\n📎 Campo: {field.get('name')}")
            try:
                # Intentar parsear como JSON
                urls = json.loads(field_value)
                if isinstance(urls, list):
                    for i, url in enumerate(urls):
                        print(f"   URL {i+1}:")
                        check_url_expiration(url)
                else:
                    print(f"   URL única:")
                    check_url_expiration(field_value)
            except json.JSONDecodeError:
                print(f"   URL única (no JSON):")
                check_url_expiration(field_value)
    
    # Probar webhook
    print("\n3️⃣ Probando webhook...")
    success = test_webhook_with_fresh_data(card_data)
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ¡Prueba completada exitosamente!")
        print("📝 Revisa los logs de Render y Supabase para ver el procesamiento.")
    else:
        print("💥 Error en la prueba del webhook")
        print("🔍 Revisa los logs para más detalles.") 
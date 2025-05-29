#!/usr/bin/env python3
"""
Script para comparar dos cards y identificar diferencias que puedan causar problemas
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"

CARD_WORKING = "1131156124"  # Card que funciona
CARD_NOT_WORKING = "1130856215"  # Card que no funciona

def get_card_detailed_info(card_id):
    """Obtiene información detallada del card"""
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
                field {
                    id
                    type
                    label
                }
            }
            assignees {
                id
                name
                email
            }
            labels {
                id
                name
                color
            }
            created_at
            updated_at
        }
    }
    """
    
    variables = {"cardId": card_id}
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            return {
                "error": data['errors'],
                "card_id": card_id
            }
        
        return data.get("data", {}).get("card")
    except Exception as e:
        return {
            "error": str(e),
            "card_id": card_id
        }

def analyze_card_fields(card_data):
    """Analiza los campos del card para identificar documentos"""
    if not card_data or "error" in card_data:
        return {
            "error": card_data.get("error", "Card no encontrado"),
            "documents": [],
            "document_count": 0
        }
    
    fields = card_data.get('fields', [])
    documents = []
    
    for field in fields:
        field_name = field.get('name', '')
        field_value = field.get('value', '')
        field_type = field.get('field', {}).get('type', '')
        field_label = field.get('field', {}).get('label', '')
        
        # Identificar si es un documento
        is_document = False
        if field_value and isinstance(field_value, str):
            if 'http' in field_value and ('pipefy.com' in field_value or 'attachment' in field_value.lower()):
                is_document = True
        
        documents.append({
            "name": field_name,
            "value": field_value,
            "type": field_type,
            "label": field_label,
            "is_document": is_document,
            "value_length": len(str(field_value)) if field_value else 0
        })
    
    document_fields = [doc for doc in documents if doc['is_document']]
    
    return {
        "documents": documents,
        "document_fields": document_fields,
        "document_count": len(document_fields),
        "total_fields": len(documents)
    }

def check_supabase_processing(card_id):
    """Verifica si el card fue procesado en Supabase"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("documents").select("*").eq("case_id", card_id).execute()
        
        return {
            "processed": len(response.data) > 0,
            "document_count": len(response.data),
            "documents": response.data
        }
    except Exception as e:
        return {
            "error": str(e),
            "processed": False
        }

def test_webhook_with_card(card_id, card_data):
    """Prueba el webhook con datos del card específico"""
    if not card_data or "error" in card_data:
        return {"error": "No se puede probar webhook sin datos del card"}
    
    # Construir payload similar al que enviaría Pipefy
    test_payload = {
        "data": {
            "card": {
                "id": card_id,
                "title": card_data.get('title', ''),
                "current_phase": card_data.get('current_phase', {}),
                "fields": card_data.get('fields', [])
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Pipefy-Webhook/1.0"
    }
    
    try:
        response = requests.post(
            "https://pipefy-render-supabase-ingestion.onrender.com/webhook/pipefy", 
            json=test_payload, 
            headers=headers, 
            timeout=30
        )
        
        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text,
            "error": None
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

if __name__ == "__main__":
    print("🔍 COMPARACIÓN DE CARDS - DIAGNÓSTICO DE PROBLEMAS")
    print("=" * 80)
    
    # Obtener información de ambos cards
    print("📋 Obteniendo información de los cards...")
    card_working = get_card_detailed_info(CARD_WORKING)
    card_not_working = get_card_detailed_info(CARD_NOT_WORKING)
    
    print(f"\n1️⃣ CARD QUE FUNCIONA: {CARD_WORKING}")
    print("-" * 50)
    
    if "error" in card_working:
        print(f"❌ Error: {card_working['error']}")
    else:
        print(f"✅ Título: {card_working.get('title')}")
        print(f"✅ Fase: {card_working.get('current_phase', {}).get('name')}")
        print(f"✅ Creado: {card_working.get('created_at')}")
        
        # Analizar campos
        analysis_working = analyze_card_fields(card_working)
        print(f"✅ Total campos: {analysis_working['total_fields']}")
        print(f"✅ Documentos detectados: {analysis_working['document_count']}")
        
        if analysis_working['document_fields']:
            print("📄 Documentos:")
            for doc in analysis_working['document_fields']:
                print(f"   - {doc['name']}: {doc['value'][:60]}...")
    
    print(f"\n2️⃣ CARD QUE NO FUNCIONA: {CARD_NOT_WORKING}")
    print("-" * 50)
    
    if "error" in card_not_working:
        print(f"❌ Error: {card_not_working['error']}")
    else:
        print(f"✅ Título: {card_not_working.get('title')}")
        print(f"✅ Fase: {card_not_working.get('current_phase', {}).get('name')}")
        print(f"✅ Creado: {card_not_working.get('created_at')}")
        
        # Analizar campos
        analysis_not_working = analyze_card_fields(card_not_working)
        print(f"✅ Total campos: {analysis_not_working['total_fields']}")
        print(f"✅ Documentos detectados: {analysis_not_working['document_count']}")
        
        if analysis_not_working['document_fields']:
            print("📄 Documentos:")
            for doc in analysis_not_working['document_fields']:
                print(f"   - {doc['name']}: {doc['value'][:60]}...")
        else:
            print("⚠️  No se detectaron documentos en este card")
    
    # Verificar procesamiento en Supabase
    print(f"\n3️⃣ VERIFICACIÓN EN SUPABASE")
    print("-" * 50)
    
    supabase_working = check_supabase_processing(CARD_WORKING)
    supabase_not_working = check_supabase_processing(CARD_NOT_WORKING)
    
    print(f"Card {CARD_WORKING}: {'✅ Procesado' if supabase_working.get('processed') else '❌ No procesado'} ({supabase_working.get('document_count', 0)} docs)")
    print(f"Card {CARD_NOT_WORKING}: {'✅ Procesado' if supabase_not_working.get('processed') else '❌ No procesado'} ({supabase_not_working.get('document_count', 0)} docs)")
    
    # Probar webhook con ambos cards
    print(f"\n4️⃣ PRUEBA DE WEBHOOK")
    print("-" * 50)
    
    if not ("error" in card_working):
        print(f"Probando webhook con card {CARD_WORKING}...")
        webhook_test_working = test_webhook_with_card(CARD_WORKING, card_working)
        print(f"   Resultado: {'✅ Éxito' if webhook_test_working.get('success') else '❌ Error'}")
        if webhook_test_working.get('error'):
            print(f"   Error: {webhook_test_working['error']}")
        elif webhook_test_working.get('response'):
            response = webhook_test_working['response']
            if isinstance(response, dict):
                print(f"   Mensaje: {response.get('message', 'Sin mensaje')}")
    
    if not ("error" in card_not_working):
        print(f"\nProbando webhook con card {CARD_NOT_WORKING}...")
        webhook_test_not_working = test_webhook_with_card(CARD_NOT_WORKING, card_not_working)
        print(f"   Resultado: {'✅ Éxito' if webhook_test_not_working.get('success') else '❌ Error'}")
        if webhook_test_not_working.get('error'):
            print(f"   Error: {webhook_test_not_working['error']}")
        elif webhook_test_not_working.get('response'):
            response = webhook_test_not_working['response']
            if isinstance(response, dict):
                print(f"   Mensaje: {response.get('message', 'Sin mensaje')}")
    
    # Análisis de diferencias
    print(f"\n5️⃣ ANÁLISIS DE DIFERENCIAS")
    print("-" * 50)
    
    if not ("error" in card_working) and not ("error" in card_not_working):
        analysis_working = analyze_card_fields(card_working)
        analysis_not_working = analyze_card_fields(card_not_working)
        
        print("🔍 Diferencias encontradas:")
        
        # Comparar número de documentos
        docs_working = analysis_working['document_count']
        docs_not_working = analysis_not_working['document_count']
        
        if docs_working != docs_not_working:
            print(f"   📄 Documentos: Card funcional tiene {docs_working}, card problemático tiene {docs_not_working}")
        
        # Comparar fases
        phase_working = card_working.get('current_phase', {}).get('name', '')
        phase_not_working = card_not_working.get('current_phase', {}).get('name', '')
        
        if phase_working != phase_not_working:
            print(f"   📍 Fases: Card funcional está en '{phase_working}', card problemático en '{phase_not_working}'")
        
        # Comparar tipos de campos
        if docs_not_working == 0:
            print("   ⚠️  PROBLEMA PRINCIPAL: El card problemático no tiene documentos detectados")
            print("   💡 Posibles causas:")
            print("      - Los documentos no están en campos de tipo 'attachment'")
            print("      - Las URLs no contienen 'pipefy.com' o 'attachment'")
            print("      - Los campos están vacíos o tienen formato incorrecto")
            
            print("\n   📋 Todos los campos del card problemático:")
            for field in analysis_not_working['documents']:
                print(f"      - {field['name']} ({field['type']}): {str(field['value'])[:100]}...")
    
    print(f"\n📋 CONCLUSIONES")
    print("=" * 80)
    print("Para resolver el problema:")
    print("1. Verifica que el card problemático tenga documentos adjuntos")
    print("2. Asegúrate de que esté en la fase correcta para activar el webhook")
    print("3. Revisa que los documentos tengan URLs válidas de Pipefy")
    print("4. Considera mover el card a la fase 'Agent - Open Banking' para activar el procesamiento") 
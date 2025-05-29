#!/usr/bin/env python3
"""
Script para probar el movimiento manual de cards y activar el webhook
"""

import requests
import json
import time

# Configuración
PIPEFY_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NDU1NDg1NzAsImp0aSI6ImViNDQ0NmYzLTk4ZjktNDdmZi1hYWQ3LTMzNWJkNTc2M2NlMSIsInN1YiI6MzA2MzA5NjQ1LCJ1c2VyIjp7ImlkIjozMDYzMDk2NDUsImVtYWlsIjoiaWdvckBjYXBpdGFsZmluYW5jYXMuY29tLmJyIn19.9CMSBmLWdxH4uWkmlCyRCfs8SKo5UWAw0c161Jaw__PV1o5GRRmNmGUT_RUFhk_JS8J0bXvNtIqsuBj9uy8QhQ"

TARGET_PHASE_ID = "338000020"  # Agent - Open Banking
CARDS_TO_TEST = ["1131156124", "1130856215"]

def get_card_current_phase(card_id):
    """Obtiene la fase actual del card"""
    query = """
    query GetCard($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            current_phase {
                id
                name
            }
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
            return {"error": data['errors']}
        
        card = data.get("data", {}).get("card")
        return card
    except Exception as e:
        return {"error": str(e)}

def get_pipe_phases():
    """Obtiene todas las fases del pipe"""
    query = """
    query GetPipePhases($pipeId: ID!) {
        pipe(id: $pipeId) {
            phases {
                id
                name
            }
        }
    }
    """
    
    variables = {"pipeId": "306294445"}
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
            return {"error": data['errors']}
        
        phases = data.get("data", {}).get("pipe", {}).get("phases", [])
        return phases
    except Exception as e:
        return {"error": str(e)}

def move_card_to_phase(card_id, phase_id):
    """Mueve un card a una fase específica"""
    mutation = """
    mutation MoveCard($cardId: ID!, $phaseId: ID!) {
        moveCardToPhase(input: {card_id: $cardId, destination_phase_id: $phaseId}) {
            card {
                id
                current_phase {
                    id
                    name
                }
            }
        }
    }
    """
    
    variables = {
        "cardId": card_id,
        "phaseId": phase_id
    }
    
    headers = {
        "Authorization": f"Bearer {PIPEFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.pipefy.com/graphql", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            return {"error": data['errors']}
        
        return data.get("data", {}).get("moveCardToPhase", {}).get("card")
    except Exception as e:
        return {"error": str(e)}

def check_recent_processing():
    """Verifica si hay procesamiento reciente en Supabase"""
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = "https://aguoqgqbdbyipztgrmbd.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFndW9xZ3FiZGJ5aXB6dGdybWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyMzMzMzcsImV4cCI6MjA2MjgwOTMzN30.L3qDlRsyXu5VTdygr3peKraeBzaR7Sd-5FfK-zmJ-4M"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Buscar documentos procesados en los últimos 5 minutos
        from datetime import datetime, timedelta
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        response = supabase.table("documents").select("*").gte("created_at", five_minutes_ago).execute()
        return response.data
    except Exception as e:
        return []

if __name__ == "__main__":
    print("🎯 PRUEBA DE MOVIMIENTO MANUAL DE CARDS")
    print("=" * 80)
    
    # 1. Obtener fases disponibles
    print("1️⃣ FASES DISPONIBLES")
    print("-" * 40)
    phases = get_pipe_phases()
    
    if isinstance(phases, dict) and "error" in phases:
        print(f"❌ Error obteniendo fases: {phases['error']}")
        exit(1)
    
    print("Fases del pipe:")
    for phase in phases:
        marker = "🎯" if phase['id'] == TARGET_PHASE_ID else "  "
        print(f"{marker} {phase['name']} (ID: {phase['id']})")
    
    # 2. Verificar estado actual de los cards
    print(f"\n2️⃣ ESTADO ACTUAL DE LOS CARDS")
    print("-" * 40)
    
    cards_info = {}
    for card_id in CARDS_TO_TEST:
        card_info = get_card_current_phase(card_id)
        cards_info[card_id] = card_info
        
        if "error" in card_info:
            print(f"❌ Card {card_id}: Error - {card_info['error']}")
        else:
            current_phase = card_info.get('current_phase', {})
            phase_name = current_phase.get('name', 'Desconocida')
            phase_id = current_phase.get('id', 'Desconocido')
            
            if phase_id == TARGET_PHASE_ID:
                print(f"⚠️  Card {card_id} ({card_info.get('title')}): YA está en '{phase_name}'")
                print(f"   Para activar el webhook, debe moverse DESDE otra fase HACIA esta")
            else:
                print(f"✅ Card {card_id} ({card_info.get('title')}): En '{phase_name}' (ID: {phase_id})")
                print(f"   Listo para mover a 'Agent - Open Banking'")
    
    # 3. Instrucciones para activar el webhook
    print(f"\n3️⃣ INSTRUCCIONES PARA ACTIVAR EL WEBHOOK")
    print("-" * 40)
    
    cards_ready_to_move = []
    cards_already_in_target = []
    
    for card_id, card_info in cards_info.items():
        if "error" not in card_info:
            current_phase_id = card_info.get('current_phase', {}).get('id')
            if current_phase_id == TARGET_PHASE_ID:
                cards_already_in_target.append(card_id)
            else:
                cards_ready_to_move.append(card_id)
    
    if cards_ready_to_move:
        print(f"✅ Cards listos para mover a 'Agent - Open Banking':")
        for card_id in cards_ready_to_move:
            card_info = cards_info[card_id]
            print(f"   - Card {card_id} ({card_info.get('title')})")
        
        print(f"\n🚀 Para activar el webhook automáticamente:")
        print(f"   1. Ve a Pipefy y mueve estos cards a 'Agent - Open Banking'")
        print(f"   2. El webhook se activará inmediatamente")
        print(f"   3. Verifica los logs de Render para confirmar")
    
    if cards_already_in_target:
        print(f"\n⚠️  Cards que YA están en la fase objetivo:")
        for card_id in cards_already_in_target:
            card_info = cards_info[card_id]
            print(f"   - Card {card_id} ({card_info.get('title')})")
        
        print(f"\n💡 Para probar con estos cards:")
        print(f"   1. Muévelos PRIMERO a otra fase (ej: 'Verificação de Crédito')")
        print(f"   2. LUEGO muévelos de vuelta a 'Agent - Open Banking'")
        print(f"   3. Esto activará el webhook")
    
    # 4. Verificar procesamiento reciente
    print(f"\n4️⃣ PROCESAMIENTO RECIENTE")
    print("-" * 40)
    
    recent_docs = check_recent_processing()
    if recent_docs:
        print(f"📊 Documentos procesados en los últimos 5 minutos: {len(recent_docs)}")
        for doc in recent_docs:
            print(f"   - Card {doc['case_id']}: {doc['name']} ({doc['created_at']})")
    else:
        print(f"📊 No hay documentos procesados en los últimos 5 minutos")
    
    print(f"\n🔗 ENLACES ÚTILES:")
    print("-" * 40)
    print(f"   - Pipe en Pipefy: https://app.pipefy.com/pipes/306294445")
    print(f"   - Logs de Render: https://dashboard.render.com/web/srv-d0rm9cre5dus73ahn2n0/logs")
    print(f"   - Supabase Dashboard: https://supabase.com/dashboard/project/aguoqgqbdbyipztgrmbd")
    
    print(f"\n📋 RESUMEN:")
    print("=" * 80)
    print(f"🔍 PROBLEMA IDENTIFICADO: El webhook solo se activa al mover cards HACIA 'Agent - Open Banking'")
    print(f"✅ SOLUCIÓN: Asegúrate de que el card NO esté ya en esa fase antes de moverlo")
    print(f"🎯 FILTRO DEL WEBHOOK: {{'to_phase_id': [338000020]}} - Solo movimientos HACIA la fase objetivo") 
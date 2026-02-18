import requests
import json

API_URL = "http://localhost:8000/api/analyze"

# Simple test
payload = {
    "prompt": "Write a function to add two numbers",
    "code": """def add_numbers(a, b):
    print(f'Adding {a} and {b}')
    logging.info('Addition operation')
    return a + b
"""
}

print("Testing API with simple NPC detection...")
print(f"Sending to: {API_URL}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(API_URL, json=payload, timeout=60)
    print(f"\n✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response:")
        print(json.dumps(data, indent=2))
        
        if 'linguistic_results' in data:
            ling = data['linguistic_results']
            print(f"\n🔍 Linguistic Analysis:")
            print(f"  - NPC Issues: {ling.get('npc_found', False)}")
            print(f"  - NPC Count: {ling.get('npc_count', 0)}")
            if 'npc_confidence' in ling:
                print(f"  - NPC Confidence: {ling['npc_confidence']}")
            if 'npc_severity' in ling:
                print(f"  - NPC Severity: {ling['npc_severity']}")
            if 'npc_consensus' in ling:
                print(f"  - NPC Consensus: {ling['npc_consensus']}")
            if 'npc_reliability' in ling:
                print(f"  - NPC Reliability: {ling['npc_reliability']}")
            if 'npc_layers_used' in ling:
                print(f"  - Layers Used: {ling['npc_layers_used']}")
    else:
        print(f"\n❌ Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

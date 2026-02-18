import requests
import json

API_URL = "http://localhost:8000/api/analyze"

payload = {
    "prompt": "Write a function to add two numbers",
    "code": """def add_numbers(a, b):
    print(f'Adding {a} and {b}')
    logging.info('Addition operation')
    return a + b
"""
}

print("Testing linguistic results with aggregation fields...")
response = requests.post(API_URL, json=payload, timeout=30)

if response.status_code == 200:
    data = response.json()
    
    # Check if linguistic_results is in the response
    print("\n📊 Full Response Keys:")
    print(json.dumps(list(data.keys()), indent=2))
    
    print("\n🔍 Checking for linguistic data...")
    # The linguistic results might be flattened into the main response
    # or embedded in bug_patterns
    
    # Let's see the full execution logs
    print("\n📋 Execution Logs:")
    for log in data.get('execution_logs', []):
        print(f"  {log['stage']}: {log['success']} ({log['execution_time']}s)")
        if log['error_message']:
            print(f"    Error: {log['error_message']}")
    
    print("\n🐛 Bug Patterns Found:")
    for bp in data.get('bug_patterns', []):
        print(f"  - {bp['pattern_name']}: severity={bp['severity']}, confidence={bp['confidence']}")
    
else:
    print(f"Error: {response.status_code}")
    print(response.text)

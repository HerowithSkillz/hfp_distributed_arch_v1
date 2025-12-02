import requests
import random
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# CONFIGURATION: IP Addresses of your laptops
# Find these by running 'ipconfig' (Windows) and 'ip a' (Linux)
NODES = [
    {
        "name": "Windows_Nvidia",
        "url": "http://172.20.10.3:8080/v1/chat/completions",
        "model": "qwen2.5-1.5b"
    },
    {
        "name": "Linux_AMD",
        "url": "http://172.20.10.6:5001/v1/chat/completions",
        "model": "qwen2.5-0.5b"
    }
]

@csrf_exempt
def query_llm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_prompt = data.get('prompt', '')

            # 1. Shuffle nodes to balance the load
            # random.shuffle modifies the list in-place
            available_nodes = NODES.copy()
            random.shuffle(available_nodes)

            # 2. Payload conforming to OpenAI Standard
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }

            # 3. Try nodes one by one (Failover Logic)
            for node in available_nodes:
                print(f"🔄 Trying node: {node['name']} ({node['url']})...")
                try:
                    response = requests.post(
                        node['url'], 
                        json=payload, 
                        timeout=30  # Don't wait forever
                    )
                    
                    if response.status_code == 200:
                        ai_response = response.json()
                        content = ai_response['choices'][0]['message']['content']
                        
                        return JsonResponse({
                            'status': 'success',
                            'node_used': node['name'],
                            'response': content
                        })
                    else:
                        print(f"❌ Node {node['name']} returned Error: {response.status_code}")

                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Node {node['name']} unreachable: {e}")
                    continue # Try the next node in the list

            # 4. If loop finishes and no one answered
            return JsonResponse({'error': 'All Worker Nodes are offline!'}, status=503)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)


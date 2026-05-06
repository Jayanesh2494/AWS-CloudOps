import requests
import json
import subprocess
import time
import os

# Start server
backend_dir = r"c:\Users\asiva\Downloads\aws-cloudops-chatbot\backend"
server = subprocess.Popen(['python', 'app.py'], cwd=backend_dir)
time.sleep(3)  # Wait for server to start

# Test conversation flow
try:
    # First message: "serverless APIs"
    print("=== Testing: 'serverless APIs' ===")
    response1 = requests.post('http://127.0.0.1:5000/api/chat',
                           json={'message': 'serverless APIs', 'session_id': 'test-session'})
    print('Status Code:', response1.status_code)
    result1 = response1.json()
    print('Bot Reply:', result1['botReply'])
    print('Action Taken:', result1.get('action_taken'))
    print('Action Result:', result1.get('action_result'))
    print()

    # Second message: "medium traffic"
    print("=== Testing: 'medium traffic' ===")
    response2 = requests.post('http://127.0.0.1:5000/api/chat',
                           json={'message': 'medium traffic', 'session_id': 'test-session'})
    print('Status Code:', response2.status_code)
    result2 = response2.json()
    print('Bot Reply:', result2['botReply'])
    print('Action Taken:', result2.get('action_taken'))
    print('Action Result:', result2.get('action_result'))

except Exception as e:
    print('Error:', e)
finally:
    server.terminate()
from app import app
import json

client = app.test_client()

print('='*60)
print('TESTING IMPROVED CONVERSATION ENGINE')
print('='*60)

# Test 1: User says they want to deploy
print('\n1. USER: I want to deploy a serverless API')
print('-'*60)
response = client.post('/chat', json={'message': 'I want to deploy a serverless API', 'accountMode': 'our'})
data = response.get_json()
print(f'Bot Response:\n{data.get("botReply", "No reply")}')
print(f'\nExtracted Params: {data.get("extractedParams", {})}')
print(f'Parameters Gathered: {data.get("parametersGathered", 0)}')
print(f'Parameters Needed: {data.get("parametersNeeded", 0)}')

# Test 2: User provides memory size
print('\n\n2. USER: I need 512 MB of memory for my Lambda')
print('-'*60)
response = client.post('/chat', json={'message': 'I need 512 MB of memory for my Lambda', 'accountMode': 'our'})
data = response.get_json()
print(f'Bot Response:\n{data.get("botReply", "No reply")}')
print(f'Extracted Params: {data.get("extractedParams", {})}')

# Test 3: Provide all params at once
print('\n\n3. USER: Deploy with 1024 MB memory, 60 second timeout, dev stage')
print('-'*60)
response = client.post('/chat', json={'message': 'Deploy with 1024 MB memory, 60 second timeout, dev stage', 'accountMode': 'our'})
data = response.get_json()
print(f'Bot Response:\n{data.get("botReply", "No reply")}')
print(f'Extracted Params: {data.get("extractedParams", {})}')
print(f'Ready to Deploy: {data.get("readyToDeploy", False)}')

print('\n' + '='*60)
print('TEST COMPLETE')
print('='*60)

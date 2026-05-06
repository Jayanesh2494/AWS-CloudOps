#!/usr/bin/env python3
"""
AWS CloudOps Chatbot - Integration Testing Script
Test all endpoints and intents without frontend
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, status, response=None):
    """Print test result"""
    symbol = f"{Colors.GREEN}✅{Colors.RESET}" if status else f"{Colors.RED}❌{Colors.RESET}"
    print(f"{symbol} {name}")
    if response and not status:
        print(f"   Response: {response}")

def print_header(title):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.RESET}\n")

def test_health():
    """Test /health endpoint"""
    print_header("TEST 1: Health Check")
    try:
        r = requests.get(f"{API_BASE}/health")
        success = r.status_code == 200
        print_test("GET /health", success, r.text if not success else None)
        if success:
            print(f"   Service: {r.json()['service']}")
            print(f"   Region: {r.json()['region']}")
        return success
    except Exception as e:
        print_test("GET /health", False, str(e))
        return False

def test_session_creation():
    """Test /api/session endpoint"""
    print_header("TEST 2: Session Creation")
    try:
        r = requests.post(f"{API_BASE}/api/session", headers=HEADERS, json={})
        success = r.status_code == 201
        print_test("POST /api/session", success, r.text if not success else None)
        if success:
            session_id = r.json()['sessionId']
            print(f"   SessionId: {session_id}")
            return session_id
        return None
    except Exception as e:
        print_test("POST /api/session", False, str(e))
        return None

def test_set_mode(session_id):
    """Test /api/set-mode endpoint"""
    print_header("TEST 3: Set Account Mode")
    try:
        payload = {
            "sessionId": session_id,
            "mode": "OUR"
        }
        r = requests.post(f"{API_BASE}/api/set-mode", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test(f"POST /api/set-mode (OUR)", success, r.text if not success else None)
        if success:
            print(f"   Mode: {r.json()['mode']}")
        return success
    except Exception as e:
        print_test("POST /api/set-mode", False, str(e))
        return False

def test_lex_intents_config():
    """Test /api/lex-intents endpoint"""
    print_header("TEST 4: Lex Intents Configuration")
    try:
        r = requests.get(f"{API_BASE}/api/lex-intents")
        success = r.status_code == 200
        print_test("GET /api/lex-intents", success, r.text if not success else None)
        if success:
            intents = r.json()['intents']
            count = r.json()['count']
            print(f"   Total intents: {count}")
            print(f"   Intents: {', '.join(intents.keys())}")
        return success
    except Exception as e:
        print_test("GET /api/lex-intents", False, str(e))
        return False

def test_chat_greeting(session_id):
    """Test /api/chat with GreetingIntent"""
    print_header("TEST 5: Chat - Greeting Intent")
    try:
        payload = {
            "sessionId": session_id,
            "message": "hello"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (greeting)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Message: {data['message'][:100]}...")
            print(f"   Requires Action: {data.get('requiresAction', False)}")
        return success
    except Exception as e:
        print_test("POST /api/chat (greeting)", False, str(e))
        return False

def test_chat_help(session_id):
    """Test /api/chat with HelpIntent"""
    print_header("TEST 6: Chat - Help Intent")
    try:
        payload = {
            "sessionId": session_id,
            "message": "what can you do"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (help)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Message: {data['message'][:100]}...")
        return success
    except Exception as e:
        print_test("POST /api/chat (help)", False, str(e))
        return False

def test_chat_deploy(session_id):
    """Test /api/chat with DeployIntent"""
    print_header("TEST 7: Chat - Deploy Intent")
    try:
        payload = {
            "sessionId": session_id,
            "message": "deploy a serverless api with high traffic"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (deploy)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Requires Action: {data.get('requiresAction', False)}")
            if 'extractedParams' in data:
                print(f"   Extracted Params: {data['extractedParams']}")
            if 'actions' in data and data['actions']:
                print(f"   Actions: {[a['label'] for a in data['actions']]}")
        return success
    except Exception as e:
        print_test("POST /api/chat (deploy)", False, str(e))
        return False

def test_chat_list(session_id):
    """Test /api/chat with ListResourcesIntent"""
    print_header("TEST 8: Chat - List Resources Intent")
    try:
        payload = {
            "sessionId": session_id,
            "message": "list my resources"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (list)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Deployments: {len(data.get('deployments', []))}")
        return success
    except Exception as e:
        print_test("POST /api/chat (list)", False, str(e))
        return False

def test_chat_terminate(session_id):
    """Test /api/chat with TerminateDeploymentIntent"""
    print_header("TEST 9: Chat - Terminate Intent")
    try:
        payload = {
            "sessionId": session_id,
            "message": "delete my deployment"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (terminate)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Requires Confirmation: {data.get('requiresConfirmation', False)}")
        return success
    except Exception as e:
        print_test("POST /api/chat (terminate)", False, str(e))
        return False

def test_chat_question(session_id):
    """Test /api/chat with GeneralQuestionIntent"""
    print_header("TEST 10: Chat - General Question")
    try:
        payload = {
            "sessionId": session_id,
            "message": "what is a VPC"
        }
        r = requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/chat (question)", success, r.text if not success else None)
        if success:
            data = r.json()
            print(f"   Intent: {data['intent']}")
            print(f"   Message: {data['message'][:100]}...")
        return success
    except Exception as e:
        print_test("POST /api/chat (question)", False, str(e))
        return False

def test_list_resources(session_id):
    """Test /api/list-resources endpoint"""
    print_header("TEST 11: List Resources Endpoint")
    try:
        payload = {"sessionId": session_id}
        r = requests.post(f"{API_BASE}/api/list-resources", headers=HEADERS, json=payload)
        success = r.status_code == 200
        print_test("POST /api/list-resources", success, r.text if not success else None)
        if success:
            print(f"   Deployments: {r.json()['count']}")
        return success
    except Exception as e:
        print_test("POST /api/list-resources", False, str(e))
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}AWS CloudOps Chatbot - Integration Tests{Colors.RESET}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE}\n")

    # Run tests
    results = []
    
    results.append(("Health Check", test_health()))
    session_id = test_session_creation()
    if session_id:
        results.append(("Session Creation", True))
        results.append(("Set Mode", test_set_mode(session_id)))
        results.append(("Lex Intents Config", test_lex_intents_config()))
        results.append(("Chat - Greeting", test_chat_greeting(session_id)))
        results.append(("Chat - Help", test_chat_help(session_id)))
        results.append(("Chat - Deploy", test_chat_deploy(session_id)))
        results.append(("Chat - List", test_chat_list(session_id)))
        results.append(("Chat - Terminate", test_chat_terminate(session_id)))
        results.append(("Chat - Question", test_chat_question(session_id)))
        results.append(("List Resources", test_list_resources(session_id)))
    else:
        results.append(("Session Creation", False))

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, status in results:
        symbol = f"{Colors.GREEN}✅{Colors.RESET}" if status else f"{Colors.RED}❌{Colors.RESET}"
        print(f"{symbol} {name}")
    
    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}🎉 All tests passed!{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}⚠️  Some tests failed. Check logs above.{Colors.RESET}\n")

if __name__ == "__main__":
    main()

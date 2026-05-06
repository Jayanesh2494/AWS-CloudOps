#!/usr/bin/env python3
"""
Test script for the validate-role endpoint
"""
import urllib.request
import json

def test_validate_role():
    url = "http://127.0.0.1:5000/validate-role"

    # Test with invalid role ARN (provider account)
    payload = {
        "roleArn": "arn:aws:iam::553015941729:role/CloudOpsChatbotRole",
        "externalId": "cloudops-chatbot-2024",
        "region": "us-east-1"
    }

    print("Testing validate-role endpoint with provider account role...")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Status Code: {response.getcode()}")
            print(f"Response: {json.dumps(result, indent=2)}")
    except urllib.error.HTTPError as e:
        # Read error response
        error_content = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_content)
            print(f"Status Code: {e.code}")
            print(f"Error Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Status Code: {e.code}")
            print(f"Error Content: {error_content}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with user account role ARN (will fail with STS error)
    payload2 = {
        "roleArn": "arn:aws:iam::123456789012:role/CloudOpsChatbotRole",
        "externalId": "cloudops-chatbot-2024",
        "region": "us-east-1"
    }

    print("\nTesting validate-role endpoint with user account role...")
    print(f"Payload: {json.dumps(payload2, indent=2)}")

    try:
        data = json.dumps(payload2).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"Status Code: {response.getcode()}")
            print(f"Response: {json.dumps(result, indent=2)}")
    except urllib.error.HTTPError as e:
        # Read error response
        error_content = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_content)
            print(f"Status Code: {e.code}")
            print(f"Error Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Status Code: {e.code}")
            print(f"Error Content: {error_content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_validate_role()
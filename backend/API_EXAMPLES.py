"""
AWS CloudOps Chatbot - API Request/Response Examples
Copy-paste ready for testing
"""

# ✅ 1. CREATE SESSION
REQUEST_SESSION = {
    "curl": """
curl -X POST http://localhost:5000/api/session \\
  -H "Content-Type: application/json" \\
  -d '{}'
    """,
    "payload": {},
    "response_200": {
        "status": "success",
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "timestamp": "2026-01-23T10:00:00.000000"
    }
}

# ✅ 2. SET ACCOUNT MODE (OUR)
REQUEST_SET_MODE_OUR = {
    "curl": """
curl -X POST http://localhost:5000/api/set-mode \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "mode": "OUR"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "mode": "OUR"
    },
    "response_200": {
        "status": "success",
        "message": "Using provider account for deployments",
        "mode": "OUR"
    }
}

# ✅ 3. SET ACCOUNT MODE (USER)
REQUEST_SET_MODE_USER = {
    "curl": """
curl -X POST http://localhost:5000/api/set-mode \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "mode": "USER",
    "roleArn": "arn:aws:iam::123456789012:role/CloudOpsRole",
    "externalId": "your-secure-external-id"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "mode": "USER",
        "roleArn": "arn:aws:iam::123456789012:role/CloudOpsRole",
        "externalId": "your-secure-external-id"
    },
    "response_200": {
        "status": "success",
        "message": "Assuming role in account 123456789012",
        "mode": "USER",
        "accountId": "123456789012",
        "arn": "arn:aws:iam::123456789012:user/assumed-user"
    },
    "response_400": {
        "status": "error",
        "message": "Failed to set mode: User: arn:aws:iam::111111111111:user/test is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::123456789012:role/CloudOpsRole"
    }
}

# ✅ 4. CHAT - GREETING INTENT
REQUEST_CHAT_GREETING = {
    "curl": """
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "hello"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "hello"
    },
    "response_200": {
        "status": "success",
        "intent": "GreetingIntent",
        "message": "Hello! I'm your AWS CloudOps assistant. I can help you deploy, manage, and monitor cloud infrastructure across your AWS account or a customer account. What would you like to do today?",
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "timestamp": "2026-01-23T10:01:00.000000",
        "slots": {},
        "requiresAction": False,
        "actions": []
    }
}

# ✅ 5. CHAT - HELP INTENT
REQUEST_CHAT_HELP = {
    "curl": """
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "what can you do"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "what can you do"
    },
    "response_200": {
        "status": "success",
        "intent": "HelpIntent",
        "message": "I can help you with:\n1. **Deploy** serverless APIs, S3 websites, VPCs, and more\n2. **List** your active deployments and resources\n3. **Describe** deployment details\n4. **Update** configurations (memory, timeout, scaling)\n5. **Terminate** deployments (with confirmation)\n6. **Answer** AWS and cloud architecture questions",
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "timestamp": "2026-01-23T10:02:00.000000",
        "slots": {},
        "requiresAction": False,
        "actions": []
    }
}

# ✅ 6. CHAT - DEPLOY INTENT (WITH EXTRACTION)
REQUEST_CHAT_DEPLOY = {
    "curl": """
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "deploy a serverless api with high traffic"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "deploy a serverless api with high traffic"
    },
    "response_200": {
        "status": "success",
        "intent": "DeployIntent",
        "message": "Great! I'll help you deploy a serverless API optimized for high traffic. Let me confirm the architecture and parameters.",
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "timestamp": "2026-01-23T10:03:00.000000",
        "slots": {
            "templateType": "serverless-api",
            "trafficLevel": "high"
        },
        "requiresAction": True,
        "extractedParams": {
            "templateType": "serverless-api",
            "trafficLevel": "high",
            "region": "us-east-1",
            "stageName": "dev",
            "memorySize": "1024"
        },
        "actions": [
            {
                "type": "deploy",
                "label": "Deploy",
                "endpoint": "/api/deploy"
            }
        ]
    }
}

# ✅ 7. DEPLOY ENDPOINT
REQUEST_DEPLOY = {
    "curl": """
curl -X POST http://localhost:5000/api/deploy \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "templateType": "serverless-api",
    "parameters": {
      "apiName": "MyOrdersAPI",
      "region": "us-east-1",
      "stageName": "dev",
      "trafficLevel": "high",
      "memorySize": 1024,
      "timeout": 120
    }
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "templateType": "serverless-api",
        "parameters": {
            "apiName": "MyOrdersAPI",
            "region": "us-east-1",
            "stageName": "dev",
            "trafficLevel": "high",
            "memorySize": 1024,
            "timeout": 120
        }
    },
    "response_201": {
        "status": "success",
        "message": "Deployment initiated",
        "deploymentId": "xyz-789-abc-123",
        "architecturePlan": """
## Architecture Plan: Serverless API

### Components:
- **API Gateway**: REST API with auto-scaling
- **Lambda**: 1024 MB, 120 second timeout (optimized for high traffic)
- **DynamoDB**: Table 'orders' with provisioned billing
- **CloudWatch**: Full request/error logging

### Traffic Handling:
- Auto-scaling Lambda (reserved concurrency: 1000)
- DynamoDB on-demand billing
- API Gateway throttling: 10,000 requests/sec

### Cost Estimate:
- API Gateway: ~$35/month
- Lambda: ~$150/month (1000 invocations/day)
- DynamoDB: ~$100/month (on-demand)
- **Total: ~$285/month**
        """,
        "nextStep": "Execute CDK deploy",
        "timestamp": "2026-01-23T10:04:00.000000"
    }
}

# ✅ 8. LIST RESOURCES ENDPOINT
REQUEST_LIST_RESOURCES = {
    "curl": """
curl -X POST http://localhost:5000/api/list-resources \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    },
    "response_200": {
        "status": "success",
        "deployments": [
            {
                "deploymentId": "xyz-789-abc-123",
                "template_id": "serverless-api",
                "stack_name": "serverless-api-xyz78abc",
                "region": "us-east-1",
                "account_mode": "OUR",
                "status": "ACTIVE",
                "created_at": "2026-01-23T10:04:00.000000",
                "params": {
                    "apiName": "MyOrdersAPI",
                    "trafficLevel": "high"
                },
                "outputs": {
                    "ApiUrl": "https://abcd1234.execute-api.us-east-1.amazonaws.com/dev"
                }
            },
            {
                "deploymentId": "abc-456-def-789",
                "template_id": "s3-static-website",
                "stack_name": "s3-static-website-abc456",
                "region": "us-west-2",
                "account_mode": "USER",
                "status": "ACTIVE",
                "created_at": "2026-01-20T14:30:00.000000",
                "params": {
                    "domain": "example.com"
                },
                "outputs": {
                    "CloudFrontUrl": "https://d1234567890abc.cloudfront.net"
                }
            }
        ],
        "count": 2,
        "timestamp": "2026-01-23T10:05:00.000000"
    }
}

# ✅ 9. TERMINATE INTENT (CHAT)
REQUEST_CHAT_TERMINATE = {
    "curl": """
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "delete my api"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "delete my api"
    },
    "response_200": {
        "status": "success",
        "intent": "TerminateDeploymentIntent",
        "message": "⚠️ **WARNING**: Terminating a deployment will **permanently delete** all AWS resources (Lambda, API Gateway, DynamoDB tables, etc.). This action cannot be undone.\n\nTo confirm termination of 'xyz-789-abc-123', please type: **CONFIRM**",
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "timestamp": "2026-01-23T10:06:00.000000",
        "slots": {},
        "requiresAction": True,
        "requiresConfirmation": True,
        "actions": [
            {
                "type": "confirm",
                "label": "Confirm Termination",
                "endpoint": "/api/terminate",
                "requiresText": "CONFIRM"
            }
        ]
    }
}

# ✅ 10. TERMINATE ENDPOINT
REQUEST_TERMINATE = {
    "curl": """
curl -X POST http://localhost:5000/api/terminate \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "deploymentId": "xyz-789-abc-123",
    "confirmation": "CONFIRM"
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "deploymentId": "xyz-789-abc-123",
        "confirmation": "CONFIRM"
    },
    "response_200": {
        "status": "success",
        "message": "Deployment xyz-789-abc-123 terminated successfully",
        "timestamp": "2026-01-23T10:07:00.000000"
    },
    "response_400_wrong_confirm": {
        "status": "error",
        "message": "You must type 'CONFIRM' to terminate. This action cannot be undone."
    }
}

# ✅ 11. UPDATE ENDPOINT
REQUEST_UPDATE = {
    "curl": """
curl -X POST http://localhost:5000/api/update \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "deploymentId": "xyz-789-abc-123",
    "parameters": {
      "memorySize": 512,
      "timeout": 60,
      "trafficLevel": "medium"
    }
  }'
    """,
    "payload": {
        "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "deploymentId": "xyz-789-abc-123",
        "parameters": {
            "memorySize": 512,
            "timeout": 60,
            "trafficLevel": "medium"
        }
    },
    "response_200": {
        "status": "success",
        "message": "Deployment xyz-789-abc-123 updated",
        "timestamp": "2026-01-23T10:08:00.000000"
    }
}

# ✅ 12. LEX INTENTS CONFIG
REQUEST_LEX_INTENTS = {
    "curl": """
curl -X GET http://localhost:5000/api/lex-intents \\
  -H "Content-Type: application/json"
    """,
    "response_200": {
        "status": "success",
        "intents": {
            "GreetingIntent": {
                "description": "User greets the chatbot",
                "sample_utterances": ["hi", "hello", "hey", "good morning"],
                "slots": {}
            },
            "HelpIntent": {
                "description": "User asks what the bot can do",
                "sample_utterances": ["what can you do", "who are you", "help me"],
                "slots": {}
            },
            "DeployIntent": {
                "description": "User wants to deploy infrastructure",
                "sample_utterances": ["deploy a serverless api", "create lambda"],
                "slots": {
                    "templateType": {"type": "AMAZON.AlphaNumeric"},
                    "trafficLevel": {"type": "AMAZON.AlphaNumeric"}
                }
            }
        },
        "count": 8
    }
}

# ✅ COMMON ERROR RESPONSES
ERROR_RESPONSES = {
    "invalid_session": {
        "status_code": 401,
        "response": {
            "status": "error",
            "message": "Invalid session"
        }
    },
    "missing_required_field": {
        "status_code": 400,
        "response": {
            "status": "error",
            "message": "sessionId and message required"
        }
    },
    "deployment_not_found": {
        "status_code": 404,
        "response": {
            "status": "error",
            "message": "Deployment not found"
        }
    },
    "server_error": {
        "status_code": 500,
        "response": {
            "status": "error",
            "message": "Chat processing failed: ..."
        }
    }
}

print("✅ API Examples ready for testing")
print("✅ 12 request/response pairs documented")
print("✅ All error cases covered")

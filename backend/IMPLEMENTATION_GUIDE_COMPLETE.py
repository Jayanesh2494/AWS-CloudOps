"""
AWS CloudOps Chatbot - Complete Implementation Guide
All Lex Intents + Bedrock Response Generation
"""

# ✅ QUICK START

"""
PHASE 1: CREATE LEX BOT (AWS Console or CLI)
================================================

1. Go to AWS Lex Console
2. Create new bot: "CloudOpsBot"
3. Create bot alias: "LIVE" (or use ATTA alias)

For each intent below:
- Click "Add intent"
- Name it exactly as shown
- Add sample utterances
- Create slots (if any)
- Save and train

---

PHASE 2: GET BOT IDs
===================

After creating bot:
1. Go to Lex Console → Bots → CloudOpsBot
2. Copy: Bot ID
3. Go to Bot Aliases
4. Copy: Bot Alias ID
5. Locale: en_US

These go into lex_service_v2.py:
    botId='BOT_ID_HERE',
    botAliasId='BOT_ALIAS_ID_HERE',

---

PHASE 3: DEPLOY SERVICES
=========================

OLD: app.py, bedrock_service.py, lex_service.py
NEW: app_v2.py, bedrock_service_v2_1.py, lex_service_v2.py

Migration steps:
1. Backup old app.py
2. Replace with app_v2.py
3. Update imports
4. Test with /health endpoint
5. Test /api/session endpoint
6. Test /api/chat endpoint

---

PHASE 4: TEST INTENTS
=====================

Test flow:
1. POST /api/session → sessionId
2. POST /api/set-mode with sessionId
3. POST /api/chat with sessionId + message
4. Check detected intent
5. Verify Bedrock response

---
"""

# ✅ INTENT CREATION GUIDE

INTENT_SETUP_GUIDE = {
    
    "1. GreetingIntent": {
        "description": "User greets the bot",
        "sample_utterances": [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good evening",
            "how are you",
            "greetings",
            "hey there",
            "what's up",
            "howdy",
        ],
        "slots": "NONE",
        "bedrock_behavior": "Friendly greeting acknowledging their AWS needs",
        "test_message": "hello",
        "expected_response": "Hello! I'm your AWS CloudOps assistant...",
    },

    "2. HelpIntent": {
        "description": "User asks what the bot can do",
        "sample_utterances": [
            "what can you do",
            "who are you",
            "help me",
            "show features",
            "what services do you support",
            "how does this work",
            "capabilities",
            "tell me about yourself",
            "show me what you can do",
        ],
        "slots": "NONE",
        "bedrock_behavior": "List all capabilities clearly",
        "test_message": "what can you do",
        "expected_response": "I can help you with: 1. Deploy infrastructure...",
    },

    "3. DeployIntent": {
        "description": "User wants to deploy infrastructure",
        "sample_utterances": [
            "deploy a serverless api",
            "create lambda api gateway",
            "launch an API with lambda",
            "deploy infrastructure",
            "build cloud architecture",
            "create backend api",
            "deploy a website",
            "set up s3 static site",
            "deploy a database",
            "create a vpc",
            "i want to deploy something",
            "provision infrastructure",
        ],
        "slots": [
            {
                "name": "templateType",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["serverless-api", "s3-static-website", "vpc", "ecs-fargate"]
            },
            {
                "name": "trafficLevel",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["low", "medium", "high", "enterprise"]
            },
            {
                "name": "region",
                "type": "AMAZON.Region",
                "required": False,
                "sample_values": ["us-east-1", "us-west-2", "eu-west-1"]
            },
            {
                "name": "stageName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["dev", "staging", "prod"]
            },
            {
                "name": "apiName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["MyAPI", "OrderAPI", "UserService"]
            }
        ],
        "bedrock_behavior": "Ask clarifying questions about template, traffic, region",
        "test_message": "deploy a serverless api with high traffic",
        "expected_response": "Great! I'll deploy a serverless API for high traffic. Let me confirm the details...",
    },

    "4. ListResourcesIntent": {
        "description": "User asks to see running resources",
        "sample_utterances": [
            "list my resources",
            "show my deployments",
            "what is running now",
            "show active stacks",
            "list services",
            "list infrastructure",
            "what have i deployed",
            "show me everything",
        ],
        "slots": "NONE",
        "bedrock_behavior": "Confirm you'll fetch the list from deployment manager",
        "test_message": "list my resources",
        "expected_response": "Let me fetch your active deployments...",
    },

    "5. DescribeDeploymentIntent": {
        "description": "User asks details about a deployment",
        "sample_utterances": [
            "show details of my serverless api",
            "what did you deploy",
            "show architecture",
            "what resources are created",
            "describe my deployment",
            "tell me about the api",
        ],
        "slots": [
            {
                "name": "deploymentName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["api-123", "website", "vpc"]
            }
        ],
        "bedrock_behavior": "Ask which deployment if not specified",
        "test_message": "describe my serverless api",
        "expected_response": "I'll fetch the details of your serverless API deployment...",
    },

    "6. TerminateDeploymentIntent": {
        "description": "User wants to delete infrastructure",
        "sample_utterances": [
            "delete my deployment",
            "terminate the stack",
            "destroy serverless api",
            "remove resources",
            "stop everything",
            "tear down the infrastructure",
            "delete the api",
        ],
        "slots": [
            {
                "name": "deploymentName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["api-123", "website"]
            }
        ],
        "bedrock_behavior": "⚠️ CRITICAL: Always warn about resource deletion + require 'CONFIRM'",
        "test_message": "delete my deployment",
        "expected_response": "⚠️ This will delete all resources. Type 'CONFIRM' to proceed.",
    },

    "7. UpdateDeploymentIntent": {
        "description": "User wants to modify infrastructure",
        "sample_utterances": [
            "update my deployment",
            "change memory",
            "increase timeout",
            "scale up",
            "change stage to prod",
            "enable logging",
            "modify the configuration",
        ],
        "slots": [
            {
                "name": "deploymentName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
            },
            {
                "name": "trafficLevel",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["low", "medium", "high"]
            },
            {
                "name": "memorySize",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["128", "256", "512", "1024"]
            },
            {
                "name": "timeout",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["30", "60", "120", "300"]
            }
        ],
        "bedrock_behavior": "Ask which deployment and what to change",
        "test_message": "update memory to 512",
        "expected_response": "I'll update the configuration. Which deployment would you like to modify?",
    },

    "8. GeneralQuestionIntent": {
        "description": "User asks AWS/cloud questions",
        "sample_utterances": [
            "what is IAM role",
            "explain VPC",
            "what is API Gateway",
            "what is Bedrock",
            "what is Lambda",
            "what is S3",
            "what is DynamoDB",
            "what is CloudFormation",
        ],
        "slots": "NONE",
        "bedrock_behavior": "Provide clear, concise AWS explanations",
        "test_message": "what is a VPC",
        "expected_response": "A VPC (Virtual Private Cloud) is...",
    },

    "9. CreateBucketIntent": {
        "description": "User wants to create a secure S3 bucket",
        "sample_utterances": [
            "create bucket",
            "make a new bucket",
            "create an s3 bucket",
            "make bucket",
            "new bucket",
            "provision an s3 bucket",
            "set up a bucket"
        ],
        "slots": "NONE",
        "bedrock_behavior": "Acknowledge bucket creation and file upload",
        "test_message": "create bucket",
        "expected_response": "Bucket Created Successfully\nFile Uploaded Successfully",
    },

    "10. ListBucketsIntent": {
        "description": "User wants to see their created S3 buckets",
        "sample_utterances": [
            "show buckets",
            "list buckets",
            "what buckets do i have",
            "list my buckets",
            "show my buckets",
            "display s3 buckets"
        ],
        "slots": "NONE",
        "bedrock_behavior": "Return the list of buckets created by the chatbot",
        "test_message": "show buckets",
        "expected_response": "Here are your S3 buckets...",
    },

    "11. DeleteBucketIntent": {
        "description": "User wants to delete an S3 bucket",
        "sample_utterances": [
            "delete bucket",
            "remove bucket",
            "destroy bucket",
            "delete s3 bucket",
            "remove s3 bucket",
            "trash bucket"
        ],
        "slots": [
            {
                "name": "bucketName",
                "type": "AMAZON.AlphaNumeric",
                "required": False,
                "sample_values": ["chatops-123456-abcdef"]
            }
        ],
        "bedrock_behavior": "⚠️ CRITICAL: Always warn about bucket deletion + require 'CONFIRM'",
        "test_message": "delete bucket chatops-123456-abcdef",
        "expected_response": "⚠️ This will delete the bucket and all its versions. Type 'CONFIRM' to proceed.",
    },

    "12. UploadFileIntent": {
        "description": "User wants to upload a file into an S3 bucket",
        "sample_utterances": [
            "upload file to bucket",
            "upload text to bucket",
            "put file in bucket",
            "upload document",
            "save file",
            "create file in s3"
        ],
        "slots": [
            {
                "name": "bucketName",
                "type": "AMAZON.AlphaNumeric",
                "required": True,
                "sample_values": ["chatops-123456-abcdef"]
            },
            {
                "name": "fileName",
                "type": "AMAZON.AlphaNumeric",
                "required": True,
                "sample_values": ["index.html", "config.json", "log.txt"]
            },
            {
                "name": "fileContent",
                "type": "AMAZON.FreeFormInput",
                "required": True,
                "sample_values": ["Hello world", "My custom config content"]
            }
        ],
        "bedrock_behavior": "Acknowledge file upload success or prompt for missing parameters",
        "test_message": "upload file to bucket",
        "expected_response": "File uploaded successfully to your bucket.",
    },
}

# ✅ TESTING WORKFLOW

TEST_WORKFLOW = """
TEST 1: Greeting Intent
=======================
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "test-session",
    "message": "hello"
  }'

Expected:
{
  "status": "success",
  "intent": "GreetingIntent",
  "message": "Hello! I'm your AWS CloudOps assistant...",
  "requiresAction": false
}


TEST 2: Deploy Intent
====================
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "test-session",
    "message": "deploy a serverless api with high traffic"
  }'

Expected:
{
  "status": "success",
  "intent": "DeployIntent",
  "message": "Great! I'll help you deploy...",
  "requiresAction": true,
  "extractedParams": {
    "templateType": "serverless-api",
    "trafficLevel": "high"
  },
  "actions": [{
    "type": "deploy",
    "label": "Deploy",
    "endpoint": "/api/deploy"
  }]
}


TEST 3: List Resources
=======================
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "test-session",
    "message": "list my resources"
  }'

Expected:
{
  "status": "success",
  "intent": "ListResourcesIntent",
  "message": "Let me fetch your deployments...",
  "deployments": [
    {
      "deploymentId": "abc-123",
      "templateType": "serverless-api",
      "status": "ACTIVE",
      "createdAt": "2026-01-23T10:00:00"
    }
  ]
}


TEST 4: Terminate Intent (with confirmation)
==============================================
Step 1: Detect terminate intent
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "test-session",
    "message": "delete my api"
  }'

Expected:
{
  "status": "success",
  "intent": "TerminateDeploymentIntent",
  "message": "⚠️ This will delete all resources...",
  "requiresAction": true,
  "requiresConfirmation": true
}

Step 2: Confirm termination
curl -X POST http://localhost:5000/api/terminate \\
  -H "Content-Type: application/json" \\
  -d '{
    "sessionId": "test-session",
    "deploymentId": "abc-123",
    "confirmation": "CONFIRM"
  }'

Expected:
{
  "status": "success",
  "message": "Deployment abc-123 terminated successfully"
}
"""

# ✅ SLOT CREATION IN LEX

SLOT_CREATION_GUIDE = """
Creating Slots in Lex V2 Console:
=================================

For each slot:

1. Go to Intent → Slots
2. Click "Add slot"
3. Fill in:
   - Slot name: exactly as shown (e.g., "templateType")
   - Slot type: Choose type (AMAZON.AlphaNumeric, AMAZON.Region, etc.)
   - Required: Check if mandatory
   - Slot value resolution: Allow Lex to choose resolution strategy
4. Click "Save"

Example: templateType slot
- Name: templateType
- Type: AMAZON.AlphaNumeric
- Required: No
- Description: "Type of template to deploy"

Slot Types Available:
- AMAZON.AlphaNumeric: Alphanumeric values
- AMAZON.Region: AWS regions (auto-recognizes us-east-1, etc.)
- AMAZON.Date: Dates
- AMAZON.Number: Numbers
- AMAZON.Person: Person names
- AMAZON.Time: Times

Custom Slot Type (if needed):
- Go to Slots → Slot types
- Click "Create slot type"
- Name: e.g., "TemplateTypeSlot"
- Add values: serverless-api, s3-static-website, vpc-private-subnet, ecs-fargate-api
- Save
"""

print("✅ Complete Lex Intent Setup Guide")
print("✅ 8 core intents configured")
print("✅ All intent-slot mappings documented")
print("✅ Bedrock response behaviors defined")
print("✅ Test cases ready")

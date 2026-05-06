"""
CloudOps Chatbot - Flask REST API
Main application with 10 endpoints for chat, deployment management, and multi-account support
"""
import json
import boto3
import sys
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lex_service import get_intent
from bedrock_service import (
    generate_response, 
    extract_parameters, 
    select_template,
    generate_architecture_plan
)
from utils.deployment_manager import DeploymentManager
from utils.template_registry import TemplateRegistry
from utils.session_store import SessionStore
from utils.aws_session import validate_assume_role, create_session_with_role
from utils.s3_manager import S3Manager
from utils.logger import get_logger
from lex_intents_config import LEX_INTENTS, INTENT_CATEGORIES
from deploy.deploy_boto3 import deploy_template_user_account
from utils.github_deployer import deploy_static_website_from_github

logger = get_logger("app")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
deployment_manager = DeploymentManager()
template_registry = TemplateRegistry("../templates")
session_store = SessionStore()
s3_manager = S3Manager()

# Configuration
BOT_ID = os.getenv("LEX_BOT_ID", "CloudOpsBot")
BOT_ALIAS_ID = os.getenv("LEX_BOT_ALIAS_ID", "LIVE")
REGION = os.getenv("AWS_REGION", "us-east-1")


# ============================================================================
# ENDPOINT 1: Health Check
# ============================================================================
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "CloudOps Chatbot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0"
    }), 200


@app.route("/", methods=["GET"])
def root():
    """Serve the frontend HTML"""
    try:
        # Get absolute path to frontend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        frontend_path = os.path.join(project_root, "frontend", "index.html")
        
        with open(frontend_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return html_content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError as e:
        return jsonify({
            "message": "CloudOps Chatbot API v2.0",
            "error": f"Frontend not found: {str(e)}",
            "endpoints": {
                "health": "GET /health",
                "session": "POST /api/session",
                "mode": "POST /api/set-mode",
                "chat": "POST /api/chat",
                "deploy": "POST /api/deploy",
                "list": "POST /api/list-resources",
                "describe": "POST /api/describe-deployment",
                "update": "POST /api/update-deployment",
                "terminate": "POST /api/terminate-deployment",
                "intents_config": "GET /api/lex-intents"
            }
        }), 200


# ============================================================================
# ENDPOINT 2: Session Management
# ============================================================================
@app.route("/api/session", methods=["POST"])
def create_session():
    """
    Create new session or retrieve existing
    
    Request:
    {
        "user_id": "user123",
        "account_mode": "OUR"  # or "USER"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id", f"user_{datetime.now(timezone.utc).timestamp()}")
        account_mode = data.get("account_mode", "OUR")
        
        session_id = session_store.create_session(user_id, account_mode)
        
        return jsonify({
            "session_id": session_id,
            "user_id": user_id,
            "account_mode": account_mode,
            "created_at": datetime.now(timezone.utc).isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 3: Set Account Mode
# ============================================================================
@app.route("/api/set-mode", methods=["POST"])
def set_mode():
    """
    Set account mode for session (OUR or USER with role ARN)
    
    Request:
    {
        "session_id": "sess_abc123",
        "account_mode": "USER",
        "role_arn": "arn:aws:iam::123456789:role/CloudOpsRole",
        "external_id": "optional-external-id"
    }
    """
    try:
        data = request.get_json()
        role_arn = data.get("roleArn")
        external_id = data.get("externalId")
        region = data.get("region", "us-east-1")
        
        # Create a session for this validation
        session_id = session_store.create_session(f"validate_{datetime.now(timezone.utc).timestamp()}", "USER")
        
        session_data = session_store.get_session(session_id)
        
        # Validate role can be assumed
        if role_arn:
            validation = validate_assume_role(role_arn, external_id)
            if not validation.get("valid"):
                return jsonify({
                    "status": "error",
                    "message": f"Cannot assume role: {validation.get('error')}"
                }), 400
            
            # Store role for later use
            session_data["role_arn"] = role_arn
            session_data["external_id"] = external_id
            session_data["region"] = region
        
        session_data["account_mode"] = "USER"
        session_store.update_session(session_id, session_data)
        
        return jsonify({
            "status": "success",
            "message": "Role validated successfully",
            "assumedAccount": "USER"
        }), 200
        
    except Exception as e:
        logger.error(f"Set mode failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# INTENT HANDLERS
# ============================================================================

def handle_deploy_intent(message, slots, conversation_state, session_id, aws_session):
    """Handle deployment intent with parameter gathering and auto-deployment"""
    
    # Extract parameters from message and slots
    template_id = extract_template_from_message(message)
    size = extract_size_from_message(message, slots)
    
    # Update conversation state
    if template_id:
        conversation_state["selectedTemplate"] = template_id
    if size:
        conversation_state["size"] = size
    
    # Check if we have all required parameters
    template = conversation_state.get("selectedTemplate", "serverless-api")
    size = conversation_state.get("size")
    
    if template and size:
        # We have all parameters, deploy automatically
        conversation_state["readyToDeploy"] = True
        
        # Perform deployment
        deployment_result = perform_deployment(template, size, session_id, aws_session)
        
        # Reset conversation state for next deployment
        conversation_state["selectedTemplate"] = None
        conversation_state["size"] = None
        conversation_state["readyToDeploy"] = False
        
        return "deploy", deployment_result
    else:
        # Missing parameters, ask for them
        conversation_state["readyToDeploy"] = False
        return None, {"status": "gathering_params", "template": template, "size": size}


def handle_list_intent(session_id):
    """Handle list resources intent"""
    deployments = deployment_manager.list_deployments()
    session_deployments = [d for d in deployments if d.get("session_id") == session_id]
    
    return "list", {
        "deployments": session_deployments,
        "count": len(session_deployments)
    }


def handle_describe_intent(message, session_id):
    """Handle describe deployment intent"""
    # Extract deployment name/id from message
    deployment_name = extract_deployment_name(message)
    
    if deployment_name:
        deployment = deployment_manager.get_deployment_by_name(deployment_name, session_id)
        if deployment:
            return "describe", deployment
        else:
            return None, {"error": f"Deployment '{deployment_name}' not found"}
    else:
        return None, {"error": "Please specify which deployment to describe"}


def handle_terminate_intent(message, conversation_state, session_id, aws_session):
    """Handle terminate deployment intent"""
    deployment_name = extract_deployment_name(message)
    
    if deployment_name:
        if conversation_state.get("awaitingConfirmation"):
            # User is confirming termination
            if message.lower().strip() == "confirm":
                result = perform_termination(deployment_name, session_id, aws_session)
                conversation_state["awaitingConfirmation"] = False
                return "terminate", result
            else:
                conversation_state["awaitingConfirmation"] = False
                return None, {"cancelled": True}
        else:
            # Ask for confirmation
            conversation_state["awaitingConfirmation"] = True
            conversation_state["pendingAction"] = f"terminate_{deployment_name}"
            return None, {"awaiting_confirmation": True, "deployment": deployment_name}
    else:
        return None, {"error": "Please specify which deployment to terminate"}


def handle_update_intent(message, slots, conversation_state, session_id, aws_session):
    """Handle update deployment intent"""
    # Extract update parameters
    deployment_name = extract_deployment_name(message)
    new_size = extract_size_from_message(message, slots)
    
    if deployment_name and new_size:
        result = perform_update(deployment_name, new_size, session_id, aws_session)
        return "update", result
    else:
        return None, {"error": "Please specify deployment name and new size"}


def handle_create_bucket_intent(session_id, aws_session, conversation_state):
    """Handle create S3 bucket intent"""
    # Call S3Manager to create the bucket
    session_data = session_store.get_session(session_id)
    account_mode = session_data.get("accountMode", "OUR")
    
    success, bucket_name, error = s3_manager.create_bucket(aws_session, session_id)
    
    if success:
        # Upload placeholder file
        s3_manager.upload_placeholder_file(bucket_name, aws_session)
        conversation_state["targetBucket"] = bucket_name
        return "create_bucket", {
            "success": True,
            "bucket_name": bucket_name,
            "message": f"Bucket Created Successfully\\nFile Uploaded Successfully\\nBucket Name: {bucket_name}"
        }
    else:
        return None, {"error": error}


def handle_list_buckets_intent(session_id):
    """Handle list S3 buckets intent"""
    session_data = session_store.get_session(session_id)
    account_mode = session_data.get("accountMode", "OUR")
    account_id = None
    if account_mode == "USER":
        role_arn = session_data.get("roleArn")
        if role_arn:
            try:
                account_id = role_arn.split(":")[4]
            except IndexError:
                account_id = "unknown"
                
    buckets = s3_manager.list_buckets(account_mode, account_id)
    
    return "list_buckets", {
        "buckets": buckets,
        "count": len(buckets)
    }


def handle_delete_bucket_intent(message, conversation_state, session_id, aws_session):
    """Handle delete S3 bucket intent with CONFIRMATION state machine"""
    bucket_name = extract_bucket_name(message)
    
    if not bucket_name and "targetBucket" in conversation_state:
        bucket_name = conversation_state["targetBucket"]
        
    if conversation_state.get("awaitingDeleteBucketName") and not bucket_name:
        bucket_name = message.strip()
        conversation_state["awaitingDeleteBucketName"] = False
        conversation_state["targetBucket"] = bucket_name
        
    if bucket_name:
        conversation_state["targetBucket"] = bucket_name
        
    if not bucket_name:
        # We need the bucket name
        conversation_state["awaitingDeleteBucketName"] = True
        return None, {"status": "gathering_params", "missing": "deleteBucketName"}
        
    # Check if we were already waiting for confirmation
    if conversation_state.get("awaitingBucketDeleteConfirm"):
        if message.lower().strip() == "confirm":
            target_bucket = conversation_state.get("targetBucket")
            if target_bucket:
                session_data = session_store.get_session(session_id)
                account_mode = session_data.get("accountMode", "OUR")
                account_id = None
                if account_mode == "USER":
                    role_arn = session_data.get("roleArn")
                    if role_arn:
                        try:
                            account_id = role_arn.split(":")[4]
                        except IndexError:
                            account_id = "unknown"
                            
                success, error_or_msg = s3_manager.delete_bucket(target_bucket, aws_session, account_mode, account_id)
                
                conversation_state["awaitingBucketDeleteConfirm"] = False
                conversation_state["targetBucket"] = None
                
                if success:
                    return "delete_bucket", {"success": True, "message": error_or_msg}
                else:
                    return None, {"error": error_or_msg}
                    
        # Any other response cancels
        conversation_state["awaitingBucketDeleteConfirm"] = False
        conversation_state["targetBucket"] = None
        return None, {"cancelled": True, "message": "Deletion cancelled."}

    # Validate bucket exists and belongs to chatbot before asking
    session_data = session_store.get_session(session_id)
    account_mode = session_data.get("accountMode", "OUR")
    account_id = None
    if account_mode == "USER":
        role_arn = session_data.get("roleArn")
        if role_arn:
            try:
                account_id = role_arn.split(":")[4]
            except IndexError:
                account_id = "unknown"
                
    buckets = s3_manager.list_buckets(account_mode, account_id)
    bucket_exists = any(b.get("bucket_name") == bucket_name for b in buckets)
    
    if not bucket_exists:
        conversation_state["targetBucket"] = None
        return None, {"error": f"Bucket '{bucket_name}' not found or you don't have permission to delete it."}
        
    # Ask for confirmation
    conversation_state["awaitingBucketDeleteConfirm"] = True
    return None, {"awaiting_confirmation": True, "bucket_name": bucket_name}

def handle_upload_file_intent(message, slots, conversation_state, session_id, aws_session):
    """Handle upload file to S3 bucket intent"""
    bucket_name = None
    file_name = None
    file_content = None
    
    if slots:
        bucket_name = slots.get("bucketName") or slots.get("BucketName")
        file_name = slots.get("fileName") or slots.get("FileName")
        file_content = slots.get("fileContent") or slots.get("FileContent")
        
    if not bucket_name:
        bucket_name = extract_bucket_name(message)
        
    if not bucket_name and "targetBucket" in conversation_state:
        bucket_name = conversation_state["targetBucket"]
    if not file_name and "targetFileName" in conversation_state:
        file_name = conversation_state["targetFileName"]
    if not file_content and "targetFileContent" in conversation_state:
        file_content = conversation_state["targetFileContent"]
        
    # Standard string capture fallback if we are actively prompting
    if conversation_state.get("awaitingBucketName") and not bucket_name:
        bucket_name = message.strip()
        conversation_state["awaitingBucketName"] = False
        
    elif conversation_state.get("awaitingFileName") and not file_name:
        file_name = message.strip()
        conversation_state["awaitingFileName"] = False
        
    elif conversation_state.get("awaitingFileContent") and not file_content:
        file_content = message.strip()
        conversation_state["awaitingFileContent"] = False

    # Store current knowns
    if bucket_name: conversation_state["targetBucket"] = bucket_name
    if file_name: conversation_state["targetFileName"] = file_name
    if file_content: conversation_state["targetFileContent"] = file_content
        
    # Check what is missing and prompt
    if not bucket_name:
        conversation_state["awaitingBucketName"] = True
        return None, {"status": "gathering_params", "missing": "bucketName"}
        
    if not file_name:
        conversation_state["awaitingFileName"] = True
        return None, {"status": "gathering_params", "missing": "fileName"}
        
    if not file_content:
        conversation_state["awaitingFileContent"] = True
        return None, {"status": "gathering_params", "missing": "fileContent"}
        
    # If we have everything, upload it!
    content_type = conversation_state.get("targetFileMime", "text/plain")
    is_base64 = conversation_state.get("isFileUploadBase64", False)
    
    success, msg = s3_manager.upload_file_to_bucket(
        bucket_name, file_name, file_content, aws_session,
        content_type=content_type, is_base64=is_base64
    )
    
    # Clear upload state
    conversation_state["targetBucket"] = None
    conversation_state["targetFileName"] = None
    conversation_state["targetFileContent"] = None
    conversation_state["targetFileMime"] = None
    conversation_state["isFileUploadBase64"] = False
    
    if success:
        return "upload_file", {"success": True, "message": msg}
    else:
        return None, {"error": msg}

def invoke_ec2_lambda(intent, message, slots, session_id, aws_session):
    """
    Invoke the ChatOpsEC2Manager lambda function manually as fallback
    if Lex didn't fulfill the request automatically.
    """
    try:
        lambda_client = aws_session.client('lambda', region_name='us-east-1') # Default or current region
        
        # Build an event structure resembling Lex V2 for the Lambda
        payload = {
            "sessionState": {
                "intent": {
                    "name": intent,
                    "slots": {}
                }
            },
            "inputTranscript": message,
            "sessionId": session_id,
            "invocationSource": "FulfillmentCodeHook"
        }
        
        # Add slots (mock Lex format)
        if slots:
            for k, v in slots.items():
                if v:
                    payload["sessionState"]["intent"]["slots"][k] = {"value": {"interpretedValue": v}}
        
        response = lambda_client.invoke(
            FunctionName='ChatOpsEC2Manager',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        # Extract messages from Lex lambda response
        messages = response_payload.get("messages", [])
        bot_reply = ""
        if messages:
            bot_reply = "\n\n".join([m.get("content", "") for m in messages if m.get("contentType") == "PlainText"])
        
        return "ec2_action", {"success": True, "reply": bot_reply}
    
    except Exception as e:
        logger.error(f"Failed to invoke ChatOpsEC2Manager: {e}")
        return "ec2_action", {"success": False, "error": str(e)}

def handle_deploy_static_website_intent(message, conversation_state, session_id, aws_session):
    """Handle static website deployment intent with multi-turn parameter gathering"""
    message_lower = message.lower().strip()
    
    # Check if we have the website type
    if not conversation_state.get("websiteType"):
        if conversation_state.get("awaitingWebsiteType"):
            if "static" in message_lower:
                conversation_state["websiteType"] = "static"
                conversation_state["awaitingWebsiteType"] = False
            elif "dynamic" in message_lower:
                conversation_state["websiteType"] = "dynamic"
                conversation_state["awaitingWebsiteType"] = False
                return None, {"error": "Currently, I can only host static websites. Please ask me to host a static website again when you're ready."}
            else:
                return None, {"status": "gathering_params", "missing": "websiteType"}
        else:
            conversation_state["awaitingWebsiteType"] = True
            return None, {"status": "gathering_params", "missing": "websiteType"}
            
    # Check if we have the GitHub URL
    if not conversation_state.get("githubUrl"):
        if conversation_state.get("awaitingGithubUrl"):
            if message_lower.startswith("http") or message_lower.startswith("github.com"):
                url = message.strip()
                if not url.startswith("http"):
                    url = "https://" + url
                conversation_state["githubUrl"] = url
                conversation_state["awaitingGithubUrl"] = False
            else:
                return None, {"status": "gathering_params", "missing": "githubUrl", "invalid": True}
        else:
            conversation_state["awaitingGithubUrl"] = True
            return None, {"status": "gathering_params", "missing": "githubUrl"}
            
    # Check if we are waiting for confirmation
    if not conversation_state.get("awaitingDeployWebsiteConfirm"):
        conversation_state["awaitingDeployWebsiteConfirm"] = True
        return "deploy_website", {"awaiting_confirmation": True, "githubUrl": conversation_state["githubUrl"]}
        
    # Process confirmation
    if message_lower == "confirm" or "yes" in message_lower:
        success, msg, url = deploy_static_website_from_github(
            conversation_state["githubUrl"], aws_session, session_id
        )
        
        # Clear state
        conversation_state["websiteType"] = None
        conversation_state["githubUrl"] = None
        conversation_state["awaitingDeployWebsiteConfirm"] = False
        
        if success:
            return "deploy_website", {"success": True, "message": msg, "website_url": url}
        else:
            return "deploy_website", {"success": False, "error": msg}
            
    # Any other answer cancels
    conversation_state["websiteType"] = None
    conversation_state["githubUrl"] = None
    conversation_state["awaitingDeployWebsiteConfirm"] = False
    return None, {"cancelled": True, "message": "Deployment cancelled."}


# ============================================================================
# PARAMETER EXTRACTION HELPERS
# ============================================================================

def extract_template_from_message(message):
    """Extract template type from message"""
    message_lower = message.lower()
    
    # If the user is specifically messing with a bucket, don't trigger the s3-static-website template
    if "bucket" in message_lower:
        return None
        
    if "serverless" in message_lower or "api" in message_lower:
        return "serverless-api"
    elif "static" in message_lower or "website" in message_lower or "s3" in message_lower:
        return "s3-static-website"
    elif "fargate" in message_lower or "ecs" in message_lower:
        return "ecs-fargate-api"
    elif "vpc" in message_lower:
        return "vpc-private-subnet"
    
    return None  # Let the conversation prompt the user instead of defaulting to serverless-api


def extract_size_from_message(message, slots=None):
    """Extract size from message"""
    message_lower = message.lower()
    
    # Check slots first
    if slots and slots.get("trafficLevel"):
        traffic = slots["trafficLevel"].lower()
        if "low" in traffic or "micro" in traffic or "small" in traffic:
            return "micro"
        elif "medium" in traffic or "normal" in traffic:
            return "medium"
        elif "high" in traffic or "large" in traffic or "enterprise" in traffic:
            return "large"
    
    # Check message content
    if "micro" in message_lower or "small" in message_lower or "low traffic" in message_lower:
        return "micro"
    elif "medium" in message_lower or "normal" in message_lower:
        return "medium"
    elif "large" in message_lower or "high traffic" in message_lower or "enterprise" in message_lower:
        return "large"
    
    return None


def extract_deployment_name(message):
    """Extract deployment name from message"""
    # Simple extraction - look for quoted names or specific patterns
    import re
    match = re.search(r'["\']([^"\']+)["\']', message)
    if match:
        return match.group(1)
    
    # Look for common patterns
    words = message.lower().split()
    for i, word in enumerate(words):
        if word in ["deployment", "stack", "api"] and i < len(words) - 1:
            return words[i+1]
    
    return None

def extract_bucket_name(message):
    """Extract bucket name from message"""
    import re
    # Look for the characteristic generated chatops name
    match = re.search(r'(chatops-\d+-[a-f0-9]+)', message)
    if match:
        return match.group(1)
        
    match = re.search(r'["\']([^"\']+)["\']', message)
    if match:
        return match.group(1)
        
    words = message.lower().split()
    for i, word in enumerate(words):
        if word in ["bucket"] and i < len(words) - 1:
            return words[i+1]
            
    return None

# ============================================================================
# ACTION PERFORMERS
# ============================================================================

def perform_deployment(template_id, size, session_id, aws_session):
    """Perform actual deployment"""
    try:
        # Get template info
        template = template_registry.get_template(template_id)
        if not template:
            return {"error": f"Template {template_id} not found"}
        
        # Map size to parameters
        size_params = {
            "micro": {"memory": 128, "timeout": 10},
            "medium": {"memory": 512, "timeout": 30},
            "large": {"memory": 1024, "timeout": 60}
        }
        
        params = size_params.get(size, size_params["medium"])
        params["apiName"] = f"CloudOpsAPI-{session_id[:8]}"
        params["stageName"] = "dev"
        
        # Get session data for account mode
        session_data = session_store.get_session(session_id)
        account_mode = session_data.get("accountMode", "OUR")
        
        # Determine role ARN for deployment
        role_arn = None
        if account_mode == "USER":
            role_arn = session_data.get("roleArn")
        
        # Get account ID
        account_id = None
        if account_mode == "USER" and role_arn:
            # Extract account ID from role ARN: arn:aws:iam::123456789012:role/RoleName
            try:
                account_id = role_arn.split(":")[4]
            except IndexError:
                account_id = "unknown"
        elif account_mode == "OUR":
            # For OUR mode, use a placeholder or get from session
            account_id = "our-account"
        
        # Create deployment record
        deployment_id = deployment_manager.create_deployment(
            template_id=template_id,
            deployment_name=f"{template_id}-{size}-{session_id[:8]}",
            params=params,
            account_mode=account_mode,
            region="us-east-1",
            session_id=session_id,
            account_id=account_id
        )
        
        # Validate role ARN for USER mode
        if account_mode == "USER" and not role_arn:
            return {"error": "Role ARN required for USER account deployments"}
        
        # Perform actual deployment
        template_path = os.path.join(template.get("path"), "cdk.out", "ServerlessApiStack.template.json")
        
        success, api_url, error = deploy_template_user_account(
            template_path=template_path,
            params=params,
            role_arn=role_arn,
            session=aws_session
        )
        
        if success:
            # Mark as deployed with real API URL
            deployment_manager.mark_deployed(deployment_id, api_url=api_url)
            return {
                "success": True,
                "deployment_id": deployment_id,
                "api_url": api_url,
                "template": template_id,
                "size": size
            }
        else:
            # Mark as failed
            deployment_manager.update_deployment(deployment_id, {
                "status": "FAILED",
                "error": error
            })
            return {"error": f"Deployment failed: {error}"}
            
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return {"error": str(e)}


def perform_termination(deployment_name, session_id, aws_session):
    """Perform deployment termination"""
    try:
        # Find deployment
        deployments = deployment_manager.list_deployments()
        deployment = None
        for d in deployments:
            if d.get("deployment_name") == deployment_name and d.get("session_id") == session_id:
                deployment = d
                break
        
        if not deployment:
            return {"error": f"Deployment '{deployment_name}' not found"}
        
        # For now, just mark as terminated (actual CloudFormation deletion would go here)
        deployment_manager.mark_terminated(deployment["deployment_id"])
        
        return {
            "success": True,
            "deployment_id": deployment["deployment_id"],
            "status": "terminated"
        }
        
    except Exception as e:
        logger.error(f"Termination failed: {str(e)}")
        return {"error": str(e)}


def perform_update(deployment_name, new_size, session_id, aws_session):
    """Perform deployment update"""
    try:
        # Find deployment
        deployments = deployment_manager.list_deployments()
        deployment = None
        for d in deployments:
            if d.get("deployment_name") == deployment_name and d.get("session_id") == session_id:
                deployment = d
                break
        
        if not deployment:
            return {"error": f"Deployment '{deployment_name}' not found"}
        
        # Update parameters
        size_params = {
            "micro": {"memory": 128, "timeout": 10},
            "medium": {"memory": 512, "timeout": 30},
            "large": {"memory": 1024, "timeout": 60}
        }
        
        new_params = size_params.get(new_size, size_params["medium"])
        
        # Update deployment record
        deployment_manager.update_deployment(deployment["deployment_id"], {
            "parameters": new_params,
            "size": new_size,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "deployment_id": deployment["deployment_id"],
            "new_size": new_size,
            "parameters": new_params
        }
        
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        return {"error": str(e)}


def format_action_response(intent, action_taken, action_result, conversation_state):
    """Format backend action results into strings without using Bedrock"""
    if not action_taken and not action_result:
        return ""
        
    if action_result and action_result.get("error"):
        return f"❌ {action_result.get('error')}"
        
    if action_result and action_result.get("awaiting_confirmation"):
        if action_taken == "deploy_website":
            return f"Ready to deploy the static website from {action_result.get('githubUrl')}. Type 'confirm' to proceed."
        return f"🛑 Are you sure you want to delete the bucket '{action_result.get('bucket_name')}'? Type 'confirm' to proceed."
        
    if action_result and action_result.get("cancelled"):
        return f"ℹ️ {action_result.get('message', 'Action cancelled.')}"
        
    if not action_taken and action_result:
        # Parameter gathering
        if action_result.get("status") == "gathering_params":
            if action_result.get("missing") == "websiteType":
                return "Static or dynamic?"
            if action_result.get("missing") == "githubUrl":
                if action_result.get("invalid"):
                    return "That doesn't look like a valid link. Please provide the public GitHub repository link (e.g. https://github.com/user/repo)."
                return "Provide the public GitHub repository link"
            if action_result.get("missing") == "deleteBucketName":
                return "Which S3 bucket would you like to delete?"
            if action_result.get("missing") == "bucketName":
                return "What is the name of the S3 bucket you would like to upload a file to?"
            if action_result.get("missing") == "fileName":
                return "What would you like to name the file? (e.g. hello.txt)"
            if action_result.get("missing") == "fileContent":
                return "What text content would you like to write inside the file?"
                
            if action_result.get("template") and not action_result.get("size"):
                return "Please specify the traffic level for your deployment (e.g., small, medium, large)."
            if action_result.get("size") and not action_result.get("template"):
                return "What type of infrastructure would you like to deploy?"
        if action_result.get("status") == "ready_to_deploy":
            return f"Ready to deploy a {action_result.get('size')} {action_result.get('template')}. Please type 'confirm' to proceed."
        if action_result.get("status") == "deployed":
            return f"Deployment initiated successfully."
            
        return ""
        
    result = action_result or {}
    reply = ""
    
    if action_taken == "deploy":
        if result.get("success"):
            reply = f"✅ Deployment completed successfully!\nTemplate: {result.get('template')}\nDeployment ID: {result.get('deployment_id')}"
            if result.get("api_url"):
                reply += f"\nAPI URL: {result.get('api_url')}"
        else:
            reply = f"❌ Deployment failed: {result.get('error')}"
            
    elif action_taken == "list":
        count = result.get("count", 0)
        reply = f"ℹ️ Found {count} deployments."
        for d in result.get("deployments", []):
            reply += f"\n- {d.get('name')} ({d.get('status')})"
            
    elif action_taken == "describe":
        if result.get("error"):
            reply = f"❌ Failed to describe deployment: {result.get('error')}"
        else:
            reply = f"ℹ️ Deployment '{result.get('deployment_name')}' details:\nStatus: {result.get('status')}\nSize: {result.get('size')}"
            
    elif action_taken == "terminate":
        if result.get("success"):
            reply = f"✅ Successfully terminated deployment."
        else:
            reply = f"❌ Failed to terminate deployment: {result.get('error')}"
            
    elif action_taken == "update":
        if result.get("success"):
            reply = f"✅ Successfully updated deployment to size {result.get('new_size')}."
        else:
            reply = f"❌ Failed to update deployment: {result.get('error')}"
            
    elif action_taken == "create_bucket":
        if result.get("success"):
            reply = f"✅ Successfully created S3 bucket: {result.get('bucket_name')}"
        else:
            reply = f"❌ Failed to create S3 bucket: {result.get('error', 'Unknown error')}"
            
    elif action_taken == "list_buckets":
        buckets = result.get("buckets", [])
        reply = f"ℹ️ Found {len(buckets)} S3 buckets created by this chatbot."
        for b in buckets:
            reply += f"\n- {b.get('bucket_name')}"
            
    elif action_taken == "upload_file":
        if result.get("success"):
            reply = f"✅ Successfully uploaded the requested file to the S3 bucket."
        else:
            reply = f"❌ Failed to upload file to S3 bucket: {result.get('error')}"
            
    elif action_taken == "delete_bucket":
        if result.get("success"):
            reply = f"✅ Successfully deleted the S3 bucket and all its contents."
        else:
            reply = f"❌ Failed to delete S3 bucket: {result.get('error')}"
            
    elif action_taken == "deploy_website":
        if result.get("success"):
            reply = f"✅ Deployment completed successfully!\n\n**Website URL:** [{result.get('website_url')}]({result.get('website_url')})\n\n{result.get('message')}"
        else:
            reply = f"❌ Deployment failed: {result.get('error')}"

    return reply


# ============================================================================
# ENDPOINT 4: Chat - Main Conversational AI
# ============================================================================
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint with full conversational flow
    
    Request:
    {
        "session_id": "sess_abc123",
        "message": "deploy a serverless api with low traffic",
        "accountMode": "OUR"
    }
    
    Response:
    {
        "session_id": "sess_abc123",
        "botReply": "I'll deploy a serverless API for low traffic...",
        "intent": "DeployIntent",
        "action_taken": "deploy",
        "deployment_result": {...}
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        message = data.get("message")
        account_mode = data.get("accountMode", "OUR").upper()
        file_upload = data.get("file_upload")
        
        # Create session if not provided or doesn't exist
        if not session_id or not session_store.get_session(session_id):
            session_id = session_store.create_session(session_id)
            session_data = session_store.get_session(session_id)
            session_data["accountMode"] = account_mode
            session_store.update_session(session_id, session_data)
        
        if not message:
            return jsonify({"error": "message required"}), 400
        
        # Get session data and conversation state
        session_data = session_store.get_session(session_id)
        if not session_data:
            return jsonify({"error": "session not found"}), 404
            
        conversation_state = session_data.get("conversationState", {})
        
        # Inject file upload data into conversation state
        if file_upload:
            conversation_state["targetFileName"] = file_upload.get("name")
            conversation_state["targetFileContent"] = file_upload.get("data")
            conversation_state["targetFileMime"] = file_upload.get("mime", "application/octet-stream")
            conversation_state["isFileUploadBase64"] = True
        
        # Get AWS session for this user
        aws_session = None
        if session_data.get("accountMode") == "USER":
            role_arn = session_data.get("roleArn")
            external_id = session_data.get("externalId")
            if role_arn:
                aws_session = create_session_with_role(role_arn, external_id)
                
        # Fallback to local boto3 credentials if no explicitly assumed role session
        if aws_session is None:
            aws_session = boto3.Session()
        
        # Step 1: Detect intent using Lex V2
        intent_result = get_intent(
            message=message,
            session_id=session_id,
            use_fallback=True,
            session=aws_session,
            conversation_state=conversation_state
        )
        
        intent = intent_result.get("intent", "GeneralQuestionIntent")
        confidence = intent_result.get("confidence", 0.0)
        slots = intent_result.get("slots", {})
        
        # Hard override for S3 operations if Lex is misclassifying them as DeployIntent
        message_lower = message.lower().strip()
        is_bucket_intent = False
        
        if file_upload:
            intent = "UploadFileIntent"
            is_bucket_intent = True
        elif "bucket" in message_lower or "s3" in message_lower:
            if "create" in message_lower or "make" in message_lower or "new" in message_lower:
                intent = "CreateBucketIntent"
                is_bucket_intent = True
            elif "list" in message_lower or "show" in message_lower:
                intent = "ListBucketsIntent"
                is_bucket_intent = True
            elif "upload" in message_lower or "put" in message_lower:
                intent = "UploadFileIntent"
                is_bucket_intent = True
            elif "delete" in message_lower or "remove" in message_lower:
                intent = "DeleteBucketIntent"
                is_bucket_intent = True
                
        # If we forcibly matched a bucket intent, clear any ongoing deployment state
        if is_bucket_intent:
            conversation_state["selectedTemplate"] = None
            conversation_state["size"] = None
            conversation_state["readyToDeploy"] = False
            
        # Step 2: Process conversation based on intent and current state
        action_taken = None
        action_result = None
        response_context = {
            "intent": intent,
            "slots": slots,
            "conversation_state": conversation_state,
            "account_mode": session_data.get("accountMode", "OUR"),
            "session_id": session_id
        }
        
        logger.error(f"===== DEEP TRACE: intent is {intent} before if/else block =====")
        logger.error(f"===== DEEP TRACE: is_bucket_intent was {is_bucket_intent} =====")
        
        # Handle different intents
        if intent == "DeployIntent":
            logger.error("===== DEEP TRACE: Entered DeployIntent block =====")
            action_taken, action_result = handle_deploy_intent(
                message, slots, conversation_state, session_id, aws_session
            )
        elif intent == "ListResourcesIntent":
            action_taken, action_result = handle_list_intent(session_id)
        elif intent == "DescribeDeploymentIntent":
            action_taken, action_result = handle_describe_intent(message, session_id)
        elif intent == "TerminateDeploymentIntent":
            action_taken, action_result = handle_terminate_intent(
                message, conversation_state, session_id, aws_session
            )
        elif intent == "UpdateDeploymentIntent":
            action_taken, action_result = handle_update_intent(
                message, slots, conversation_state, session_id, aws_session
            )
        elif intent == "CreateBucketIntent":
            action_taken, action_result = handle_create_bucket_intent(
                session_id, aws_session, conversation_state
            )
        elif intent == "ListBucketsIntent":
            action_taken, action_result = handle_list_buckets_intent(session_id)
        elif intent == "DeleteBucketIntent":
            action_taken, action_result = handle_delete_bucket_intent(
                message, conversation_state, session_id, aws_session
            )
        elif intent == "UploadFileIntent":
            action_taken, action_result = handle_upload_file_intent(
                message, slots, conversation_state, session_id, aws_session
            )
        elif intent == "DeployStaticWebsiteIntent":
            action_taken, action_result = handle_deploy_static_website_intent(
                message, conversation_state, session_id, aws_session
            )
        elif intent in ["CreateInstanceIntent", "ListInstancesIntent", "DescribeInstanceIntent", "StopInstanceIntent", "TerminateInstanceIntent"]:
            # If Lex hasn't fulfilled it, let's manually invoke the Lambda
            if not intent_result.get("lex_messages"):
                logger.info(f"EC2 Intent detected without Lex messages. Invoking Lambda natively for {intent}.")
                action_taken, action_result = invoke_ec2_lambda(intent, message, slots, session_id, aws_session)
                
                # If lambda succeeded, put its text into lex_messages so it gets displayed
                if action_result and action_result.get("success") and action_result.get("reply"):
                    intent_result["lex_messages"] = [action_result["reply"]]
            else:
                # Lex fulfilled it
                action_taken = "ec2_action"
                action_result = {"success": True, "reply": "Fulfilled by Lex."}
        
        # Update response context with action results
        response_context["action_taken"] = action_taken
        response_context["action_result"] = action_result
        
        # Step 3: Generate response bypassing Bedrock
        bot_reply = ""
        lex_messages = intent_result.get("lex_messages", [])
        
        # 1. Use Lex's pre-configured message if available
        if lex_messages:
            bot_reply = "\n\n".join(lex_messages)
            
        # 2. Append actual execution results of backend actions
        action_addition = format_action_response(intent, action_taken, action_result, conversation_state)
        
        if action_addition:
            if bot_reply:
                bot_reply += "\n\n" + action_addition
            else:
                bot_reply = action_addition
                
        # 3. Final Fallback if empty
        if not bot_reply:
            if intent == "GreetingIntent":
                bot_reply = "Hello! I am your CloudOps Assistant. How can I help you today?"
            elif intent == "HelpIntent":
                bot_reply = "I can help you create S3 buckets, deploy serverless APIs, or manage your AWS infrastructure. Try asking me to list your buckets."
            elif intent == "CreateBucketIntent":
                bot_reply = "I am creating your S3 bucket now."
            else:
                bot_reply = "I received your request, but I don't have a specific response configured."
        
        # Step 4: Update conversation state
        conversation_state["lastIntent"] = intent
        conversation_state["lastMessage"] = message
        session_store.update_conversation_state(session_id, conversation_state)
        
        logger.info(f"Chat: intent={intent}, confidence={confidence}, action={action_taken}")
        
        return jsonify({
            "session_id": session_id,
            "botReply": bot_reply,
            "intent": intent,
            "confidence": confidence,
            "slots": slots,
            "action_taken": action_taken,
            "action_result": action_result,
            "conversation_state": conversation_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 5: Deploy
# ============================================================================
@app.route("/api/deploy", methods=["POST"])
def deploy():
    """
    Deploy infrastructure with selected template
    
    Request:
    {
        "session_id": "sess_abc123",
        "template_id": "serverless-api",
        "parameters": {
            "apiName": "my-api",
            "trafficLevel": "medium",
            "region": "us-east-1"
        },
        "deploymentName": "my-deployment"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        template_id = data.get("template_id")
        parameters = data.get("parameters", {})
        deployment_name = data.get("deploymentName", f"deploy-{datetime.now(timezone.utc).timestamp()}")
        
        if not session_id or not template_id:
            return jsonify({"error": "session_id and template_id required"}), 400
        
        session_data = session_store.get_session(session_id)
        if not session_data:
            return jsonify({"error": "session not found"}), 404
        
        # Get AWS session
        aws_session = None
        if session_data.get("accountMode") == "USER":
            role_arn = session_data.get("role_arn")
            external_id = session_data.get("external_id")
            if role_arn:
                aws_session = create_session_with_role(role_arn, external_id)
        
        # Validate template
        template = template_registry.get_template(template_id)
        if not template:
            return jsonify({"error": f"template {template_id} not found"}), 404
        
        # Validate parameters
        validation = template_registry.validate_params(template_id, parameters)
        if not validation.get("valid"):
            return jsonify({
                "error": "Parameter validation failed",
                "details": validation.get("errors")
            }), 400
        
        # Create deployment record
        deployment_id = deployment_manager.create_deployment(
            template_id=template_id,
            deployment_name=deployment_name,
            parameters=parameters,
            account_mode=session_data.get("accountMode", "OUR"),
            region=parameters.get("region", "us-east-1")
        )
        
        logger.info(f"Deployment created: {deployment_id}")
        
        # Actually deploy using CloudFormation
        template_path = os.path.join(template.get("path"), "cdk.out", "ServerlessApiStack.template.json")
        
        # For USER mode, we need a role ARN to deploy in their account
        role_arn = None
        if session_data.get("accountMode") == "USER":
            role_arn = session_data.get("role_arn")
            if not role_arn:
                return jsonify({"error": "Role ARN required for USER account deployments"}), 400
        
        success, api_url, error = deploy_template_user_account(
            template_path=template_path,
            params=parameters,
            role_arn=role_arn,
            session=aws_session
        )
        
        if success:
            # Mark as deployed with real API URL
            deployment_manager.mark_deployed(deployment_id, api_url=api_url)
            logger.info(f"✅ Deployment {deployment_id} completed successfully")
            
            return jsonify({
                "deployment_id": deployment_id,
                "template_id": template_id,
                "status": "ACTIVE",
                "deployment_name": deployment_name,
                "api_url": api_url,
                "created_at": datetime.now(timezone.utc).isoformat()
            }), 201
        else:
            # Mark as failed
            deployment_manager.update_deployment(deployment_id, {
                "status": "FAILED",
                "error": error
            })
            logger.error(f"❌ Deployment {deployment_id} failed: {error}")
            
            return jsonify({
                "error": f"Deployment failed: {error}",
                "deployment_id": deployment_id
            }), 500
        
    except Exception as e:
        logger.error(f"Deploy failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 6: List Resources
# ============================================================================
@app.route("/api/list-resources", methods=["POST"])
def list_resources():
    """
    List all deployments for account
    
    Request:
    {
        "session_id": "sess_abc123",
        "filter_status": "ACTIVE"  # Optional
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        filter_status = data.get("filter_status")
        
        if not session_id:
            return jsonify({"error": "session_id required"}), 400
        
        session_data = session_store.get_session(session_id)
        if not session_data:
            return jsonify({"error": "session not found"}), 404
        
        # Get deployments
        deployments = deployment_manager.list_deployments(
            account_mode=session_data.get("accountMode", "OUR"),
            status=filter_status
        )
        
        return jsonify({
            "session_id": session_id,
            "account_mode": session_data.get("accountMode", "OUR"),
            "count": len(deployments),
            "deployments": deployments,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"List resources failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 7: Describe Deployment
# ============================================================================
@app.route("/api/describe-deployment", methods=["POST"])
def describe_deployment():
    """
    Get details of specific deployment
    
    Request:
    {
        "session_id": "sess_abc123",
        "deployment_id": "deploy_xyz"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        deployment_id = data.get("deployment_id")
        
        if not session_id or not deployment_id:
            return jsonify({"error": "session_id and deployment_id required"}), 400
        
        deployment = deployment_manager.get_deployment(deployment_id)
        if not deployment:
            return jsonify({"error": "deployment not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "deployment": deployment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Describe deployment failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 8: Terminate Deployment
# ============================================================================
@app.route("/api/terminate-deployment", methods=["POST"])
def terminate_deployment():
    """
    Terminate a deployment (REQUIRES confirmation)
    
    Request:
    {
        "session_id": "sess_abc123",
        "deployment_id": "deploy_xyz",
        "confirmed": true
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        deployment_id = data.get("deployment_id")
        confirmed = data.get("confirmed", False)
        
        if not session_id or not deployment_id:
            return jsonify({"error": "session_id and deployment_id required"}), 400
        
        if not confirmed:
            return jsonify({
                "error": "Termination requires confirmation",
                "message": "Set confirmed=true to terminate",
                "deployment_id": deployment_id
            }), 400
        
        deployment = deployment_manager.get_deployment(deployment_id)
        if not deployment:
            return jsonify({"error": "deployment not found"}), 404
        
        # TODO: Call CDK/CloudFormation to destroy
        
        # Mark as terminated
        deployment_manager.mark_terminated(deployment_id)
        
        logger.info(f"Deployment terminated: {deployment_id}")
        
        return jsonify({
            "deployment_id": deployment_id,
            "status": "TERMINATED",
            "terminated_at": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Terminate deployment failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 9: Update Deployment
# ============================================================================
@app.route("/api/update-deployment", methods=["POST"])
def update_deployment_endpoint():
    """
    Update deployment parameters (e.g., memory, traffic level)
    
    Request:
    {
        "session_id": "sess_abc123",
        "deployment_id": "deploy_xyz",
        "parameters": {
            "trafficLevel": "high",
            "memorySize": 1024
        }
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        deployment_id = data.get("deployment_id")
        parameters = data.get("parameters", {})
        
        if not session_id or not deployment_id:
            return jsonify({"error": "session_id and deployment_id required"}), 400
        
        deployment = deployment_manager.get_deployment(deployment_id)
        if not deployment:
            return jsonify({"error": "deployment not found"}), 404
        
        # Merge parameters
        updated_params = {**deployment.get("parameters", {}), **parameters}
        
        # Update in database
        deployment_manager.update_deployment(deployment_id, {
            "parameters": updated_params,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # TODO: Call CDK/CloudFormation to update
        
        logger.info(f"Deployment updated: {deployment_id}")
        
        return jsonify({
            "deployment_id": deployment_id,
            "status": "UPDATED",
            "parameters": updated_params,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Update deployment failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ENDPOINT 10: Lex Intents Configuration
# ============================================================================
@app.route("/api/lex-intents", methods=["GET"])
def get_lex_intents():
    """
    Get all Lex intents configuration
    
    Returns list of 8 intents with utterances and slots
    """
    try:
        return jsonify({
            "intents": LEX_INTENTS,
            "intent_count": len(LEX_INTENTS),
            "categories": INTENT_CATEGORIES,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get intents config failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Error Handlers
# ============================================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "internal server error"}), 500


# ============================================================================
# Startup
# ============================================================================
if __name__ == "__main__":
    logger.info("Starting CloudOps Chatbot Flask API...")
    logger.info(f"LEX_BOT_ID: {BOT_ID}")
    logger.info(f"LEX_BOT_ALIAS_ID: {BOT_ALIAS_ID}")
    logger.info(f"REGION: {REGION}")
    
    # Run Flask in development mode
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)


"""
Enhanced Bedrock Service - Primary chatbot brain
Generates natural responses, extracts parameters, selects templates
"""
import boto3
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger("bedrock_service")


def generate_response(message: str, intent: str, context: dict = None, session=None) -> str:
    """
    Generate natural language response using Bedrock
    
    Args:
        message: User message
        intent: Intent detected by Lex
        context: Additional context (templates, deployments, etc.)
        session: boto3 session
    
    Returns:
        str: Natural response from Claude
    """
    if session is None:
        session = boto3.Session()

    context_str = ""
    if context:
        context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"

    # Build a more specific prompt based on action results
    action_info = ""
    if context and context.get("action_taken"):
        action = context["action_taken"]
        result = context.get("action_result", {})
        
        if action == "deploy":
            if result.get("success"):
                action_info = f"\n\nIMPORTANT: A deployment was just completed successfully! Deployment ID: {result.get('deployment_id')}, Template: {result.get('template')}, API URL: {result.get('api_url')}"
            else:
                action_info = f"\n\nIMPORTANT: A deployment attempt failed with error: {result.get('error')}"
        elif action == "list":
            count = result.get("count", 0)
            action_info = f"\n\nIMPORTANT: Listed {count} deployments for the user."
        elif action == "describe":
            if result.get("error"):
                action_info = f"\n\nIMPORTANT: Failed to describe deployment: {result.get('error')}"
            else:
                action_info = f"\n\nIMPORTANT: Provided details for deployment '{result.get('deployment_name')}'."
        elif action == "terminate":
            if result.get("success"):
                action_info = f"\n\nIMPORTANT: Successfully terminated deployment {result.get('deployment_id')}."
            else:
                action_info = f"\n\nIMPORTANT: Failed to terminate deployment: {result.get('error')}"
        elif action == "update":
            if result.get("success"):
                action_info = f"\n\nIMPORTANT: Successfully updated deployment {result.get('deployment_id')} to size {result.get('new_size')}."
            else:
                action_info = f"\n\nIMPORTANT: Failed to update deployment: {result.get('error')}"
        elif action == "create_bucket":
            if result.get("success"):
                action_info = f"\n\nIMPORTANT: Successfully created S3 bucket: {result.get('bucket_name')} and uploaded a welcome file."
            else:
                action_info = f"\n\nIMPORTANT: Failed to create S3 bucket: {result.get('error')}"
        elif action == "list_buckets":
            buckets = result.get("buckets", [])
            action_info = f"\n\nIMPORTANT: Found {len(buckets)} S3 buckets created by this chatbot."
        elif action == "upload_file":
            if result.get("success"):
                action_info = "\n\nIMPORTANT: Successfully uploaded the requested file to the S3 bucket."
            else:
                action_info = f"\n\nIMPORTANT: Failed to upload file to S3 bucket: {result.get('error')}"
        elif action == "delete_bucket":
            if result.get("success"):
                action_info = "\n\nIMPORTANT: Successfully deleted the S3 bucket and all its contents."
            else:
                action_info = f"\n\nIMPORTANT: Failed to delete S3 bucket: {result.get('error')}"
    
    # Handle parameter gathering case
    if context and not context.get("action_taken") and context.get("action_result"):
        result = context.get("action_result", {})
        if result.get("status") == "gathering_params":
            template = result.get("template", "serverless-api")
            size = result.get("size")
            
            if template and not size:
                template_names = {
                    "serverless-api": "Serverless API",
                    "s3-static-website": "S3 Static Website", 
                    "ecs-fargate-api": "ECS Fargate API",
                    "vpc-private-subnet": "VPC with Private Subnet"
                }
                template_display = template_names.get(template, template)
                action_info = f"\n\nIMPORTANT: User wants to deploy a {template_display} but hasn't specified the size. Ask them for traffic level (micro/small/low, medium/normal, large/high/enterprise)."
            elif size and not template:
                action_info = f"\n\nIMPORTANT: User specified size '{size}' but no template. Ask them what type of infrastructure to deploy."

    prompt = f"""You are an AWS CloudOps assistant. You help users deploy, manage, and monitor AWS infrastructure.

User message: "{message}"
Detected intent: {intent}
{context_str}
{action_info}

Respond naturally and helpfully. Be concise and professional. If an action was just completed, acknowledge it specifically in your response."""

    try:
        bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')

        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 500,
            "temperature": 0.7,
            "top_p": 0.9,
        })

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-v2',
            body=body
        )

        result = json.loads(response['body'].read())
        reply = result.get('completion', '').strip()
        logger.info(f"Bedrock generated response for intent {intent}")
        return reply

    except Exception as e:
        logger.error(f"Bedrock call failed: {str(e)}")
        # Fallback responses based on context
        if context and context.get("action_taken") == "deploy":
            result = context.get("action_result", {})
            if result.get("success"):
                return f"✅ Deployment completed successfully! Your API is available at: {result.get('api_url', 'N/A')}"
            elif result.get("error"):
                return f"❌ Deployment failed: {result.get('error')}. Please try again or contact support."
            else:
                return "Deployment initiated. Please wait while I set up your infrastructure..."
        
        # Handle parameter gathering in fallback
        if context and not context.get("action_taken") and context.get("action_result"):
            result = context.get("action_result", {})
            if result.get("status") == "gathering_params":
                template = result.get("template", "serverless-api")
                size = result.get("size")
                
                if template and not size:
                    template_names = {
                        "serverless-api": "Serverless API",
                        "s3-static-website": "S3 Static Website", 
                        "ecs-fargate-api": "ECS Fargate API",
                        "vpc-private-subnet": "VPC with Private Subnet"
                    }
                    template_display = template_names.get(template, template)
                    return f"Great! I can deploy a {template_display} for you. What traffic level are you expecting? Choose from: micro/small (low traffic), medium/normal, or large/high/enterprise."
                elif size and not template:
                    return f"I see you want to deploy with {size} traffic. What type of infrastructure would you like? I support serverless APIs, S3 static websites, ECS Fargate APIs, and VPC setups."
        
        # Default fallback responses
        fallback_responses = {
            "GreetingIntent": "Hello! I'm your AWS CloudOps assistant. How can I help you deploy or manage your infrastructure?",
            "HelpIntent": "I can help you deploy serverless APIs, manage AWS resources, and operate your cloud infrastructure across your AWS account or a customer account using role assumption.",
            "DeployIntent": "I'd be happy to help you deploy! What template would you like to use? I support serverless APIs, S3 static websites, and more.",
            "ListResourcesIntent": "Let me fetch your running deployments and resources for you.",
            "TerminateIntent": "To terminate a deployment, I need to confirm this important action. This will delete all associated AWS resources.",
            "UnknownIntent": "I'm not sure what you mean. You can ask me to deploy infrastructure, list resources, or manage deployments.",
        }
        return fallback_responses.get(intent, "How can I help you with your cloud infrastructure?")


def extract_parameters(message: str, template_id: str = None, session=None) -> dict:
    """
    Extract deployment parameters from user message using Bedrock
    
    Args:
        message: User message
        template_id: Template being deployed (optional)
        session: boto3 session
    
    Returns:
        dict: Extracted parameters
    """
    if session is None:
        session = boto3.Session()

    template_info = f"Template: {template_id}" if template_id else ""

    prompt = f"""Extract deployment parameters from this user message:

Message: "{message}"
{template_info}

Return ONLY a JSON object with extracted parameters. Include:
- memory (if applicable, in MB)
- timeout (in seconds)
- region (AWS region)
- stage (deployment stage like dev, prod)
- name (service name)
- traffic_level (low, medium, high)
- description

Return empty object if no parameters found. Return valid JSON only."""

    try:
        bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')

        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 200,
            "temperature": 0.0,  # Lower temp for structured output
            "top_p": 0.9,
        })

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-v2',
            body=body
        )

        result = json.loads(response['body'].read())
        response_text = result.get('completion', '{}').strip()
        
        # Try to extract JSON
        try:
            params = json.loads(response_text)
            logger.info(f"Extracted parameters: {params}")
            return params
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse extracted parameters: {response_text}")
            return {}

    except Exception as e:
        logger.error(f"Parameter extraction failed: {str(e)}")
        return {}


def select_template(message: str, available_templates: list, intent: str, session=None) -> dict:
    """
    Use Bedrock to select best template for user request
    
    Args:
        message: User message
        available_templates: List of available templates
        intent: Detected intent
        session: boto3 session
    
    Returns:
        dict: {"template_id": str, "reasoning": str, "confidence": float}
    """
    if session is None:
        session = boto3.Session()

    templates_str = json.dumps([
        {
            "id": t.get("template_id"),
            "name": t.get("name"),
            "description": t.get("description"),
            "use_cases": t.get("use_cases", [])
        }
        for t in available_templates
    ], indent=2)

    prompt = f"""Based on the user message and intent, select the best AWS template to deploy.

User message: "{message}"
Intent: {intent}

Available templates:
{templates_str}

Return a JSON response with:
- template_id: the selected template ID
- reasoning: brief explanation (1 sentence)
- confidence: 0.0-1.0

Return valid JSON only."""

    try:
        bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')

        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 150,
            "temperature": 0.3,
            "top_p": 0.9,
        })

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-v2',
            body=body
        )

        result = json.loads(response['body'].read())
        response_text = result.get('completion', '{}').strip()
        
        try:
            selection = json.loads(response_text)
            logger.info(f"Template selected: {selection.get('template_id')}")
            return selection
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse template selection: {response_text}")
            # Default to first template
            return {
                "template_id": available_templates[0].get("template_id") if available_templates else None,
                "reasoning": "Default template selection",
                "confidence": 0.5
            }

    except Exception as e:
        logger.error(f"Template selection failed: {str(e)}")
        return {
            "template_id": available_templates[0].get("template_id") if available_templates else None,
            "error": str(e)
        }


def generate_architecture_plan(user_message: str, template_id: str, 
                              params: dict, session=None) -> str:
    """
    Generate architecture explanation using Bedrock
    
    Args:
        user_message: Original user request
        template_id: Selected template
        params: Extracted parameters
        session: boto3 session
    
    Returns:
        str: Architecture explanation
    """
    if session is None:
        session = boto3.Session()

    params_str = json.dumps(params, indent=2)

    prompt = f"""Create a brief architecture plan for this AWS deployment:

User request: "{user_message}"
Template: {template_id}
Parameters: {params_str}

Explain:
1. What will be deployed
2. AWS services involved
3. How it will be used
4. Cost considerations

Keep it under 150 words."""

    try:
        bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')

        body = json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 300,
            "temperature": 0.7,
            "top_p": 0.9,
        })

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-v2',
            body=body
        )

        result = json.loads(response['body'].read())
        plan = result.get('completion', '').strip()
        logger.info("Architecture plan generated")
        return plan

    except Exception as e:
        logger.error(f"Architecture generation failed: {str(e)}")
        return f"Deploying {template_id} with parameters: {params_str}"

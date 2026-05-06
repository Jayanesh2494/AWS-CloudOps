import boto3
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import get_logger
from utils.aws_helpers import check_cdk_bootstrap, get_bootstrap_instructions, get_account_id, detect_bootstrap_error

logger = get_logger("deploy_boto3")


def deploy_lex_bot_in_user_account(role_arn: str):
    """
    Deploy Lex bot automatically in user account

    Args:
        role_arn: ARN of role to assume in user account

    Returns:
        tuple: (success: bool, bot_name: str, error: str)
    """
    try:
        # Create session by assuming role
        sts_client = boto3.client('sts')
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='CloudOpsChatbotLexDeploy',
            ExternalId='cloudops-chatbot-2024'
        )

        credentials = response['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

        # Load Lex bot template
        template_path = os.path.join('templates', 'lex-bot.json')
        if not os.path.exists(template_path):
            return False, None, f"Lex bot template not found: {template_path}"

        with open(template_path, 'r') as f:
            template_body = f.read()

        # Create CloudFormation client
        cf_client = session.client('cloudformation', region_name='us-east-1')

        stack_name = "cloudops-chatbot-lex-bot"

        logger.info(f"Deploying Lex bot stack: {stack_name} in user account")

        # Create stack
        cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
        )

        # Wait for stack creation to complete
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})

        logger.info("✅ Lex bot deployed successfully in user account")
        return True, "CloudOpsChatbot", None

    except Exception as e:
        error_msg = f"Lex bot deployment failed: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def deploy_template_user_account(template_path: str, params: dict, role_arn: str = None, session=None, region: str = 'ap-south-1'):
    """
    Deploy CloudFormation template using provided credentials or assumed role

    Args:
        template_path: Path to CloudFormation template JSON file
        params: CloudFormation parameters dict
        role_arn: ARN of role to assume (optional, for USER account mode)
        session: boto3.Session (optional, if already created)
        region: AWS region for deployment (default: ap-south-1)

    Returns:
        tuple: (success: bool, api_url: str, error: str)
    """
    try:
        if session is None:
            if role_arn:
                # Create session by assuming role (USER mode)
                sts_client = boto3.client('sts')
                response = sts_client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName='CloudOpsChatbotDeploy',
                    ExternalId='cloudops-chatbot-2024'
                )

                credentials = response['Credentials']
                session = boto3.Session(
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            else:
                # Use current credentials (OUR mode)
                session = boto3.Session()

        # Check CDK bootstrap before deployment
        logger.info(f"Checking CDK bootstrap in region: {region}")
        if not check_cdk_bootstrap(region, session):
            account_id = get_account_id(session)
            instructions = get_bootstrap_instructions(region, account_id or 'YOUR_ACCOUNT_ID')
            return False, None, instructions

        # Create CloudFormation client with user account session
        cf_client = session.client('cloudformation', region_name=region)

        # Load template
        if not os.path.exists(template_path):
            return False, None, f"Template not found: {template_path}"

        with open(template_path, 'r') as f:
            template_body = f.read()

        # Parse template to check available parameters
        try:
            template_json = json.loads(template_body)
            valid_params = template_json.get("Parameters", {}).keys()
        except json.JSONDecodeError:
            valid_params = []
            logger.warning("Failed to parse template JSON to validate parameters")

        # Convert params dict to CloudFormation format, filtering to only valid parameters
        cf_params = []
        for key, value in params.items():
            if key in valid_params:
                cf_params.append({
                    'ParameterKey': key,
                    'ParameterValue': str(value)
                })
            else:
                logger.debug(f"Skipping parameter '{key}' not defined in template")

        stack_name = f"cloudops-{os.path.basename(template_path).replace('.template.json', '').lower()}-{hash(str(params)) % 10000}"

        logger.info(f"Deploying stack: {stack_name} in user account")

        # Create/update stack
        try:
            cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=cf_params,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        except cf_client.exceptions.AlreadyExistsException:
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=cf_params,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )

        # Wait for stack creation/update to complete
        waiter = cf_client.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
        except:
            # Try update waiter
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})

        # Get stack outputs
        stack_info = cf_client.describe_stacks(StackName=stack_name)
        outputs = stack_info['Stacks'][0].get('Outputs', [])

        # Extract API URL from outputs
        api_url = None
        for output in outputs:
            if output['OutputKey'] == 'ApiUrl':
                api_url = output['OutputValue']
                break

        if not api_url:
            api_url = f"https://{stack_name}.execute-api.{region}.amazonaws.com/prod"

        logger.info(f"✅ Deployment successful! API URL: {api_url}")
        return True, api_url, None

    except Exception as e:
        error_msg = f"Deployment failed: {str(e)}"
        logger.error(error_msg)
        
        # Check if it's a bootstrap error and provide helpful message
        if detect_bootstrap_error(error_msg):
            account_id = get_account_id(session)
            instructions = get_bootstrap_instructions(region, account_id or 'YOUR_ACCOUNT_ID')
            return False, None, instructions
        
        return False, None, error_msg

import boto3
import sys
import os
from typing import Dict, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger("aws_session")

def create_aws_session(account_mode: str, role_arn: str = None, external_id: str = None):
    """
    Create boto3 session based on account mode

    Args:
        account_mode: "our" or "user"
        role_arn: Required when account_mode is "user"
        external_id: Optional external ID for role assumption

    Returns:
        boto3.Session: Configured session for the target account
    """
    if account_mode == "our":
        # Use default credentials (our account)
        logger.info("Creating session for OUR AWS account")
        return boto3.Session()

    elif account_mode == "user":
        if not role_arn:
            raise ValueError("roleArn required for user account mode")

        logger.info(f"Creating session for USER AWS account using role: {role_arn}")

        # Assume role into user account
        sts_client = boto3.client('sts')

        assume_role_params = {
            'RoleArn': role_arn,
            'RoleSessionName': 'cloudops-chatbot-session'
        }

        # Add ExternalId if provided
        if external_id:
            assume_role_params['ExternalId'] = external_id

        response = sts_client.assume_role(**assume_role_params)

        credentials = response['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

        logger.info("✅ Successfully assumed role into user account")
        return session

    else:
        raise ValueError(f"Invalid account_mode: {account_mode}")


def validate_assume_role(role_arn: str, external_id: str = None) -> Dict:
    """
    Validate that a role can be assumed
    
    Args:
        role_arn: Role ARN to validate
        external_id: Optional external ID
    
    Returns:
        {"valid": True/False, "error": error_message}
    """
    try:
        sts_client = boto3.client('sts')
        
        assume_role_params = {
            'RoleArn': role_arn,
            'RoleSessionName': 'cloudops-validate-role'
        }
        
        if external_id:
            assume_role_params['ExternalId'] = external_id
        
        response = sts_client.assume_role(**assume_role_params)
        logger.info(f"✅ Role validation successful: {role_arn}")
        return {"valid": True, "error": None}
        
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Role validation failed: {error_msg}")
        return {"valid": False, "error": error_msg}


def create_session_with_role(role_arn: str, external_id: str = None):
    """
    Create boto3 session by assuming a role
    
    Args:
        role_arn: Role ARN to assume
        external_id: Optional external ID
    
    Returns:
        boto3.Session: Session with assumed role credentials
    """
    try:
        sts_client = boto3.client('sts')
        
        assume_role_params = {
            'RoleArn': role_arn,
            'RoleSessionName': 'cloudops-chatbot-session'
        }
        
        if external_id:
            assume_role_params['ExternalId'] = external_id
        
        response = sts_client.assume_role(**assume_role_params)
        credentials = response['Credentials']
        
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        logger.info(f"✅ Created session with assumed role: {role_arn}")
        return session
        
    except Exception as e:
        logger.error(f"Failed to create session with role: {str(e)}")
        return None
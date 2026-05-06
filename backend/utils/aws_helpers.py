"""
AWS Helper Functions
Utilities for AWS operations including CDK bootstrap detection
"""
import boto3
import sys
import os
from typing import Dict, Optional, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger("aws_helpers")


def get_account_id(session=None) -> Optional[str]:
    """
    Get AWS account ID from session
    
    Args:
        session: boto3 session (uses default if None)
    
    Returns:
        str: AWS account ID or None if failed
    """
    try:
        if session is None:
            session = boto3.Session()
        
        sts_client = session.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        logger.info(f"Retrieved account ID: {account_id}")
        return account_id
    except Exception as e:
        logger.error(f"Failed to get account ID: {str(e)}")
        return None


def check_cdk_bootstrap(region: str, session=None) -> bool:
    """
    Check if CDK is bootstrapped in the given region
    
    CDK bootstrap creates SSM parameter: /cdk-bootstrap/hnb659fds/version
    
    Args:
        region: AWS region to check
        session: boto3 session (uses default if None)
    
    Returns:
        bool: True if bootstrapped, False otherwise
    """
    try:
        if session is None:
            session = boto3.Session()
        
        ssm_client = session.client('ssm', region_name=region)
        
        # Try to get the CDK bootstrap version parameter
        parameter_name = '/cdk-bootstrap/hnb659fds/version'
        response = ssm_client.get_parameter(Name=parameter_name)
        
        version = response['Parameter']['Value']
        logger.info(f"✅ CDK is bootstrapped in {region} (version: {version})")
        return True
        
    except ssm_client.exceptions.ParameterNotFound:
        logger.warning(f"❌ CDK is NOT bootstrapped in {region}")
        return False
    except Exception as e:
        logger.error(f"Failed to check CDK bootstrap: {str(e)}")
        # Return False on error to be safe
        return False


def get_bootstrap_instructions(region: str, account_id: str) -> str:
    """
    Get formatted instructions for bootstrapping CDK
    
    Args:
        region: AWS region that needs bootstrapping
        account_id: AWS account ID
    
    Returns:
        str: Formatted instructions with exact command
    """
    instructions = f"""
⚠️ **CDK Bootstrap Required**

Your AWS account needs to be bootstrapped for CDK deployments in the **{region}** region.

**What is CDK Bootstrap?**
CDK bootstrap sets up the necessary AWS resources (S3 bucket, IAM roles, etc.) that CDK needs to deploy your infrastructure.

**How to fix this:**

1. Open your terminal
2. Run this command:

```
cdk bootstrap aws://{account_id}/{region}
```

3. Wait for it to complete (takes 1-2 minutes)
4. Try your deployment again

**Need help?**
- Make sure you have AWS CDK installed: `npm install -g aws-cdk`
- Make sure your AWS credentials are configured
- The bootstrap only needs to be done once per region per account

Would you like me to explain more about CDK bootstrap?
"""
    return instructions.strip()


def detect_bootstrap_error(error_message: str) -> bool:
    """
    Detect if an error is related to CDK bootstrap
    
    Args:
        error_message: Error message from deployment
    
    Returns:
        bool: True if it's a bootstrap error
    """
    bootstrap_indicators = [
        "/cdk-bootstrap/hnb659fds/version",
        "parameter store",
        "bootstrap",
        "CDKToolkit"
    ]
    
    error_lower = error_message.lower()
    return any(indicator.lower() in error_lower for indicator in bootstrap_indicators)


def parse_region_from_message(message: str) -> Optional[str]:
    """
    Extract AWS region from user message
    
    Args:
        message: User message
    
    Returns:
        str: AWS region code or None if not found
    """
    import re
    
    # Common AWS regions
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
        'sa-east-1', 'ca-central-1', 'me-south-1', 'af-south-1'
    ]
    
    message_lower = message.lower()
    
    # Check for explicit region mentions
    for region in regions:
        if region in message_lower:
            logger.info(f"Extracted region from message: {region}")
            return region
    
    # Check for patterns like "in region X" or "region: X"
    pattern = r'region[:\s]+([a-z]{2}-[a-z]+-\d)'
    match = re.search(pattern, message_lower)
    if match:
        region = match.group(1)
        if region in regions:
            logger.info(f"Extracted region from pattern: {region}")
            return region
    
    logger.debug("No region found in message")
    return None


def validate_region(region: str) -> bool:
    """
    Validate if a string is a valid AWS region
    
    Args:
        region: Region string to validate
    
    Returns:
        bool: True if valid AWS region
    """
    valid_regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1',
        'sa-east-1', 'ca-central-1', 'me-south-1', 'af-south-1'
    ]
    
    return region in valid_regions


def get_region_from_user_or_default(message: str, default_region: str = 'ap-south-1') -> str:
    """
    Get region from user message or return default
    
    Priority:
    1. Region mentioned in message
    2. Default region parameter
    3. Fallback to ap-south-1
    
    Args:
        message: User message
        default_region: Default region to use
    
    Returns:
        str: AWS region code
    """
    # Try to extract from message
    region = parse_region_from_message(message)
    if region:
        return region
    
    # Use default
    if validate_region(default_region):
        logger.info(f"Using default region: {default_region}")
        return default_region
    
    # Final fallback
    logger.warning(f"Invalid default region {default_region}, using ap-south-1")
    return 'ap-south-1'

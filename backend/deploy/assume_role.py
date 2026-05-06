import boto3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import get_logger

logger = get_logger("assume_role")


def assume_role(role_arn: str, session_name="CloudOpsChatbotSession", region="us-east-1"):
    """
    Used for USER ACCOUNT deployment.
    We'll fully use it in Phase 8.
    """
    sts = boto3.client("sts", region_name=region)

    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name
    )

    creds = response["Credentials"]

    logger.info("AssumeRole success. Temporary credentials created.")

    return {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }

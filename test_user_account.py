import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import boto3
from utils.logger import get_logger
from utils.aws_session import create_aws_session

logger = get_logger("test_assume_role")

def test_assume_role(role_arn: str):
    """
    Test AssumeRole into user account
    """
    try:
        logger.info(f"Testing AssumeRole with ARN: {role_arn}")

        # Create session using our factory
        session = create_aws_session("user", role_arn)

        # Test by listing CloudFormation stacks in user account
        cf_client = session.client('cloudformation', region_name='us-east-1')
        stacks = cf_client.describe_stacks()

        logger.info(f"✅ AssumeRole SUCCESS! Found {len(stacks['Stacks'])} stacks in user account")

        # Test Lex access
        try:
            lex_client = session.client('lex-runtime', region_name='us-east-1')
            # Just test if we can call describe_bot (this will fail if no bot exists, but tests access)
            lex_client.describe_bot(botName='CloudOpsChatbot')
            logger.info("✅ Lex access confirmed")
        except lex_client.exceptions.NotFoundException:
            logger.info("✅ Lex access confirmed (bot not found, but access works)")
        except Exception as e:
            logger.warning(f"⚠️ Lex access test failed: {str(e)}")

        # Test Bedrock access
        try:
            bedrock_client = session.client('bedrock', region_name='us-east-1')
            models = bedrock_client.list_foundation_models()
            logger.info(f"✅ Bedrock access confirmed. Found {len(models['modelSummaries'])} models")
        except Exception as e:
            logger.warning(f"⚠️ Bedrock access test failed: {str(e)}")

        return True, session

    except Exception as e:
        logger.error(f"❌ AssumeRole FAILED: {str(e)}")
        return False, None

def test_full_chat_flow(role_arn: str):
    """
    Test the full chat flow with user account
    """
    from backend.lex_service import detect_intent_from_message
    from backend.bedrock_service import extract_parameters_with_bedrock

    try:
        session = create_aws_session("user", role_arn)

        # Test message
        message = "deploy serverless api"

        # Test Lex
        lex_result = detect_intent_from_message(message, session)
        logger.info(f"Lex result: {lex_result}")

        # Test Bedrock
        bedrock_params = extract_parameters_with_bedrock(message, session)
        logger.info(f"Bedrock params: {bedrock_params}")

        return True

    except Exception as e:
        logger.error(f"❌ Full chat flow test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Replace with your actual role ARN
    # For testing, if you have admin user, create a role first
    role_arn = "arn:aws:iam::553015941729:role/CloudOpsChatbotRole"  # Update this with your role ARN!

    print("🧪 Testing AssumeRole functionality...")
    print(f"Using Role ARN: {role_arn}")
    print("Note: Make sure this role exists and trusts your account!")

    success, session = test_assume_role(role_arn)

    if success:
        print("🎉 AssumeRole test passed!")
        print("\n🧪 Testing full chat flow...")
        chat_success = test_full_chat_flow(role_arn)
        if chat_success:
            print("🎉 Full chat flow test passed!")
        else:
            print("💥 Full chat flow test failed!")
    else:
        print("💥 AssumeRole test failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the role ARN is correct")
        print("2. Make sure the role exists in the target account")
        print("3. Make sure the role trusts your account (add to trust policy)")
        print("4. Make sure you have sts:AssumeRole permission")
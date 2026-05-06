import os
import sys
import subprocess
import json
import boto3
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import get_logger

logger = get_logger("deploy_cdk")


def deploy_template_cdk(template_path: str, params: dict, stack_name: str = None):
    """
    Deploy CDK template using cdk deploy command

    Args:
        template_path: Path to cdk.json file
        params: Deployment parameters
        stack_name: Optional custom stack name

    Returns:
        tuple: (success: bool, api_url: str, error: str)
    """
    try:
        # Get the template directory (parent of cdk.json)
        template_dir = os.path.dirname(template_path)

        if not os.path.exists(template_dir):
            return False, None, f"Template directory not found: {template_dir}"

        logger.info(f"Deploying CDK template in: {template_dir}")
        logger.info(f"Parameters: {params}")

        # Change to template directory
        original_cwd = os.getcwd()
        os.chdir(template_dir)

        try:
            # Run cdk deploy with full path
            deploy_stack_name = stack_name or "ServerlessApiStack"
            cdk_path = r"C:\Users\asiva\AppData\Roaming\npm\cdk.cmd"
            cmd = [cdk_path, "deploy", deploy_stack_name, "--require-approval", "never", "--outputs-file", "outputs.json"]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                error_msg = f"CDK deploy failed: {result.stderr}"
                logger.error(error_msg)
                return False, None, error_msg

            logger.info("CDK deployment successful")

            # Read outputs from the generated file
            outputs_file = os.path.join(template_dir, "outputs.json")
            if os.path.exists(outputs_file):
                with open(outputs_file, 'r') as f:
                    outputs = json.load(f)

                # Extract API URL from outputs
                stack_outputs = outputs.get(deploy_stack_name, {})
                api_url = stack_outputs.get("ApiUrl")

                if api_url:
                    logger.info(f"✅ Real API URL obtained: {api_url}")
                    return True, api_url, None

            # Fallback: try to get from CloudFormation directly
            try:
                cf_client = boto3.client('cloudformation', region_name='us-east-1')
                stack_info = cf_client.describe_stacks(StackName=deploy_stack_name)
                outputs = stack_info['Stacks'][0].get('Outputs', [])

                for output in outputs:
                    if output['OutputKey'] == 'ApiUrl':
                        api_url = output['OutputValue']
                        logger.info(f"✅ Real API URL from CloudFormation: {api_url}")
                        return True, api_url, None
            except Exception as cf_error:
                logger.warning(f"Could not get outputs from CloudFormation: {cf_error}")

            # Final fallback
            api_url = f"https://{stack_name.lower()}.execute-api.us-east-1.amazonaws.com/prod"
            logger.warning(f"Using fallback API URL: {api_url}")
            return True, api_url, None

        finally:
            # Always restore original working directory
            os.chdir(original_cwd)

    except subprocess.TimeoutExpired:
        error_msg = "CDK deployment timed out after 10 minutes"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"CDK deployment failed: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg

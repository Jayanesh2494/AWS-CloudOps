import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from utils.template_registry import template_registry

logger = get_logger("policy_generator")

class PolicyGenerator:
    """Enhanced policy generator with different policy types"""

    def __init__(self):
        self.base_policies = {
            "minimal": [
                "lex:PostText",
                "lex:PostContent",
                "lex:GetSession",
                "lex:PutSession",
                "lex:DeleteSession",
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "deploy": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:GetTemplate",
                "iam:PassRole"
            ],
            "manage": [
                "cloudformation:DeleteStack",
                "cloudformation:ListStackResources",
                "cloudformation:DescribeStackResources",
                "lambda:GetFunction",
                "lambda:ListFunctions",
                "apigateway:GET",
                "apigateway:POST",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ]
        }

    def generate_policy(self, template_name: str, policy_type: str = "deploy", account_id: str = None):
        """
        Generate IAM policy for template operations

        Args:
            template_name: Name of the template
            policy_type: Type of policy (minimal, deploy, manage)
            account_id: AWS account ID for resource ARN scoping (optional)

        Returns:
            Policy document dict or None if template not found
        """
        try:
            template = template_registry.get_template(template_name)
            if not template:
                logger.error(f"Template {template_name} not found")
                return None

            # Get template-specific actions
            template_actions = template.get("policyActions", [])

            # Combine base policy actions with template actions
            all_actions = set()

            # Always include minimal actions
            all_actions.update(self.base_policies["minimal"])

            # Add policy type specific actions
            if policy_type in self.base_policies:
                all_actions.update(self.base_policies[policy_type])

            # Add template specific actions
            all_actions.update(template_actions)

            # Create policy document
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": sorted(list(all_actions)),
                        "Resource": "*"
                    }
                ]
            }

            logger.info(f"Generated {policy_type} policy for template {template_name} with {len(all_actions)} actions")
            return policy_document

        except Exception as e:
            logger.error(f"Policy generation failed: {e}")
            return None

    def get_minimal_policy(self):
        """Generate minimal policy for Lex + Bedrock access only"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": self.base_policies["minimal"],
                    "Resource": "*"
                }
            ]
        }

    def generate_deploy_policy(self, template_name: str, account_id: str = None):
        """Generate policy for deployment operations"""
        return self.generate_policy(template_name, "deploy", account_id)

    def generate_manage_policy(self, template_name: str, account_id: str = None):
        """Generate policy for management operations (list, update, delete)"""
        return self.generate_policy(template_name, "manage", account_id)

    def get_policy_types(self):
        """Get available policy types"""
        return list(self.base_policies.keys())

    def format_policy_json(self, policy_dict: dict) -> str:
        """Format policy dictionary as pretty JSON string"""
        return json.dumps(policy_dict, indent=2, ensure_ascii=False)
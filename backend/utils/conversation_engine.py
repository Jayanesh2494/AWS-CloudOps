import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from bedrock_service import extract_parameters_with_bedrock

logger = get_logger("conversation_engine")


class ConversationEngine:
    """Intelligent conversation engine that asks follow-up questions to gather deployment specs"""

    def __init__(self):
        self.required_params = {
            "serverless-api": {
                "lambdaMemory": {
                    "description": "Lambda function memory",
                    "question": "What memory size would you like for your Lambda function? (128, 256, 512, 1024, or 2048 MB)",
                    "extracted_by_lex": False
                },
                "lambdaTimeout": {
                    "description": "Lambda timeout in seconds",
                    "question": "How many seconds should the Lambda function timeout be? (typical: 30-60 seconds)",
                    "extracted_by_lex": False
                },
                "stageName": {
                    "description": "API Gateway stage name",
                    "question": "What stage name would you like? (e.g., 'dev', 'prod', 'test')",
                    "extracted_by_lex": False,
                    "default": "dev"
                }
            }
        }

    def extract_parameters_from_message(self, message: str, template_name: str) -> dict:
        """
        Extract deployment parameters from user message using keyword matching
        
        Args:
            message: User message
            template_name: Template being deployed
            
        Returns:
            dict: Extracted parameters
        """
        extracted = {}
        msg_lower = message.lower()

        if template_name == "serverless-api":
            # Extract lambda memory
            if "memory" in msg_lower:
                for size in [128, 256, 512, 1024, 2048]:
                    if str(size) in msg_lower:
                        extracted["lambdaMemory"] = size
                        break

            # Extract timeout
            if "timeout" in msg_lower or "second" in msg_lower:
                import re
                match = re.search(r'(\d+)\s*(?:second|sec|s)?', msg_lower)
                if match:
                    extracted["lambdaTimeout"] = int(match.group(1))

            # Extract stage name
            for stage in ["dev", "prod", "test", "staging", "development", "production"]:
                if stage in msg_lower:
                    extracted["stageName"] = "prod" if stage in ["prod", "production"] else "dev"
                    break

        return extracted

    def get_missing_parameters(self, template_name: str, extracted_params: dict) -> list:
        """
        Get list of missing required parameters
        
        Args:
            template_name: Template name
            extracted_params: Already extracted parameters
            
        Returns:
            list: List of missing parameter descriptions
        """
        if template_name not in self.required_params:
            return []

        required = self.required_params[template_name]
        missing = []

        for param_name, param_info in required.items():
            # Skip if already extracted
            if param_name in extracted_params:
                continue

            # Skip if has default
            if "default" in param_info:
                continue

            missing.append(param_info)

        return missing

    def generate_follow_up_questions(self, missing_params: list, session=None) -> str:
        """
        Generate intelligent follow-up questions for missing parameters
        
        Args:
            missing_params: List of missing parameter info dicts
            session: boto3 session for Bedrock
            
        Returns:
            str: Formatted follow-up questions
        """
        if not missing_params:
            return ""

        # Simple approach: list the questions directly
        questions = []
        for param in missing_params:
            questions.append(f"• {param['question']}")

        try:
            # Try to use Bedrock to generate a more conversational version
            param_list = "\n".join([p['question'] for p in missing_params])
            prompt = f"""
            The user wants to deploy a serverless API. We need some specifications.
            Generate a friendly, concise message asking for these details:
            
            {param_list}
            
            Make it conversational and helpful, not just a list. Keep it under 150 words.
            """

            bedrock_result = extract_parameters_with_bedrock(prompt, session)
            if bedrock_result and "architecture" in bedrock_result:
                return bedrock_result["architecture"]
        except Exception as e:
            logger.warning(f"Bedrock follow-up generation failed: {e}")

        # Fallback: just format the questions nicely
        return "To help you better, I need a few specifications:\n\n" + "\n".join(questions)

    def build_response_with_questions(self, intent: str, message: str, template_name: str, 
                                     initial_reply: str, session=None) -> dict:
        """
        Build a response that includes follow-up questions for deployment
        
        Args:
            intent: Detected intent
            message: User message
            template_name: Template name
            initial_reply: Initial bot reply from Lex
            session: boto3 session
            
        Returns:
            dict: Enhanced response with follow-up questions
        """
        response = {
            "intent": intent,
            "botReply": initial_reply,
            "templateName": template_name,
            "extractedParams": {},
            "followUpQuestions": []
        }

        # Only ask questions for deployment intents
        if intent != "DeployServerlessAPI":
            return response

        # Extract parameters from the message
        extracted = self.extract_parameters_from_message(message, template_name)
        response["extractedParams"] = extracted
        logger.info(f"Extracted parameters: {extracted}")

        # Get missing parameters
        missing = self.get_missing_parameters(template_name, extracted)

        if missing:
            logger.info(f"Missing parameters: {[p['description'] for p in missing]}")
            
            # Generate follow-up questions
            questions = self.generate_follow_up_questions(missing, session)
            response["botReply"] += f"\n\n❓ **What I need to know:**\n{questions}"
            response["followUpQuestions"] = [p["question"] for p in missing]
            response["parametersGathered"] = len(extracted)
            response["parametersNeeded"] = len(missing)
        else:
            # All parameters gathered - ready to deploy
            response["botReply"] += "\n\n✅ Great! I have all the information needed to deploy your serverless API. Click 'Deploy' to proceed."
            response["readyToDeploy"] = True

        return response


# Global instance
conversation_engine = ConversationEngine()

"""
Enhanced Template Registry - Flexible template system for Git expansion
"""
import os
import json
from typing import Dict, List, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger("template_registry")


class TemplateRegistry:
    """Manages all deployment templates"""

    # Hardcoded template definitions (can be loaded from files later)
    BUILTIN_TEMPLATES = {
        "serverless-api": {
            "template_id": "serverless-api",
            "name": "Serverless REST API",
            "description": "API Gateway + Lambda + DynamoDB serverless API",
            "use_cases": ["REST APIs", "Microservices", "Webhooks"],
            "supported_intents": ["DeployIntent", "CreateIntent"],
            "required_params": ["memory", "timeout"],
            "optional_params": ["region", "stage", "name", "description"],
            "size_presets": {
                "micro": {"memory": 128, "timeout": 30, "description": "Low traffic, startup"},
                "medium": {"memory": 512, "timeout": 60, "description": "Normal production"},
                "large": {"memory": 1024, "timeout": 120, "description": "High traffic, enterprise"}
            },
            "traffic_mapping": {
                "low": "micro",
                "medium": "medium",
                "high": "large",
                "startup": "micro",
                "production": "large",
                "enterprise": "large"
            },
            "services": ["AWS::Lambda::Function", "AWS::ApiGateway::RestApi", "AWS::DynamoDB::Table"],
            "path": os.path.join(os.path.dirname(__file__), "..", "..", "templates", "serverless-api")
        },
        "s3-static-website": {
            "template_id": "s3-static-website",
            "name": "S3 Static Website",
            "description": "S3 + CloudFront static website hosting",
            "use_cases": ["Static websites", "Documentation", "SPAs"],
            "supported_intents": ["DeployIntent"],
            "required_params": ["domain_name"],
            "optional_params": ["region", "cache_ttl"],
            "size_presets": {
                "micro": {"storage": "10GB", "objects": "unlimited", "description": "Small sites"},
                "medium": {"storage": "100GB", "objects": "unlimited", "description": "Medium sites"},
                "large": {"storage": "1TB", "objects": "unlimited", "description": "Large sites"}
            },
            "traffic_mapping": {
                "low": "micro",
                "medium": "medium",
                "high": "large"
            },
            "services": ["AWS::S3::Bucket", "AWS::CloudFront::Distribution"],
            "path": os.path.join(os.path.dirname(__file__), "..", "..", "templates", "s3-static-website")
        },
        "vpc-private-subnet": {
            "template_id": "vpc-private-subnet",
            "name": "VPC with Private Subnets",
            "description": "VPC with public/private subnets, NAT Gateway, Security Groups",
            "use_cases": ["Enterprise apps", "Multi-tier apps", "Secure databases"],
            "supported_intents": ["DeployIntent"],
            "required_params": ["vpc_cidr", "availability_zones"],
            "optional_params": ["region", "nat_gateway_count"],
            "size_presets": {
                "micro": {"nat_gateways": 1, "subnets": 2, "description": "Dev/Test"},
                "medium": {"nat_gateways": 2, "subnets": 4, "description": "Production"},
                "large": {"nat_gateways": 3, "subnets": 6, "description": "Enterprise"}
            },
            "traffic_mapping": {
                "low": "micro",
                "medium": "medium",
                "high": "large"
            },
            "services": ["AWS::EC2::VPC", "AWS::EC2::Subnet", "AWS::EC2::NatGateway"],
            "path": os.path.join(os.path.dirname(__file__), "..", "..", "templates", "vpc-private-subnet")
        },
        "ecs-fargate-api": {
            "template_id": "ecs-fargate-api",
            "name": "ECS Fargate Container API",
            "description": "ECS Fargate cluster with Application Load Balancer",
            "use_cases": ["Container apps", "Docker microservices", "Scalable APIs"],
            "supported_intents": ["DeployIntent"],
            "required_params": ["docker_image", "container_port"],
            "optional_params": ["region", "cpu", "memory", "desired_count"],
            "size_presets": {
                "micro": {"cpu": "256", "memory": "512", "desired_count": 1, "description": "Dev"},
                "medium": {"cpu": "512", "memory": "1024", "desired_count": 2, "description": "Staging"},
                "large": {"cpu": "1024", "memory": "2048", "desired_count": 3, "description": "Production"}
            },
            "traffic_mapping": {
                "low": "micro",
                "medium": "medium",
                "high": "large"
            },
            "services": ["AWS::ECS::Cluster", "AWS::ECS::Service", "AWS::ElasticLoadBalancingV2::LoadBalancer"],
            "path": os.path.join(os.path.dirname(__file__), "..", "..", "templates", "ecs-fargate-api")
        }
    }

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.templates = dict(self.BUILTIN_TEMPLATES)  # Copy built-in templates
        self.load_custom_templates()

    def load_custom_templates(self):
        """Load custom templates from templates directory if available"""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        try:
            for item in os.listdir(self.templates_dir):
                template_dir = os.path.join(self.templates_dir, item)
                if os.path.isdir(template_dir):
                    template_json = os.path.join(template_dir, "template.json")
                    if os.path.exists(template_json):
                        try:
                            with open(template_json, 'r') as f:
                                template = json.load(f)
                                template['path'] = template_dir
                                self.templates[item] = template
                                logger.info(f"Loaded custom template: {item}")
                        except Exception as e:
                            logger.warning(f"Failed to load template {item}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error loading custom templates: {str(e)}")

    def list_templates(self) -> List[Dict]:
        """Get list of all available templates"""
        return [
            {
                "template_id": template_id,
                "name": template.get("name", "Unknown"),
                "description": template.get("description", ""),
                "use_cases": template.get("use_cases", [])
            }
            for template_id, template in self.templates.items()
        ]

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID"""
        template = self.templates.get(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None
        return template

    def get_template_by_intent(self, intent: str) -> Optional[Dict]:
        """Get recommended template for an intent"""
        for template_id, template in self.templates.items():
            if intent in template.get("supported_intents", []):
                logger.info(f"Found template for {intent}: {template_id}")
                return template
        logger.warning(f"No template found for intent: {intent}")
        return None

    def infer_size_from_traffic(self, template_id: str, traffic_level: str) -> Optional[Dict]:
        """
        Infer resource size based on traffic level
        
        Args:
            template_id: Template ID
            traffic_level: "low", "medium", "high", "startup", "production", "enterprise"
        
        Returns:
            Size preset with memory, timeout, etc.
        """
        template = self.get_template(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None
        
        # Get traffic mapping
        traffic_mapping = template.get("traffic_mapping", {})
        size_name = traffic_mapping.get(traffic_level.lower(), "medium")
        
        # Get size preset
        size_presets = template.get("size_presets", {})
        size = size_presets.get(size_name)
        
        if size:
            logger.info(f"Inferred size for {template_id}@{traffic_level}: {size_name}")
        
        return size

    def validate_params(self, template_id: str, parameters: Dict) -> Dict:
        """
        Validate parameters against template requirements
        
        Returns:
            {
                "valid": True/False,
                "errors": [list of validation errors]
            }
        """
        template = self.get_template(template_id)
        if not template:
            return {"valid": False, "errors": [f"Template not found: {template_id}"]}
        
        errors = []
        required_params = template.get("required_params", [])
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Required parameter missing: {param}")
        
        if errors:
            logger.warning(f"Parameter validation failed: {errors}")
            return {"valid": False, "errors": errors}
        
        logger.info(f"Parameters valid for {template_id}")
        return {"valid": True, "errors": []}

    def select_template(self, intent: str, user_message: str = "") -> Optional[Dict]:
        """
        Select best template for intent
        
        Args:
            intent: Detected intent
            user_message: Optional user message for context
        
        Returns:
            Recommended template
        """
        template = self.get_template_by_intent(intent)
        if template:
            logger.info(f"Selected template for {intent}: {template.get('template_id')}")
            return template
        
        # Default to serverless-api for deployment intents
        if "Deploy" in intent or "Create" in intent:
            logger.info(f"Defaulting to serverless-api for {intent}")
            return self.get_template("serverless-api")
        
        logger.warning(f"Could not select template for {intent}")
        return None


# Global instance
_registry = None


def get_registry(templates_dir: str = "templates") -> TemplateRegistry:
    """Get or create global template registry"""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry(templates_dir)
    return _registry

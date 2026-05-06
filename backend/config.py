import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))

    # AWS settings
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # For Lex and Bedrock services
    DEFAULT_DEPLOYMENT_REGION = os.getenv("DEFAULT_DEPLOYMENT_REGION", "ap-south-1")  # For user deployments

    # Lex settings (Phase 3)
    LEX_BOT_ID = os.getenv("LEX_BOT_ID", "")
    LEX_BOT_ALIAS_ID = os.getenv("LEX_BOT_ALIAS_ID", "")
    LEX_LOCALE_ID = os.getenv("LEX_LOCALE_ID", "en_US")

    # Project paths
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

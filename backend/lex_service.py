"""
Lex V2 Service - Intent Detection with Intelligent Fallback
Purpose: Use Lex V2 Runtime ONLY for intent classification, not responses
"""
import boto3
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from lex_intents_config import KEYWORD_PATTERNS, INTENT_PRIORITY

logger = get_logger("lex_service")

# Configuration
BOT_ID = os.getenv("LEX_BOT_ID", "CloudOpsBot")
BOT_ALIAS_ID = os.getenv("LEX_BOT_ALIAS_ID", "LIVE")
LOCALE_ID = "en_US"
REGION = os.getenv("AWS_REGION", "us-east-1")


def detect_intent_lex_v2(message: str, session_id: str, session=None) -> dict:
    """
    Detect intent using AWS Lex V2 Runtime
    
    Args:
        message: User message
        session_id: Unique session ID
        session: boto3 session (optional, uses default if None)
    
    Returns:
        dict: {
            "intent": "DeployIntent",
            "confidence": 0.95,
            "slots": {},
            "session_state": {}
        }
    """
    try:
        if session is None:
            session = boto3.Session()
        
        client = session.client('lexv2-runtime', region_name=REGION)
        
        response = client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=session_id,
            text=message
        )
        
        # Extract intent from response
        intent_name = response.get('sessionState', {}).get('intent', {}).get('name')
        confidence = response.get('sessionState', {}).get('intent', {}).get('nluConfidence', {}).get('score', 0.0)
        slots = response.get('sessionState', {}).get('intent', {}).get('slots', {})
        lex_messages = response.get('messages', [])
        
        # Format slots for consumption
        formatted_slots = {}
        if slots:
            for slot_name, slot_value in slots.items():
                if slot_value and 'value' in slot_value:
                    formatted_slots[slot_name] = slot_value['value']['interpretedValue']
        
        # Extract plain text messages
        bot_messages = []
        if lex_messages:
            for msg in lex_messages:
                if msg.get('contentType') == 'PlainText':
                    bot_messages.append(msg.get('content'))
                
        logger.debug(f"Lex V2 detected: intent={intent_name}, confidence={confidence}, messages={len(bot_messages)}")
        
        return {
            "intent": intent_name or "GeneralQuestion",
            "confidence": confidence,
            "slots": formatted_slots,
            "session_state": response.get('sessionState', {}),
            "lex_messages": bot_messages
        }
        
    except Exception as e:
        logger.warning(f"Lex V2 detection failed: {str(e)}. Using fallback.")
        return None


def fallback_intent_detection(message: str) -> dict:
    """
    Intelligent fallback intent detection using enhanced keyword matching
    Used when Lex V2 is unavailable or low confidence
    
    This function is designed to handle ANY user question by:
    1. Matching specific keywords first (high priority intents)
    2. Using semantic analysis for general questions
    3. Defaulting to GeneralQuestionIntent for unmatched queries
    
    Args:
        message: User message
    
    Returns:
        dict: {
            "intent": "DeployIntent",
            "confidence": 0.6,
            "slots": {},
            "fallback": True
        }
    """
    message_lower = message.lower().strip()
    best_match = None
    best_priority = 999999
    matches = []
    
    # Check each intent's keywords with enhanced matching
    for intent, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            # Exact substring match (most reliable)
            if pattern_lower in message_lower:
                priority = INTENT_PRIORITY.get(intent, 999)
                matches.append((intent, priority, "exact"))
                if priority < best_priority:
                    best_priority = priority
                    best_match = intent
                logger.debug(f"Exact keyword match: {intent} (pattern: {pattern})")
                continue
            
            # Word boundary match (handles word variations)
            import re
            if re.search(r'\b' + re.escape(pattern_lower) + r'\b', message_lower):
                priority = INTENT_PRIORITY.get(intent, 999) + 1  # Slightly lower priority
                matches.append((intent, priority, "word_boundary"))
                if priority < best_priority:
                    best_priority = priority
                    best_match = intent
                logger.debug(f"Word boundary match: {intent} (pattern: {pattern})")
                continue
    
    # If we found a match, calculate confidence
    if best_match:
        # Calculate confidence based on match count, priority, and match type
        match_count = len([m for m in matches if m[0] == best_match])
        exact_matches = len([m for m in matches if m[0] == best_match and m[2] == "exact"])
        
        # Higher confidence for exact matches and multiple matches
        base_confidence = 0.4
        confidence = min(0.95, base_confidence + (match_count * 0.1) + (exact_matches * 0.2))
        
        logger.info(f"Fallback detected: {best_match} (confidence={confidence:.2f}, matches={match_count})")
        return {
            "intent": best_match,
            "confidence": confidence,
            "slots": {},
            "fallback": True,
            "lex_messages": []
        }
    
    # Advanced semantic analysis for unmatched messages
    # Check for question patterns that indicate specific intents
    question_words = ["what", "how", "why", "when", "where", "which", "who", "can", "do", "is", "are", "does", "will", "should", "could", "would"]
    action_words = ["deploy", "create", "build", "launch", "start", "run", "execute", "delete", "remove", "stop", "update", "change", "modify", "list", "show", "describe", "explain"]
    
    has_question = any(word in message_lower for word in question_words)
    has_action = any(word in message_lower for word in action_words)
    
    if has_question and not has_action:
        # Pure question - likely GeneralQuestionIntent
        logger.info("Semantic analysis: Pure question detected -> GeneralQuestionIntent")
        return {
            "intent": "GeneralQuestionIntent",
            "confidence": 0.7,
            "slots": {},
            "fallback": True,
            "lex_messages": []
        }
    elif has_action:
        # Contains action words - could be various intents
        if any(word in message_lower for word in ["delete", "remove", "stop", "terminate", "destroy"]):
            logger.info("Semantic analysis: Destructive action detected -> TerminateDeploymentIntent")
            return {
                "intent": "TerminateDeploymentIntent",
                "confidence": 0.6,
                "slots": {},
                "fallback": True,
                "lex_messages": []
            }
        elif any(word in message_lower for word in ["update", "change", "modify", "scale"]):
            logger.info("Semantic analysis: Modification detected -> UpdateDeploymentIntent")
            return {
                "intent": "UpdateDeploymentIntent",
                "confidence": 0.6,
                "slots": {},
                "fallback": True,
                "lex_messages": []
            }
        elif any(word in message_lower for word in ["list", "show", "what is running", "what do i have"]):
            logger.info("Semantic analysis: Listing detected -> ListResourcesIntent")
            return {
                "intent": "ListResourcesIntent",
                "confidence": 0.6,
                "slots": {},
                "fallback": True,
                "lex_messages": []
            }
        elif "upload" in message_lower or "put" in message_lower:
             return {
                 "intent": "UploadFileIntent",
                 "confidence": 0.6,
                 "slots": {},
                 "fallback": True,
                 "lex_messages": []
             }
        elif "bucket" in message_lower or "s3" in message_lower:
            if "create" in message_lower or "make" in message_lower or "new" in message_lower:
                 return {
                     "intent": "CreateBucketIntent",
                     "confidence": 0.6,
                     "slots": {},
                     "fallback": True,
                     "lex_messages": []
                 }
            elif "list" in message_lower or "show" in message_lower:
                 return {
                     "intent": "ListBucketsIntent",
                     "confidence": 0.6,
                     "slots": {},
                     "fallback": True,
                     "lex_messages": []
                 }
            elif "delete" in message_lower or "remove" in message_lower:
                 return {
                     "intent": "DeleteBucketIntent",
                     "confidence": 0.6,
                     "slots": {},
                     "fallback": True,
                     "lex_messages": []
                 }
        else:
            # Default to deploy for action-oriented messages
            logger.info("Semantic analysis: General action detected -> DeployIntent")
            return {
                "intent": "DeployIntent",
                "confidence": 0.5,
                "slots": {},
                "fallback": True,
                "lex_messages": []
            }
    
    # Default to GeneralQuestionIntent for everything else
    logger.info("No specific pattern matched. Defaulting to GeneralQuestionIntent")
    return {
        "intent": "GeneralQuestionIntent",
        "confidence": 0.4,
        "slots": {},
        "fallback": True,
        "lex_messages": []
    }


def get_intent(message: str, session_id: str, use_fallback: bool = True, session=None, conversation_state: dict = None) -> dict:
    """
    Main entry point for intent detection with intelligent fallback
    Tries Lex V2 first, then enhanced fallback for low confidence or failures
    """
    # CRITICAL OVERRIDE: AWS Lex bot might over-aggressively match "create a bucket" to DeployIntent
    message_lower = message.lower().strip()
    
    if ("host" in message_lower and "website" in message_lower) or "github" in message_lower:
        return {
            "intent": "DeployStaticWebsiteIntent",
            "confidence": 1.0,
            "slots": {},
            "method": "website_override",
            "lex_messages": []
        }
        
    if "upload" in message_lower or "put file" in message_lower:
        return {
            "intent": "UploadFileIntent",
            "confidence": 1.0,
            "slots": {},
            "method": "bucket_override",
            "lex_messages": []
        }
        
    if "bucket" in message_lower or "s3" in message_lower:
        if "create" in message_lower or "make" in message_lower or "new" in message_lower:
            return {
                "intent": "CreateBucketIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "list" in message_lower or "show" in message_lower:
            return {
                "intent": "ListBucketsIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "upload" in message_lower or "put" in message_lower:
            return {
                "intent": "UploadFileIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "delete" in message_lower or "remove" in message_lower:
            return {
                "intent": "DeleteBucketIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }

    # Check conversation state for ongoing deployment
    if conversation_state and conversation_state.get("selectedTemplate") and not conversation_state.get("size"):
        # We're in the middle of gathering deployment parameters
        size_keywords = ["micro", "small", "low traffic", "medium", "normal", "large", "high traffic", "enterprise"]
        if any(keyword in message_lower for keyword in size_keywords):
            logger.info("Conversation context: Detected size specification in ongoing deployment -> DeployIntent")
            return {
                "intent": "DeployIntent",
                "confidence": 0.9,
                "slots": {},
                "method": "conversation_context",
                "lex_messages": []
            }
            
    # Check conversation state for ongoing static website deployment
    if conversation_state:
        if conversation_state.get("awaitingWebsiteType") or conversation_state.get("awaitingGithubUrl") or conversation_state.get("awaitingDeployWebsiteConfirm"):
            logger.info("Conversation context: Awaiting static website details -> DeployStaticWebsiteIntent")
            return {
                "intent": "DeployStaticWebsiteIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "conversation_context",
                "lex_messages": []
            }
            
    # Check conversation state for ongoing file uploads or deletions
    if conversation_state:
        if conversation_state.get("awaitingBucketName") or conversation_state.get("awaitingFileName") or conversation_state.get("awaitingFileContent"):
            logger.info("Conversation context: Awaiting file upload parameters -> UploadFileIntent")
            return {
                "intent": "UploadFileIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "conversation_context",
                "lex_messages": []
            }
            
        if conversation_state.get("awaitingBucketDeleteConfirm") or conversation_state.get("awaitingDeleteBucketName"):
            logger.info("Conversation context: Awaiting bucket deletion confirmation -> DeleteBucketIntent")
            return {
                "intent": "DeleteBucketIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "conversation_context",
                "lex_messages": []
            }
            
    # CRITICAL OVERRIDE: AWS Lex bot might over-aggressively match "create a bucket" to DeployIntent
    message_lower = message.lower().strip()
    if "bucket" in message_lower or "s3" in message_lower:
        if "create" in message_lower or "make" in message_lower or "new" in message_lower:
            return {
                "intent": "CreateBucketIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "list" in message_lower or "show" in message_lower:
            return {
                "intent": "ListBucketsIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "upload" in message_lower or "put" in message_lower:
            return {
                "intent": "UploadFileIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
        elif "delete" in message_lower or "remove" in message_lower:
            return {
                "intent": "DeleteBucketIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "bucket_override"
            }
            
    if "ec2" in message_lower or "instance" in message_lower or "server" in message_lower:
        if "create" in message_lower or "make" in message_lower or "launch" in message_lower or "new" in message_lower:
            return {
                "intent": "CreateInstanceIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "ec2_override"
            }
        elif "list" in message_lower or "show" in message_lower:
            return {
                "intent": "ListInstancesIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "ec2_override"
            }
        elif "stop" in message_lower or "pause" in message_lower:
            return {
                "intent": "StopInstanceIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "ec2_override"
            }
        elif "describe" in message_lower or "status" in message_lower or "detail" in message_lower:
            return {
                "intent": "DescribeInstanceIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "ec2_override"
            }
        elif "delete" in message_lower or "remove" in message_lower or "terminate" in message_lower:
            return {
                "intent": "TerminateInstanceIntent",
                "confidence": 1.0,
                "slots": {},
                "method": "ec2_override"
            }
    
    # Try Lex V2 first
    lex_result = detect_intent_lex_v2(message, session_id, session)
    
    # CRITICAL: Since the AWS Lex bot might over-aggressively match "create a bucket" to DeployIntent
    # Provide a hard-override for bucket-specific and ec2-specific operations
    message_lower = message.lower().strip()
    is_bucket_command = "bucket" in message_lower or "s3" in message_lower
    is_ec2_command = "ec2" in message_lower or "instance" in message_lower or "server" in message_lower
    
    if lex_result and lex_result.get("confidence", 0) > 0.7:
        # If Lex thinks it's DeployIntent but the user said "bucket" or "ec2", override Lex
        if lex_result["intent"] in ["DeployIntent", "GeneralQuestionIntent"]:
            if is_bucket_command:
                logger.info("Lex returned generic intent but user asked for a bucket. Overriding lex outcome.")
                if "list" in message_lower or "show" in message_lower:
                    return {"intent": "ListBucketsIntent", "confidence": 1.0, "slots": {}, "method": "bucket_override", "lex_messages": []}
                elif "delete" in message_lower or "remove" in message_lower:
                    return {"intent": "DeleteBucketIntent", "confidence": 1.0, "slots": {}, "method": "bucket_override", "lex_messages": []}
                elif "upload" in message_lower or "put file" in message_lower:
                    return {"intent": "UploadFileIntent", "confidence": 1.0, "slots": {}, "method": "bucket_override", "lex_messages": []}
                else:
                    return {"intent": "CreateBucketIntent", "confidence": 1.0, "slots": {}, "method": "bucket_override", "lex_messages": []}
            elif is_ec2_command:
                logger.info("Lex returned generic intent but user asked for EC2. Overriding lex outcome.")
                if "list" in message_lower or "show" in message_lower:
                    return {"intent": "ListInstancesIntent", "confidence": 1.0, "slots": {}, "method": "ec2_override", "lex_messages": []}
                elif "stop" in message_lower or "pause" in message_lower:
                    return {"intent": "StopInstanceIntent", "confidence": 1.0, "slots": {}, "method": "ec2_override", "lex_messages": []}
                elif "describe" in message_lower or "status" in message_lower or "detail" in message_lower:
                    return {"intent": "DescribeInstanceIntent", "confidence": 1.0, "slots": {}, "method": "ec2_override", "lex_messages": []}
                elif "delete" in message_lower or "remove" in message_lower or "terminate" in message_lower:
                    return {"intent": "TerminateInstanceIntent", "confidence": 1.0, "slots": {}, "method": "ec2_override", "lex_messages": []}
                else:
                    return {"intent": "CreateInstanceIntent", "confidence": 1.0, "slots": {}, "method": "ec2_override", "lex_messages": []}
        
        # Lex is confident and it's not a bucket conflict - use it
        lex_result["method"] = "lex_v2"
        logger.info(f"Using Lex V2 result: {lex_result['intent']} (confidence: {lex_result['confidence']:.2f})")
        return lex_result
    
    # Lex failed or low confidence - use enhanced fallback
    if use_fallback:
        logger.info("Using enhanced fallback detection")
        fallback_result = fallback_intent_detection(message)
        
        # If Lex gave a result but with low confidence, compare with fallback
        if lex_result and lex_result.get("confidence", 0) > fallback_result.get("confidence", 0):
            # Lex result is better even if low confidence
            lex_result["method"] = "lex_v2_low_confidence"
            logger.info(f"Using Lex V2 (low confidence): {lex_result['intent']} (confidence: {lex_result['confidence']:.2f})")
            return lex_result
        else:
            # Fallback is better or Lex failed completely
            fallback_result["method"] = "enhanced_fallback"
            logger.info(f"Using enhanced fallback: {fallback_result['intent']} (confidence: {fallback_result['confidence']:.2f})")
            return fallback_result
    
    # No fallback allowed - return Lex result or default
    if lex_result:
        lex_result["method"] = "lex_v2"
        return lex_result
    
    # Ultimate fallback - always return something
    logger.warning("All detection methods failed, using ultimate fallback")
    return {
        "intent": "GeneralQuestionIntent",
        "confidence": 0.1,
        "slots": {},
        "method": "ultimate_fallback"
    }

def validate_chat_payload(payload: dict):
    if not payload:
        return False, "Missing JSON body"

    if "message" not in payload:
        return False, "Missing 'message' field"

    msg = str(payload.get("message", "")).strip()
    if not msg:
        return False, "Message cannot be empty"

    if len(msg) > 500:
        return False, "Message too long (max 500 chars)"

    # Optional: accountMode and roleArn for user account mode
    account_mode = payload.get("accountMode")
    if account_mode and account_mode not in ["our", "user"]:
        return False, "accountMode must be 'our' or 'user'"

    return True, None


def validate_deploy_payload(payload: dict):
    if not payload:
        return False, "Missing JSON body"

    required_fields = ["intent", "accountMode", "parameters"]
    for field in required_fields:
        if field not in payload:
            return False, f"Missing '{field}' field"

    account_mode = payload.get("accountMode")
    if account_mode not in ["our", "user"]:
        return False, "accountMode must be 'our' or 'user'"

    # If user mode, roleArn is required
    if account_mode == "user" and "roleArn" not in payload:
        return False, "roleArn required when accountMode is 'user'"

    params = payload.get("parameters")
    if not isinstance(params, dict):
        return False, "parameters must be a JSON object"

    return True, None

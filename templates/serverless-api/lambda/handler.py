import json

def main(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Hello Guest! API is working ✅",
            "input": event
        })
    }


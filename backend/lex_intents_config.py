"""
Lex V2 Intent Configuration
Defines all intents, slots, and utterances for the CloudOps chatbot
Ready to be imported into AWS Lex console or via API
"""

# ✅ INTENT DEFINITIONS FOR LEX V2
LEX_INTENTS = {
    "GreetingIntent": {
        "description": "User greets the chatbot or starts conversation",
        "sample_utterances": [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
            "good evening", "good day", "howdy", "hiya", "what's up", "sup", "yo",
            "how are you", "how do you do", "how's it going", "how have you been",
            "nice to meet you", "pleased to meet you", "glad to meet you", "welcome",
            "long time no see", "nice seeing you again", "hello there", "hi there",
            "hey there", "greetings bot", "hello chatbot", "hi assistant", "hey assistant"
        ],
        "slots": {},
    },
    
    "HelpIntent": {
        "description": "User asks what the bot can do or needs assistance",
        "sample_utterances": [
            "what can you do", "who are you", "help me", "show features", "what services do you support",
            "how does this work", "what are you capable of", "capabilities", "tell me about yourself",
            "what do you do", "how do you work", "what's your purpose", "how can you help me",
            "assist me", "what do you offer", "what can you help with", "guide me", "show me how",
            "teach me", "instructions", "how to use this", "tutorial", "documentation", "manual",
            "guide", "help guide", "user guide", "getting started", "how to get started",
            "what features do you have", "what can you do for me", "how do I", "I need help with",
            "can you help me", "please help", "help please", "I need assistance", "assist me please"
        ],
        "slots": {},
    },
    
    "DeployIntent": {
        "description": "User wants to deploy infrastructure",
        "sample_utterances": [
            "deploy a serverless api",
            "create lambda api gateway",
            "launch an API with lambda",
            "deploy infrastructure",
            "build cloud architecture",
            "create backend api",
            "deploy a website",
            "set up a static site",
            "deploy a database",
            "create a vpc",
            "i want to deploy something",
            "deploy app",
        ],
        "slots": {
            "templateType": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Type of template: serverless-api, s3-static-website, ecs-fargate-api, vpc-private-subnet",
                "is_required": False,
            },
            "trafficLevel": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Expected traffic: low, medium, high, enterprise",
                "is_required": False,
            },
            "region": {
                "type": "AMAZON.Region",
                "description": "AWS region for deployment",
                "is_required": False,
            },
            "stageName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Stage: dev, staging, prod",
                "is_required": False,
            },
            "apiName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name for the API or resource",
                "is_required": False,
            },
        }
    },
    
    "ListResourcesIntent": {
        "description": "User asks to see running resources",
        "sample_utterances": [
            "list my resources",
            "show my deployments",
            "what is running now",
            "show active stacks",
            "list services",
            "list infrastructure",
            "what have i deployed",
            "show me everything",
            "list all resources",
        ],
        "slots": {},
    },
    
    "DescribeDeploymentIntent": {
        "description": "User asks for details about a specific deployment",
        "sample_utterances": [
            "show details of my serverless api",
            "what did you deploy",
            "show architecture",
            "what resources are created",
            "describe my deployment",
            "tell me about the api",
            "show deployment details",
        ],
        "slots": {
            "deploymentName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of the deployment to describe",
                "is_required": False,
            },
        }
    },
    
    "TerminateDeploymentIntent": {
        "description": "User wants to delete/terminate infrastructure",
        "sample_utterances": [
            "delete my deployment",
            "terminate the stack",
            "destroy serverless api",
            "remove resources",
            "stop everything",
            "tear down the infrastructure",
            "delete the api",
            "remove the deployment",
            "terminate everything",
        ],
        "slots": {
            "deploymentName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of deployment to terminate",
                "is_required": False,
            },
        }
    },
    
    "UpdateDeploymentIntent": {
        "description": "User wants to modify existing infrastructure",
        "sample_utterances": [
            "update my deployment",
            "change memory",
            "increase timeout",
            "scale up",
            "change stage to prod",
            "enable logging",
            "update the api",
            "modify the configuration",
            "change the settings",
            "update parameters",
        ],
        "slots": {
            "deploymentName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of deployment to update",
                "is_required": False,
            },
            "trafficLevel": {
                "type": "AMAZON.AlphaNumeric",
                "description": "New traffic level",
                "is_required": False,
            },
            "memorySize": {
                "type": "AMAZON.AlphaNumeric",
                "description": "New memory size in MB",
                "is_required": False,
            },
            "timeout": {
                "type": "AMAZON.AlphaNumeric",
                "description": "New timeout in seconds",
                "is_required": False,
            },
        }
    },
    
    "DeployStaticWebsiteIntent": {
        "description": "User wants to host a static website from GitHub",
        "sample_utterances": [
            "I need to host a website",
            "host a website",
            "deploy a static website",
            "host my github repo",
            "deploy website from github"
        ],
        "slots": {}
    },
    
    "CreateBucketIntent": {
        "description": "User wants to create a secure S3 bucket",
        "sample_utterances": [
            "create bucket",
            "make a new bucket",
            "create an s3 bucket",
            "make bucket",
            "new bucket",
            "provision an s3 bucket",
            "set up a bucket"
        ],
        "slots": {}
    },
    
    "ListBucketsIntent": {
        "description": "User wants to see their created S3 buckets",
        "sample_utterances": [
            "show buckets",
            "list buckets",
            "what buckets do i have",
            "list my buckets",
            "show my buckets",
            "display s3 buckets"
        ],
        "slots": {}
    },
    
    "UploadFileIntent": {
        "description": "User wants to upload a file to a bucket",
        "sample_utterances": [
            "upload file to bucket",
            "upload text to bucket",
            "put file in bucket",
            "upload document",
            "save file",
            "create file in s3"
        ],
        "slots": {
            "bucketName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of the target bucket",
                "is_required": True,
            },
            "fileName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of the file",
                "is_required": True,
            },
            "fileContent": {
                "type": "AMAZON.FreeFormInput",
                "description": "Content of the text file",
                "is_required": True,
            }
        }
    },
    
    "DeleteBucketIntent": {
        "description": "User wants to delete an S3 bucket",
        "sample_utterances": [
            "delete bucket",
            "remove bucket",
            "destroy bucket",
            "delete s3 bucket",
            "remove s3 bucket",
            "trash bucket"
        ],
        "slots": {
            "bucketName": {
                "type": "AMAZON.AlphaNumeric",
                "description": "Name of bucket to delete",
                "is_required": False,
            }
        }
    },
    
    "CreateInstanceIntent": {
        "description": "User wants to create an EC2 instance",
        "sample_utterances": [
            "create instance", "launch ec2", "start server", "new virtual machine",
            "provision ec2 instance", "create server"
        ],
        "slots": {}
    },
    
    "ListInstancesIntent": {
        "description": "User wants to list EC2 instances",
        "sample_utterances": [
            "list instances", "show my ec2 servers", "display ec2 instances",
            "what instances do I have", "show machines"
        ],
        "slots": {}
    },
    
    "DescribeInstanceIntent": {
        "description": "User wants to describe an EC2 instance",
        "sample_utterances": [
            "describe instance", "status of server", "ec2 details",
            "show instance info", "get instance status"
        ],
        "slots": {
            "instanceId": {
                "type": "AMAZON.AlphaNumeric",
                "description": "ID of the EC2 instance",
                "is_required": False,
            }
        }
    },
    
    "StopInstanceIntent": {
        "description": "User wants to stop an EC2 instance",
        "sample_utterances": [
            "stop instance", "pause server", "stop ec2 instance",
            "halt machine", "shut down instance"
        ],
        "slots": {
            "instanceId": {
                "type": "AMAZON.AlphaNumeric",
                "description": "ID of the EC2 instance",
                "is_required": False,
            }
        }
    },
    
    "TerminateInstanceIntent": {
        "description": "User wants to terminate an EC2 instance",
        "sample_utterances": [
            "terminate instance", "delete server", "destroy ec2 machine",
            "terminate ec2 instance", "remove instance"
        ],
        "slots": {
            "instanceId": {
                "type": "AMAZON.AlphaNumeric",
                "description": "ID of the EC2 instance",
                "is_required": False,
            }
        }
    },
    
    "GeneralQuestionIntent": {
        "description": "User asks AWS/cloud questions not related to infra actions - catch-all for general inquiries",
        "sample_utterances": [
            "what is IAM role", "explain VPC", "what is API Gateway", "what is Bedrock",
            "what is Lambda", "what is S3", "what is DynamoDB", "what is CloudFormation",
            "what is CDK", "explain Lex", "what is EC2", "what is RDS", "what is Route 53",
            "what is CloudWatch", "what is CloudTrail", "what is SNS", "what is SQS",
            "what is ElastiCache", "what is Elastic Load Balancer", "what is Auto Scaling",
            "what is Elastic Beanstalk", "what is ECS", "what is EKS", "what is Fargate",
            "what is Aurora", "what is Redshift", "what is Athena", "what is Glue",
            "what is Step Functions", "what is EventBridge", "what is X-Ray",
            "what is Systems Manager", "what is Config", "what is Trusted Advisor",
            "what is Cost Explorer", "what is Budgets", "what is Organizations",
            "what is Control Tower", "what is Security Hub", "what is GuardDuty",
            "what is Macie", "what is Inspector", "what is Detective",
            "how does AWS work", "what is cloud computing", "explain serverless",
            "what is microservices", "what is containers", "what is kubernetes",
            "what is docker", "what is terraform", "what is ansible", "what is jenkins",
            "what is CI/CD", "what is DevOps", "what is infrastructure as code",
            "what is monitoring", "what is logging", "what is alerting",
            "what is backup", "what is disaster recovery", "what is high availability",
            "what is scalability", "what is performance", "what is security",
            "what is compliance", "what is governance", "what is cost optimization",
            "how much does it cost", "what are the pricing", "what is free tier",
            "what is reserved instances", "what is spot instances", "what is savings plans",
            "can you explain", "tell me about", "I want to know", "I'm curious about",
            "what does this mean", "what is the difference", "how do I", "why should I",
            "when should I", "where can I", "which one should I", "who can help me",
            "is it possible", "does it support", "can I use", "will it work",
            "should I use", "could you tell me", "would you explain", "please explain",
            "help me understand", "I'm confused about", "I don't understand",
            "what's the best way", "what are the benefits", "what are the drawbacks",
            "what are the limitations", "what are the requirements", "what do I need",
            "how do I get started", "where do I begin", "what's next", "what now"
        ],
        "slots": {},
    },
    
    "AMAZON_FallbackIntent": {
        "description": "Fallback for unmatched utterances",
        "is_builtin": True,
        "slots": {},
    }
}

# ✅ INTENT PRIORITIES (for fallback routing)
INTENT_PRIORITY = {
    "DeployIntent": 1,
    "UpdateDeploymentIntent": 2,
    "TerminateDeploymentIntent": 3,
    "ListResourcesIntent": 4,
    "DescribeDeploymentIntent": 5,
    "HelpIntent": 6,
    "GeneralQuestionIntent": 7,
    "GreetingIntent": 8,
    "CreateBucketIntent": 9,
    "ListBucketsIntent": 10,
    "UploadFileIntent": 11,
    "DeleteBucketIntent": 12,
    "DeleteBucketIntent": 12,
    "DeployStaticWebsiteIntent": 13,
    "CreateInstanceIntent": 14,
    "ListInstancesIntent": 15,
    "DescribeInstanceIntent": 16,
    "StopInstanceIntent": 17,
    "TerminateInstanceIntent": 18,
}

# ✅ INTENT CATEGORIES
INTENT_CATEGORIES = {
    "deployment_actions": ["DeployIntent", "UpdateDeploymentIntent", "TerminateDeploymentIntent", "DeployStaticWebsiteIntent"],
    "s3_actions": ["CreateBucketIntent", "ListBucketsIntent", "DeleteBucketIntent", "UploadFileIntent"],
    "ec2_actions": ["CreateInstanceIntent", "ListInstancesIntent", "DescribeInstanceIntent", "StopInstanceIntent", "TerminateInstanceIntent"],
    "information": ["ListResourcesIntent", "DescribeDeploymentIntent"],
    "conversational": ["GreetingIntent", "HelpIntent", "GeneralQuestionIntent"],
}

# ✅ KEYWORD FALLBACK PATTERNS (used when Lex unavailable)
KEYWORD_PATTERNS = {
    "GreetingIntent": [
        "hi", "hello", "hey", "greet", "morning", "evening", "afternoon", "night",
        "howdy", "hiya", "sup", "yo", "what's up", "how are you", "how do you do",
        "nice to meet", "pleased to meet", "good day", "salutations", "welcome",
        "how's it going", "how have you been", "long time no see", "nice seeing you"
    ],
    "HelpIntent": [
        "help", "what can", "capabilities", "features", "who are", "about you",
        "what do you do", "how do you work", "what are you", "tell me about",
        "explain yourself", "what's your purpose", "how can you help", "assist me",
        "what services", "what do you offer", "what can you help with", "guide me",
        "teach me", "instructions", "how to", "tutorial", "documentation", "manual",
        "guide", "help guide", "user guide", "getting started", "how to get started",
        "what features do you have", "what can you do for me", "how do I", "I need help with",
        "can you help me", "please help", "help please", "I need assistance", "assist me please"
    ],
    "DeployIntent": [
        "deploy", "create", "build", "launch", "set up", "provision", "start",
        "begin", "initiate", "establish", "construct", "develop", "make", "generate",
        "produce", "setup", "configure", "initialize", "bootstrap", "spin up",
        "bring up", "stand up", "roll out", "implement", "execute", "run", "host",
        "publish", "release", "go live", "activate", "enable", "install", "add",
        "serverless", "api", "lambda", "function", "website", "static", "s3",
        "ecs", "fargate", "vpc", "subnet", "infrastructure", "cloud", "aws"
    ],
    "ListResourcesIntent": [
        "list", "show me", "what is running", "what's running", "active resources", 
        "what do i have", "what's deployed", "what's available", "what's there", 
        "inventory", "catalog", "see all", "display", "view all", "check status", 
        "current deployments", "existing deployments", "what are my", "what have i", 
        "what's in my account", "overview", "summary", "report", "status of", 
        "running instances", "active services", "my resources", "my deployments"
    ],
    "DescribeDeploymentIntent": [
        "describe", "details", "what did", "tell me about my", "what happened to",
        "what is my", "what was", "what's the status", "give me info about",
        "elaborate on my", "break down my", "analyze my", "inspect my", "examine my"
    ],
    "TerminateDeploymentIntent": [
        "terminate", "delete", "remove", "destroy", "tear down", "stop", "end",
        "finish", "close", "shut down", "kill", "cancel", "abort", "cease", "halt",
        "eliminate", "erase", "wipe out", "clean up", "get rid of", "take down",
        "bring down", "shut off", "power off", "disable", "deactivate", "uninstall"
    ],
    "UpdateDeploymentIntent": [
        "update", "modify", "change", "scale", "enable", "upgrade", "improve",
        "enhance", "adjust", "alter", "revise", "edit", "transform", "convert",
        "increase", "decrease", "expand", "reduce", "grow", "shrink", "boost",
        "optimize", "tune", "configure", "reconfigure", "resize", "rescale"
    ],
    "CreateBucketIntent": [
        "create bucket", "make bucket", "new bucket", "provision bucket", "s3 bucket"
    ],
    "ListBucketsIntent": [
        "show buckets", "list buckets", "my buckets", "all buckets", "display buckets"
    ],
    "UploadFileIntent": [
        "upload file", "upload text", "put file", "add file", "upload to s3", "upload to bucket"
    ],
    "DeployStaticWebsiteIntent": [
        "host website", "host a website", "deploy website", "deploy static website", "github repo", "host github"
    ],
    "DeleteBucketIntent": [
        "delete bucket", "remove bucket", "destroy bucket", "trash bucket", "drop bucket"
    ],
    "CreateInstanceIntent": [
        "create instance", "launch ec2", "new instance", "provision instance", "create server"
    ],
    "ListInstancesIntent": [
        "list instances", "show instances", "my instances", "display instances", "my ec2 instances"
    ],
    "DescribeInstanceIntent": [
        "describe instance", "instance details", "status of instance", "instance info", "ec2 details"
    ],
    "StopInstanceIntent": [
        "stop instance", "pause instance", "shut down instance", "halt ec2"
    ],
    "TerminateInstanceIntent": [
        "terminate instance", "delete instance", "destroy instance", "remove instance", "kill ec2"
    ],
    "GeneralQuestionIntent": [
        "what is", "explain", "how does", "what does", "why does", "when does", "where does",
        "which", "who", "can you explain", "tell me how", "help me understand",
        "what's the difference", "compare", "versus", "vs", "how do I", "why should I",
        "when should I", "where can I", "which one", "who can", "is it possible",
        "does it support", "can I use", "will it work", "should I use", "could you tell me",
        "would you explain", "please explain", "help me understand", "I'm confused about",
        "I don't understand", "what's the best way", "what are the benefits", "what are the drawbacks",
        "what are the limitations", "what are the requirements", "what do I need", "how do I get started",
        "where do I begin", "what's next", "what now", "question", "ask", "inquire", "wonder",
        "curious", "confused", "unclear", "unsure", "doubt", "puzzle", "mystify", "baffle",
        "perplex", "confound", "bewilder", "stump"
    ]
}

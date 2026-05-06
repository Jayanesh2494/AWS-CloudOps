"""
AWS CloudOps Chatbot - IAM Policies Required
For both provider account and customer account (USER mode)
"""

# ✅ PROVIDER ACCOUNT POLICIES
PROVIDER_ACCOUNT_POLICIES = {
    "lex-access": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LexBotAccess",
                "Effect": "Allow",
                "Action": [
                    "lex:RecognizeText",
                    "lex:PostText",
                    "lex:PostContent",
                    "lex:GetSession",
                    "lex:PutSession"
                ],
                "Resource": "*"
            },
            {
                "Sid": "LexModelsAccess",
                "Effect": "Allow",
                "Action": [
                    "lex:GetBot",
                    "lex:GetBotAlias",
                    "lex:ListBotAliases"
                ],
                "Resource": "*"
            }
        ]
    },
    
    "bedrock-access": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockInvoke",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::model/anthropic.claude-v2",
                    "arn:aws:bedrock:*::model/anthropic.claude-instant-v1"
                ]
            },
            {
                "Sid": "BedrockList",
                "Effect": "Allow",
                "Action": [
                    "bedrock:ListFoundationModels"
                ],
                "Resource": "*"
            }
        ]
    },
    
    "cdk-cloudformation": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudFormationStack",
                "Effect": "Allow",
                "Action": [
                    "cloudformation:CreateStack",
                    "cloudformation:UpdateStack",
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStacks",
                    "cloudformation:GetTemplateBody"
                ],
                "Resource": "arn:aws:cloudformation:*:*:stack/cloudops-*"
            }
        ]
    },
    
    "sts-assume-role": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeCustomerRole",
                "Effect": "Allow",
                "Action": [
                    "sts:AssumeRole"
                ],
                "Resource": "arn:aws:iam::*:role/CloudOpsRole"
            }
        ]
    }
}

# ✅ CUSTOMER ACCOUNT POLICIES (USER Mode)
CUSTOMER_ACCOUNT_POLICIES = {
    "cloudops-deployment-role": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LexAccess",
                "Effect": "Allow",
                "Action": [
                    "lex:RecognizeText",
                    "lex:PostText",
                    "lex:PostContent"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::model/anthropic.claude-v2",
                    "arn:aws:bedrock:*::model/anthropic.claude-instant-v1"
                ]
            },
            {
                "Sid": "CloudFormationManagement",
                "Effect": "Allow",
                "Action": [
                    "cloudformation:*"
                ],
                "Resource": "arn:aws:cloudformation:*:*:stack/cloudops-*"
            },
            {
                "Sid": "IAMRoleCreation",
                "Effect": "Allow",
                "Action": [
                    "iam:CreateRole",
                    "iam:PutRolePolicy",
                    "iam:PassRole",
                    "iam:GetRole",
                    "iam:ListRolePolicies"
                ],
                "Resource": "arn:aws:iam::*:role/cloudops-*"
            },
            {
                "Sid": "LambdaManagement",
                "Effect": "Allow",
                "Action": [
                    "lambda:CreateFunction",
                    "lambda:UpdateFunction",
                    "lambda:DeleteFunction",
                    "lambda:GetFunction",
                    "lambda:ListFunctions",
                    "lambda:AddPermission",
                    "lambda:RemovePermission"
                ],
                "Resource": "arn:aws:lambda:*:*:function:cloudops-*"
            },
            {
                "Sid": "APIGatewayManagement",
                "Effect": "Allow",
                "Action": [
                    "apigateway:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "DynamoDBManagement",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:CreateTable",
                    "dynamodb:UpdateTable",
                    "dynamodb:DeleteTable",
                    "dynamodb:DescribeTable",
                    "dynamodb:ListTables"
                ],
                "Resource": "arn:aws:dynamodb:*:*:table/cloudops-*"
            },
            {
                "Sid": "S3Management",
                "Effect": "Allow",
                "Action": [
                    "s3:CreateBucket",
                    "s3:DeleteBucket",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:GetBucketVersioning",
                    "s3:PutBucketVersioning",
                    "s3:PutBucketPublicAccessBlock",
                    "s3:GetBucketPublicAccessBlock"
                ],
                "Resource": [
                    "arn:aws:s3:::cloudops-*",
                    "arn:aws:s3:::cloudops-*/*"
                ]
            },
            {
                "Sid": "CloudFrontManagement",
                "Effect": "Allow",
                "Action": [
                    "cloudfront:CreateDistribution",
                    "cloudfront:UpdateDistribution",
                    "cloudfront:DeleteDistribution",
                    "cloudfront:DescribeDistribution",
                    "cloudfront:ListDistributions"
                ],
                "Resource": "*"
            },
            {
                "Sid": "VPCManagement",
                "Effect": "Allow",
                "Action": [
                    "ec2:CreateVpc",
                    "ec2:DeleteVpc",
                    "ec2:DescribeVpcs",
                    "ec2:CreateSubnet",
                    "ec2:DeleteSubnet",
                    "ec2:DescribeSubnets",
                    "ec2:CreateSecurityGroup",
                    "ec2:DeleteSecurityGroup",
                    "ec2:DescribeSecurityGroups",
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress",
                    "ec2:CreateRouteTable",
                    "ec2:DeleteRouteTable",
                    "ec2:CreateRoute",
                    "ec2:DeleteRoute"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECSManagement",
                "Effect": "Allow",
                "Action": [
                    "ecs:CreateCluster",
                    "ecs:DeleteCluster",
                    "ecs:DescribeClusters",
                    "ecs:CreateService",
                    "ecs:DeleteService",
                    "ecs:DescribeServices",
                    "ecs:RegisterTaskDefinition",
                    "ecs:DeregisterTaskDefinition",
                    "ecs:DescribeTaskDefinition"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECRManagement",
                "Effect": "Allow",
                "Action": [
                    "ecr:CreateRepository",
                    "ecr:DeleteRepository",
                    "ecr:DescribeRepositories",
                    "ecr:PutImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage"
                ],
                "Resource": "arn:aws:ecr:*:*:repository/cloudops-*"
            },
            {
                "Sid": "ElasticLoadBalancing",
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:CreateLoadBalancer",
                    "elasticloadbalancing:DeleteLoadBalancer",
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:CreateTargetGroup",
                    "elasticloadbalancing:DeleteTargetGroup",
                    "elasticloadbalancing:DescribeTargetGroups"
                ],
                "Resource": "*"
            },
            {
                "Sid": "CloudWatchLogs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:DeleteLogGroup",
                    "logs:DescribeLogGroups",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:log-group:/aws/cloudops/*"
            },
            {
                "Sid": "TaggingResources",
                "Effect": "Allow",
                "Action": [
                    "ec2:CreateTags",
                    "ec2:DeleteTags"
                ],
                "Resource": "*"
            }
        ]
    }
}

# ✅ CUSTOMER ACCOUNT TRUST RELATIONSHIP (for role that provider assumes)
CUSTOMER_ACCOUNT_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::553015941729:root",  # Provider account
                "Service": "cloudformation.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "your-external-id-here"  # Security best practice
                }
            }
        }
    ]
}

# ✅ TERRAFORM CODE TO CREATE CUSTOMER ROLE
CUSTOMER_ROLE_TERRAFORM = """
# Create the CloudOpsRole in customer's AWS account
resource "aws_iam_role" "cloudops" {
  name = "CloudOpsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::553015941729:root"
          Service = "cloudformation.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "your-secure-external-id"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "CloudOpsRole"
    Environment = "production"
    Service     = "cloudops-chatbot"
  }
}

# Attach the policy
resource "aws_iam_role_policy" "cloudops" {
  name = "cloudops-policy"
  role = aws_iam_role.cloudops.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ... include statements from CUSTOMER_ACCOUNT_POLICIES above
    ]
  })
}

# Output the role ARN
output "cloudops_role_arn" {
  value = aws_iam_role.cloudops.arn
}
"""

# ✅ CLOUDFORMATION TO CREATE CUSTOMER ROLE
CUSTOMER_ROLE_CLOUDFORMATION = """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudOps Chatbot Deployment Role for Customer Account'

Parameters:
  ProviderAccountId:
    Type: String
    Default: '553015941729'
    Description: AWS Account ID of the CloudOps provider
  
  ExternalId:
    Type: String
    NoEcho: true
    Description: External ID for additional security

Resources:
  CloudOpsDeploymentRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: CloudOpsRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${ProviderAccountId}:root'
              Service: cloudformation.amazonaws.com
            Action: 'sts:AssumeRole'
            Condition:
              StringEquals:
                'sts:ExternalId': !Ref ExternalId

  CloudOpsDeploymentPolicy:
    Type: AWS::IAM::RolePolicy
    Properties:
      RoleName: !Ref CloudOpsDeploymentRole
      PolicyName: cloudops-deployment-policy
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          # ... include statements from CUSTOMER_ACCOUNT_POLICIES above
          - Sid: LexAccess
            Effect: Allow
            Action:
              - 'lex:RecognizeText'
              - 'lex:PostText'
              - 'lex:PostContent'
            Resource: '*'
          
          - Sid: BedrockAccess
            Effect: Allow
            Action:
              - 'bedrock:InvokeModel'
              - 'bedrock:InvokeModelWithResponseStream'
            Resource:
              - 'arn:aws:bedrock:*::model/anthropic.claude-v2'

Outputs:
  CloudOpsRoleArn:
    Description: ARN of the CloudOps deployment role
    Value: !GetAtt CloudOpsDeploymentRole.Arn
    Export:
      Name: CloudOpsRoleArn
"""

print("✅ IAM Policies configured")
print("✅ Provider account needs Lex + Bedrock + STS AssumeRole")
print("✅ Customer account needs CloudFormation + service-specific permissions")
print("✅ Trust relationship: Customer role trusts provider account")

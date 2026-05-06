from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    CfnOutput,
)
from constructs import Construct


class ServerlessApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hello_fn = _lambda.Function(
            self,
            "HelloFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.main",
            code=_lambda.Code.from_asset("lambda"),
        )

        api = apigw.LambdaRestApi(
            self,
            "HelloApi",
            handler=hello_fn,
            proxy=True
        )

        # Add outputs for the API URL
        CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="API Gateway URL",
        )

        CfnOutput(
            self,
            "ApiId",
            value=api.rest_api_id,
            description="API Gateway ID",
        )

from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)


class WordleCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        my_lambda = _lambda.Function(
            self, 'CreateUser',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='createUser.handler',
        )

        api = apigw.RestApi(
            self,
            "CdkProjectAPI",
            rest_api_name="CdkProject API",
            description="API for CdkProject",
            deploy_options={
                "stage_name": "v1"
            }
        )

         # Create the `/users` resource
        users_resource = api.root.add_resource("users")

        # Add a POST method to the `/users` resource and connect it to the Lambda function
        create_user_integration = apigw.LambdaIntegration(my_lambda)
        users_resource.add_method("POST", create_user_integration)

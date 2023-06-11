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

        create_user_lambda = _lambda.Function(
            self, 'CreateUser',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='createUser.handler',
        )
        # Create the Lambda function for creating a game
        create_game_lambda = _lambda.Function(
            self,
            "CreateGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="createGame.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        # Create the Lambda function for deleting a game
        delete_game_lambda = _lambda.Function(
            self,
            "DeleteGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="deleteGame.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        api = apigw.RestApi(
            self,
            "CdkProjectAPI",
            rest_api_name="CdkProject API",
            description="API for CdkProject",
            deploy_options={
                "stage_name": "v1"
            },
            endpoint_types=[apigw.EndpointType.REGIONAL]
        )

         # Create the `/users` resource
        users_resource = api.root.add_resource("users")

        # Add a POST method to the `/users` resource and connect it to the create user Lambda function
        create_user_integration = apigw.LambdaIntegration(create_user_lambda)
        users_resource.add_method("POST", create_user_integration)

        # Create the `/users/{user_id}/games` resource
        users_games_resource = users_resource.add_resource("{user_id}").add_resource("games")

        # Add a POST method to the `/users/{user_id}/games` resource and connect it to the create game Lambda function
        create_game_integration = apigw.LambdaIntegration(create_game_lambda)
        users_games_resource.add_method("POST", create_game_integration)

        # Create the `/users/{user_id}/games/{game_id}` resource
        games_resource = users_games_resource.add_resource("{game_id}")

        # Add a DELETE method to the `/users/{user_id}/games/{game_id}` resource and connect it to the delete game Lambda function
        delete_game_integration = apigw.LambdaIntegration(delete_game_lambda)
        games_resource.add_method("DELETE", delete_game_integration)

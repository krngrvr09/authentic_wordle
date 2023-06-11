from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
)

# from aws_cdk import core


class WordleCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # # Create the DynamoDB game table
        # gameTable = dynamodb.Table(
        #     self,
        #     "GameTable",
        #     partition_key=dynamodb.Attribute(name="game_id", type=dynamodb.AttributeType.STRING),
        #     removal_policy=core.RemovalPolicy.DESTROY
        # )

        # # Create the DynamoDB user table
        # userTable = dynamodb.Table(
        #     self,
        #     "UserTable",
        #     partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
        #     removal_policy=core.RemovalPolicy.DESTROY
        # )


        create_user_lambda = _lambda.Function(
            self, 'CreateUser',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='createUser.handler',
            # environment={
            #     "USER_TABLE": userTable.table_name,
            #     "AWS_REGION": self.region
            # }
        )

        # userTable.grant_full_access(create_user_lambda)

        # Create the Lambda function for creating a game
        create_game_lambda = _lambda.Function(
            self,
            "CreateGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="createGame.handler",
            code=_lambda.Code.from_asset("lambda"),
            # environment={
            #     "USER_TABLE": userTable.table_name,
            #     "GAME_TABLE": gameTable.table_name,
            #     "AWS_REGION": self.region
            # }
        )

        # userTable.grant_full_access(create_game_lambda)
        # gameTable.grant_full_access(create_game_lambda)
        

        # Create the Lambda function for deleting a game
        delete_game_lambda = _lambda.Function(
            self,
            "DeleteGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="deleteGame.handler",
            code=_lambda.Code.from_asset("lambda"),
            # environment={
            #     "USER_TABLE": userTable.table_name,
            #     "GAME_TABLE": gameTable.table_name,
            #     "AWS_REGION": self.region
            # }
        )

        # userTable.grant_full_access(delete_game_lambda)
        # gameTable.grant_full_access(delete_game_lambda)
        

        # Create the Lambda function for making a guess
        guess_lambda = _lambda.Function(
            self,
            "GuessLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="guess.handler",
            code=_lambda.Code.from_asset("lambda"),
            # environment={
            #     "USER_TABLE": userTable.table_name,
            #     "GAME_TABLE": gameTable.table_name,
            #     "AWS_REGION": self.region
            # }
        )

        # userTable.grant_full_access(guess_lambda)
        # gameTable.grant_full_access(guess_lambda)

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

        # Create the `/users/{user_id}/games/{game_id}/guess` resource
        guess_resource = games_resource.add_resource("guess")

        # Add a POST method to the `/users/{user_id}/games/{game_id}/guess` resource and connect it to the guess Lambda function
        guess_integration = apigw.LambdaIntegration(guess_lambda)
        guess_resource.add_method("POST", guess_integration)
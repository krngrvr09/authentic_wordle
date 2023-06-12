from constructs import Construct
import aws_cdk as core
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
)



class DBStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the DynamoDB game table
        gameTable = dynamodb.Table(
            self,
            "GameTable",
            partition_key=dynamodb.Attribute(name="game_id", type=dynamodb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Create the DynamoDB user table
        userTable = dynamodb.Table(
            self,
            "UserTable",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Create the DynamoDB words table
        wordTable = dynamodb.Table(
            self,
            "WordTable",
            partition_key=dynamodb.Attribute(name="word_length", type=dynamodb.AttributeType.NUMBER),
            sort_key=dynamodb.Attribute(name="word", type=dynamodb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Output the table names
        self.user_table_name_output = core.CfnOutput(self, 'UserTableName', value=userTable.table_name)
        self.game_table_name_output = core.CfnOutput(self, 'GameTableName', value=gameTable.table_name)
        self.word_table_name_output = core.CfnOutput(self, 'WordTableName', value=wordTable.table_name)

        # # Define a custom IAM policy for CloudWatch Logs access
        # cloudwatch_policy = iam.PolicyStatement(
        #     actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        #     resources=["arn:aws:logs:*:*:*"]
        # )

        # lambda_role = iam.Role(
        #     self,
        #     "CDKLambdaRole",
        #     assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        #     role_name="CDKLambdaRole"
        # )

        # lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))
        # lambda_role.add_to_policy(cloudwatch_policy)

        # # Create the Lambda function for creating a user    
        # create_user_lambda = _lambda.Function(
        #     self, 'CreateUser',
        #     runtime=_lambda.Runtime.PYTHON_3_7,
        #     code=_lambda.Code.from_asset('lambda'),
        #     handler='createUser.handler',
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )
        

        # # Create the Lambda function for creating a game
        # create_game_lambda = _lambda.Function(
        #     self,
        #     "CreateGameLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="createGame.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "GAME_TABLE": gameTable.table_name,
        #         "WORD_TABLE": wordTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )        

        # # Create the Lambda function for deleting a game
        # delete_game_lambda = _lambda.Function(
        #     self,
        #     "DeleteGameLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="deleteGame.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "GAME_TABLE": gameTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )
        
        # # Create the Lambda function for getting a game
        # get_game_lambda = _lambda.Function(
        #     self,
        #     "GetGameLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="getGame.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "GAME_TABLE": gameTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )
        
        # # Create the Lambda function for getting a user
        # get_user_lambda = _lambda.Function(
        #     self,
        #     "GetUserLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="getUser.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "GAME_TABLE": gameTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )
        
        # # Create the Lambda function for making a guess
        # guess_lambda = _lambda.Function(
        #     self,
        #     "GuessLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="guess.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "USER_TABLE": userTable.table_name,
        #         "GAME_TABLE": gameTable.table_name,
        #         "WORD_TABLE": wordTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )

        # # Create the Lambda function for creating a game
        # populate_words_lambda = _lambda.Function(
        #     self,
        #     "PopulateWordsLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler="populateWords.handler",
        #     code=_lambda.Code.from_asset("lambda"),
        #     environment={
        #         "WORD_TABLE": wordTable.table_name,
        #         "REGION": self.region
        #     },
        #     role=lambda_role
        # )        

        # # Create the Lambda function for getting a game
        # api = apigw.RestApi(
        #     self,
        #     "CdkProjectAPI",
        #     rest_api_name="CdkProject API",
        #     description="API for CdkProject",
        #     deploy_options={
        #         "stage_name": "v1"
        #     },
        #     endpoint_types=[apigw.EndpointType.REGIONAL]
        # )

        #  # Create the `/words` resource
        # words_resource = api.root.add_resource("words")

        # # Add a POST method to the `/words` resource and connect it to the create populateWords Lambda function
        # populate_words_integration = apigw.LambdaIntegration(populate_words_lambda)
        # words_resource.add_method("POST", populate_words_integration)

        #  # Create the `/users` resource
        # users_resource = api.root.add_resource("users")

        # # Add a POST method to the `/users` resource and connect it to the create user Lambda function
        # create_user_integration = apigw.LambdaIntegration(create_user_lambda)
        # users_resource.add_method("POST", create_user_integration)

        # # Create the `/users/{user_id} resource
        # user_resource = users_resource.add_resource("{user_id}")

        # # Add a GET method to the `/users/{user_id}/games/{game_id}` resource and connect it to the delete game Lambda function
        # get_user_integration = apigw.LambdaIntegration(get_user_lambda)
        # user_resource.add_method("GET", get_user_integration)

        # # Create the `/users/{user_id}/games` resource
        # users_games_resource = user_resource.add_resource("games")

        # # Add a POST method to the `/users/{user_id}/games` resource and connect it to the create game Lambda function
        # create_game_integration = apigw.LambdaIntegration(create_game_lambda)
        # users_games_resource.add_method("POST", create_game_integration)

        # # Create the `/users/{user_id}/games/{game_id}` resource
        # games_resource = users_games_resource.add_resource("{game_id}")

        # # Add a DELETE method to the `/users/{user_id}/games/{game_id}` resource and connect it to the delete game Lambda function
        # delete_game_integration = apigw.LambdaIntegration(delete_game_lambda)
        # games_resource.add_method("DELETE", delete_game_integration)

        # # Add a GET method to the `/users/{user_id}/games/{game_id}` resource and connect it to the delete game Lambda function
        # get_game_integration = apigw.LambdaIntegration(get_game_lambda)
        # games_resource.add_method("GET", get_game_integration)

        # # Create the `/users/{user_id}/games/{game_id}/guess` resource
        # guess_resource = games_resource.add_resource("guess")

        # # Add a POST method to the `/users/{user_id}/games/{game_id}/guess` resource and connect it to the guess Lambda function
        # guess_integration = apigw.LambdaIntegration(guess_lambda)
        # guess_resource.add_method("POST", guess_integration)
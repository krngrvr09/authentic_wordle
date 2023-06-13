from constructs import Construct
import aws_cdk as core
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
)


class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, table_names: dict,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        user_table_name = table_names['user']
        game_table_name = table_names['game']
        word_table_name = table_names['word']

        
        # Define a custom IAM policy for CloudWatch Logs access
        cloudwatch_policy = iam.PolicyStatement(
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            resources=["arn:aws:logs:*:*:*"]
        )

        # Create the IAM role for the Lambda function
        lambda_role = iam.Role(
            self,
            "CDKLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="CDKLambdaRole"
        )

        # Attach the custom policy for CloudWatch Logs access and DynamoDB access
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))
        lambda_role.add_to_policy(cloudwatch_policy)

        # Create the Lambda function for getting home page    
        get_home_lambda = _lambda.Function(
            self, 'GetHome',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='getHome.handler',
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )

        # Create the Lambda function for creating a user    
        create_user_lambda = _lambda.Function(
            self, 'CreateUser',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='createUser.handler',
            environment={
                "USER_TABLE": user_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )
        

        # Create the Lambda function for creating a game
        create_game_lambda = _lambda.Function(
            self,
            "CreateGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="createGame.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "WORD_TABLE": word_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )        

        # Create the Lambda function for deleting a game
        delete_game_lambda = _lambda.Function(
            self,
            "DeleteGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="deleteGame.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )
        
        # Create the Lambda function for getting a game
        get_game_lambda = _lambda.Function(
            self,
            "GetGameLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="getGame.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )
        
        # Create the Lambda function for getting a user
        get_user_lambda = _lambda.Function(
            self,
            "GetUserLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="getUser.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )
        
        # Create the Lambda function for making a guess
        guess_lambda = _lambda.Function(
            self,
            "GuessLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="guess.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "USER_TABLE": user_table_name,
                "GAME_TABLE": game_table_name,
                "WORD_TABLE": word_table_name,
                "REGION": self.region
            },
            role=lambda_role
        )

        # Create the Lambda function for populating words
        populate_words_lambda = _lambda.Function(
            self,
            "PopulateWordsLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="populateWords.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "WORD_TABLE": word_table_name,
                "REGION": self.region
            },
            role=lambda_role,
            timeout=core.Duration.seconds(30)
        )

        self.get_home_lambda = get_home_lambda
        self.create_user_lambda = create_user_lambda
        self.create_game_lambda = create_game_lambda
        self.delete_game_lambda = delete_game_lambda
        self.get_game_lambda = get_game_lambda
        self.get_user_lambda = get_user_lambda
        self.guess_lambda = guess_lambda
        self.populate_words_lambda = populate_words_lambda

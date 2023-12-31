from constructs import Construct
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
)


class APIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, lambda_functions: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the Lambda functions from the LambdaStack
        get_home_lambda = lambda_functions['get_home']
        create_user_lambda = lambda_functions['create_user']
        create_game_lambda = lambda_functions['create_game']
        get_game_lambda = lambda_functions['get_game']
        get_user_lambda = lambda_functions['get_user']
        delete_game_lambda = lambda_functions['delete_game']
        guess_lambda = lambda_functions['guess']
        populate_words_lambda = lambda_functions['populate_words']


        # Create the API Gateway
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


        # Add a GET method to the `/` resource and connect it to the getHome Lambda function
        get_home_integration = apigw.LambdaIntegration(get_home_lambda)
        api.root.add_method("GET", get_home_integration)
        
        # Create the `/words` resource
        words_resource = api.root.add_resource("words")

        # Add a POST method to the `/words` resource and connect it to the create populateWords Lambda function
        populate_words_integration = apigw.LambdaIntegration(populate_words_lambda)
        words_resource.add_method("POST", populate_words_integration)

         # Create the `/users` resource
        users_resource = api.root.add_resource("users")

        # Add a POST method to the `/users` resource and connect it to the createUser Lambda function
        create_user_integration = apigw.LambdaIntegration(create_user_lambda)
        users_resource.add_method("POST", create_user_integration)

        # Create the `/users/{user_id} resource
        user_resource = users_resource.add_resource("{user_id}")

        # Add a GET method to the `/users/{user_id}` resource and connect it to the getUser Lambda function
        get_user_integration = apigw.LambdaIntegration(get_user_lambda)
        user_resource.add_method("GET", get_user_integration)

        # Create the `/users/{user_id}/games` resource
        users_games_resource = user_resource.add_resource("games")

        # Add a POST method to the `/users/{user_id}/games` resource and connect it to the createGame Lambda function
        create_game_integration = apigw.LambdaIntegration(create_game_lambda)
        users_games_resource.add_method("POST", create_game_integration)

        # Create the `/users/{user_id}/games/{game_id}` resource
        games_resource = users_games_resource.add_resource("{game_id}")

        # Add a DELETE method to the `/users/{user_id}/games/{game_id}` resource and connect it to the deleteGame Lambda function
        delete_game_integration = apigw.LambdaIntegration(delete_game_lambda)
        games_resource.add_method("DELETE", delete_game_integration)

        # Add a GET method to the `/users/{user_id}/games/{game_id}` resource and connect it to the getGame Lambda function
        get_game_integration = apigw.LambdaIntegration(get_game_lambda)
        games_resource.add_method("GET", get_game_integration)

        # Create the `/users/{user_id}/games/{game_id}/guess` resource
        guess_resource = games_resource.add_resource("guess")

        # Add a POST method to the `/users/{user_id}/games/{game_id}/guess` resource and connect it to the guess Lambda function
        guess_integration = apigw.LambdaIntegration(guess_lambda)
        guess_resource.add_method("POST", guess_integration)
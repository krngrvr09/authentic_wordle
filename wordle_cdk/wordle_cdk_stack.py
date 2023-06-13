from constructs import Construct
from aws_cdk import Stack
from wordle_cdk.db_stack import DBStack
from wordle_cdk.lambda_stack import LambdaStack
from wordle_cdk.api_stack import APIStack

class WordleCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the DynamoDB stack
        dynamodb_stack = DBStack(self, 'DynamoDBStack')

        user_table_name = dynamodb_stack.user_table_name_output.value
        game_table_name = dynamodb_stack.game_table_name_output.value
        word_table_name = dynamodb_stack.word_table_name_output.value

        
        # Create the Lambda stack
        lambda_stack = LambdaStack(self, 'LambdaStack', table_names={
            'user': user_table_name,
            'game': game_table_name,
            'word': word_table_name
        })

        api_stack = APIStack(self, 'APIStack', lambda_functions={
            'get_home': lambda_stack.get_home_lambda,
            'create_user': lambda_stack.create_user_lambda,
            'create_game': lambda_stack.create_game_lambda,
            'get_game': lambda_stack.get_game_lambda,
            'get_user': lambda_stack.get_user_lambda,
            'delete_game': lambda_stack.delete_game_lambda,
            'guess': lambda_stack.guess_lambda,
            'populate_words': lambda_stack.populate_words_lambda
        })

        
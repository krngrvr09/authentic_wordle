from constructs import Construct
import aws_cdk as core
from aws_cdk import (
    Stack,
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

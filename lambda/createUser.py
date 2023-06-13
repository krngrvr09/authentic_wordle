import json
import boto3
import uuid
import os
from wordle_utils import _http_response, _putItem, ResponseStatus


def handler(event, context):
        
        dynamodb = boto3.resource('dynamodb')
        userTable = dynamodb.Table(os.environ['USER_TABLE'])
        
        user_id = str(uuid.uuid4())
        new_item = {
            "user_id": user_id,
            "game_id": ""
        }

        reply = _putItem(userTable, new_item)
        if not reply["success"]:
            return _http_response( reply["status"], reply["response"])
        
        return _http_response(ResponseStatus.CREATED, reply["response"])
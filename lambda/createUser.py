import json
import boto3
import uuid
import os
from enum import Enum


class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    INTERNAL_ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORISED = 403


def _http_response(response_status, response_message):
    return {
                'statusCode': response_status.value,
                'body': json.dumps({"message":response_message, "status": response_status.name})
            }


def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to create user."
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while creating a new user."
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


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
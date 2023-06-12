import json
import boto3
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


def _getItem(table, pk_name, pk_value, sk_name=None, sk_value=None):
    key = {
        pk_name: pk_value,
    }
    if sk_name is not None:
        key[sk_name] = sk_value
    
    try:
        itemObject = table.get_item(Key=key)
        if "Item" in itemObject:
            return {"success":True, "response":itemObject["Item"]}
        else:
            error_message = "{} with id: {} not found.".format(pk_name, str(pk_value))
            return {"success":False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from dynamoDB".format(pk_name, str(pk_value))
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to delete game."
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while deleting game."
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _deleteItem(table, item_id_name, item_id):
    try:
        response = table.delete_item(
                Key={
                    item_id_name: item_id
                }
            )
            # Check the response status
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Item deleted successfully.')
            return {"success": True, "response": "Item deleted successfully."}
        else:
            print('Error deleting item:', item_id)
            return {"success": False, "response": "Error deleting item: {}".format(item_id), "status": ResponseStatus.INTERNAL_ERROR}
            
    except Exception as e:
        print(e)
        print("Exception deleting game from : "+item_id)
        return {"success": False, "response": "Exception deleting game from : {}".format(item_id), "status": ResponseStatus.INTERNAL_ERROR}


def handler(event, context):
    
    if "pathParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters")
    
    pathParams = event["pathParameters"]
    if "user_id" not in pathParams or "game_id" not in pathParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters")
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    game_id = pathParams["game_id"]
    user_id = pathParams["user_id"]

    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game")

    reply = _deleteItem(gameTable, "game_id", game_id)

    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])

    user["game_id"] = ""
    reply = _putItem(userTable, user)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    return _http_response(ResponseStatus.OK, "Game deleted successfully")
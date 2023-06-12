import json
import boto3
import os
from enum import Enum
from urllib.parse import urljoin

class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    INTERNAL_ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORISED = 403
    TEMPORARY_REDIRECT = 302


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


def handler(event, context):
    if "queryStringParameters" not in event:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    queryParams = event["queryStringParameters"]
    if queryParams is None or "user_id" not in queryParams or "game_id" not in queryParams:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    """
    if user not present:
        return error. malformed request
    if game not present:
        return error. malformed request
    if game present but not in user:
        return error. not authorised
    
    redirect to game.
    """
    print("1")
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    print("2")
    game_id = queryParams["game_id"]
    user_id = queryParams["user_id"]

    print("3")
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    user = reply["response"]
    user_game_id = user["game_id"]
    print("4")
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game")

    print("5")
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    print("6")
    request_path = event['path']
    redirect_path = "/v1/users/{}/games/{}".format(user_id, game_id)  # Replace with your desired redirect path
    redirect_url = urljoin(request_path, redirect_path)
    # Set the redirect response
    print("7")
    # return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    headers = {
        'Access-Control-Allow-Origin': '*',  # Replace * with the appropriate origin
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET',  # Adjust the allowed methods as needed
        'Location': redirect_url,
    }
    response = {
        'statusCode': 302,  # Use the appropriate status code (e.g., 302 for temporary redirect)
        'headers': headers,
        'body': 'test',
    }
    print("8")
    return response
    return _http_response(ResponseStatus.TEMPORARY_REDIRECT, reply["response"])
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])

    return _http_response(ResponseStatus.OK, reply["response"])
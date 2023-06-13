import json
import boto3
import os
from enum import Enum
from urllib.parse import urljoin

# HTTP response status codes
class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    INTERNAL_ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORISED = 403
    TEMPORARY_REDIRECT = 302


def _http_response(response_status, response_message):
    """
    Builds a HTTP response object using the response status and message provided.

    Args:
        response_status (ResponseStatus): The HTTP response status code
        response_message (str): The message to be returned in the HTTP response body
    
    Returns:
        dict: The HTTP response object
    """
    return {
                'statusCode': response_status.value,
                'body': json.dumps({"message":response_message, "status": response_status.name})
            }


def _getItem(table, pk_name, pk_value, sk_name=None, sk_value=None):
    """
    Retrieves an item from the provided table using the provided primary key and sort key (if provided).

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        pk_name (str): The name of the primary key
        pk_value (str/int): The value of the primary key
        sk_name (str, optional): The name of the sort key. Defaults to None.
        sk_value (str/int, optional): The value of the sort key. Defaults to None.
    
    Returns:
        dict: The item retrieved from the table as a dictionary object if successful, otherwise a dictionary object containing an error message and status code
    """
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
            error_message = "{} with id: {} not found in {}".format(pk_name, str(pk_value), table.table_name)
            return {"success":False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from {}".format(pk_name, str(pk_value), table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def handler(event, context):

    # If no query parameters are provided, return the home page
    if "queryStringParameters" not in event:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    queryParams = event["queryStringParameters"]
    if queryParams is None or "user_id" not in queryParams or "game_id" not in queryParams:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    game_id = queryParams["game_id"]
    user_id = queryParams["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # Check if user is allowed to access this game
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game")

    # Check if game exists
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # Redirect to game page
    request_path = event['path']
    redirect_path = "/v1/users/{}/games/{}".format(user_id, game_id)
    redirect_url = urljoin(request_path, redirect_path)
    
    #TODO: CHeck if this works, if so add it to _http wrapper
    headers = {
        # 'Access-Control-Allow-Origin': '*',  # Replace * with the appropriate origin
        # 'Access-Control-Allow-Headers': 'Content-Type',
        # 'Access-Control-Allow-Methods': 'OPTIONS, POST, GET',  # Adjust the allowed methods as needed
        'Location': redirect_url,
    }
    response = {
        'statusCode': 302,
        'headers': headers,
        'body': 'test',
    }
    return response
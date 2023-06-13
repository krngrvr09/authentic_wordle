import json
import boto3
import os
from enum import Enum

# HTTP response status codes
class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    INTERNAL_ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORISED = 403


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


def _putItem(table, item):
    """
    Inserts a new item into the provided table.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        item (dict): The item to be inserted into the table
    
    Returns:
        dict: A dictionary object of the item inserted into the table if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to write item to {}".format(table.table_name)
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while writing item to {}".format(table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _deleteItem(table, item_id_name, item_id):
    """
    Deletes an item from the provided table using the provided primary key.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        item_id_name (str): The name of the primary key
        item_id (str/int): The value of the primary key
    
    Returns:
        dict: A dictionary object containing a success message if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        response = table.delete_item(
                Key={
                    item_id_name: item_id
                }
            )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": "Item deleted successfully."}
        else:
            return {"success": False, "response": "Error deleting item: {} in {}".format(str(item_id), table.table_name), "status": ResponseStatus.INTERNAL_ERROR}
            
    except Exception as e:
        print(e)
        return {"success": False, "response": "Exception deleting item with id: {} from {}".format(str(item_id), table.table_name), "status": ResponseStatus.INTERNAL_ERROR}


def handler(event, context):
    
    # Validate request and request parameters
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

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # Check if user is authorized to delete this game
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game")

    # delete game
    reply = _deleteItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])

    # update user
    user["game_id"] = ""
    reply = _putItem(userTable, user)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # return success
    return _http_response(ResponseStatus.OK, "Game deleted successfully")
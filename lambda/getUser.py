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
            return {"success":False, "response": error_message, "status": ResponseStatus.NOT_FOUND}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from {}".format(pk_name, str(pk_value), table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def handler(event, context):
    
    # validate request and request parameters
    if "pathParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters")
    
    pathParams = event["pathParameters"]
    if "user_id" not in pathParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters")
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])

    user_id = event["pathParameters"]["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])

    # Return user
    return _http_response(ResponseStatus.OK, reply["response"])
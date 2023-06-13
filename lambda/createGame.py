import json
import boto3
import uuid
import os
from enum import Enum

# HTTP response status codes
class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    NOT_AUTHORISED = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


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
        error_message = "Exception while getting {}: {} from {}}".format(pk_name, str(pk_value), table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _getRandomItem(table, partition_key, partition_key_value):
    #TODO: CHeck if this works, if not dont include in this function
    print(table.table_name)
    """
    Retrieves a random item from the provided table. Performs a scan
    on the table using partition_key and partition_key_value to filter
    the results. A random item is then selected from the results.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        partition_key (str): The name of the partition key
        partition_key_value (str/int): The value of the partition key
    
    Returns:
        dict: The item retrieved from the table as a dictionary object if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        keyConditionExpression = "{} = :partition_key_value".format(partition_key)
        response = table.query(
            KeyConditionExpression=keyConditionExpression,
            ExpressionAttributeValues={':partition_key_value': partition_key_value}
        )
        items = response['Items']
        n = len(items)
        if n == 0:
            return {"success":False, "response": "No items found in {}".format(table.table_name), "status": ResponseStatus.INTERNAL_ERROR}
        else:
            random_int = uuid.uuid4().int
            idx = random_int % n
            return {"success":True, "response": items[idx]}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from {}".format(partition_key, str(partition_key_value), table.table_name)
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

# check is string represents an integer
def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def handler(event, context):
    # Validate request and request parameters
    if "queryStringParameters" not in event or "pathParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters")
    
    pathParams = event["pathParameters"]
    queryParams = event["queryStringParameters"]
    if "user_id" not in pathParams or "hard_mode" not in queryParams or "word_length" not in queryParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters")
    
    user_id = pathParams["user_id"]
    word_length = queryParams["word_length"]
    hard_mode = queryParams["hard_mode"]
    if(not isInt(word_length) or int(word_length) < 5 or int(word_length) > 8):
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Word length must be and integer between 5 and 8")
    if(hard_mode != "1" and hard_mode != "0"):
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Hard mode must be 1 or 0")
    
    dynamodb = boto3.resource('dynamodb')
    userTable = dynamodb.Table(os.environ['USER_TABLE'])
    gameTable = dynamodb.Table(os.environ['GAME_TABLE'])
    wordTable = dynamodb.Table(os.environ['WORD_TABLE'])

    # Check if user exists
    result = _getItem(userTable, "user_id", user_id)
    if not result["success"]:
        return _http_response(result["status"], result["response"])
    userObject = result["response"]
    
    # Generate game id
    game_id = str(uuid.uuid4())
    
    # Get random word
    result = _getRandomItem(wordTable, "word_length", int(word_length))
    if not result["success"]:
        return _http_response(result["status"], result["response"])
    word = result["response"]["word"]
    
    # Create game object
    attempts_left = int(word_length)+1
    gameObject = {
        "game_id": game_id,
        "hard_mode": hard_mode,
        "attempts_left": str(attempts_left),
        "word_length": word_length,
        "word": word,
        "status": "IN_PROGRESS",
        "guesses": [],
        "responses": []
    }

    # Update user object and write to DB
    userObject["game_id"] = game_id
    result = _putItem(userTable, userObject)
    # return _http_response(result["response_code"])
    if not result["success"]:
        return _http_response(result["status"], result["response"])
    

    # Write game object to DB
    result = _putItem(gameTable, gameObject)
    if not result["success"]:
        return _http_response(result["status"], result["response"])

    # Return game object
    return _http_response(ResponseStatus.CREATED, result["response"])
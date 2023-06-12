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
            error_message = "{} with id: {} not found".format(pk_name, pk_value)
            return {"success":False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from dynamoDB".format(pk_name, pk_value)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _getRandomItem(table, partition_key, partition_key_value):
    try:
        keyConditionExpression = partition_key+" = :partition_key_value"
        response = table.query(
            KeyConditionExpression=keyConditionExpression,
            ExpressionAttributeValues={':partition_key_value': partition_key_value}
        )
        items = response['Items']
        n = len(items)
        if n == 0:
            return {"success":False, "response": "No items found", "status": ResponseStatus.INTERNAL_ERROR}
        else:
            random_int = uuid.uuid4().int
            idx = random_int % n
            return {"success":True, "response": items[idx]}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from dynamoDB".format(partition_key, str(partition_key_value))
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to create game."
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while creating a new game."
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}



def handler(event, context):
            
    if "queryStringParameters" not in event or "pathParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters")
    
    pathParams = event["pathParameters"]
    queryParams = event["queryStringParameters"]
    if "user_id" not in pathParams or "hard_mode" not in queryParams or "word_length" not in queryParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters")
    
    user_id = pathParams["user_id"]
    word_length = queryParams["word_length"]
    hard_mode = queryParams["hard_mode"]
    if(int(word_length) < 5 or int(word_length) > 8):
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Word length must be between 5 and 8")
    if(hard_mode != "1" and hard_mode != "0"):
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Hard mode must be 1 or 0")
    attempts_left = int(word_length)+1
    dynamodb = boto3.resource('dynamodb')
    userTable = dynamodb.Table(os.environ['USER_TABLE'])
    gameTable = dynamodb.Table(os.environ['GAME_TABLE'])
    wordTable = dynamodb.Table(os.environ['WORD_TABLE'])

    result = _getItem(userTable, "user_id", user_id)
    if not result["success"]:
        print("2")
        return _http_response(result["status"], result["response"])
    userObject = result["response"]
    
    game_id = str(uuid.uuid4())
    
    result = _getRandomItem(wordTable, "word_length", int(word_length))
    if not result["success"]:
        return _http_response(result["status"], result["response"])
    print(result)
    word = result["response"]["word"]

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

    userObject["game_id"] = game_id
    result = _putItem(userTable, userObject)
    # return _http_response(result["response_code"])
    if not result["success"]:
        return _http_response(result["status"], result["response"])
    

    result = _putItem(gameTable, gameObject)
    if not result["success"]:
        print("1")
        return _http_response(result["status"], result["response"])

    return _http_response(ResponseStatus.CREATED, result["response"])
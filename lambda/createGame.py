import json
import boto3
import uuid
import os

def _http_response(response_code, response_message):
    return {
                'statusCode': response_code,
                'body': json.dumps({"message":response_message})
            }

def _getItem(table, item_id_name, item_id):
    try:
        itemObject = table.get_item(Key={item_id_name: item_id})
        if "Item" in itemObject:
            return {"success":True, "response":itemObject["Item"]}
        else:
            error_message = item_id_name+" with id: "+item_id+" not found"
            return {"success":False, "response": error_message, "response_code": 404}
    except Exception as e:
        print(e)
        error_message = "Exception while getting "+item_id_name+": "+item_id+" from DynamoDB"
        return {"success": False, "response": error_message, "response_code": 500}

def _putItem(table, item):
    try:
        try:
            tmp = json.dumps(item)
            print("putting item into table")
            print(tmp)
        except Exception as e:
            return {"success": False, "response": "Error serializing json", "response_code": 500}
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to create new game."
            return {"success": False, "response": error_message, "response_code": 422}
    except Exception as e:
        print(e)
        error_message = "An exception occured while creating a new game."
        return {"success": False, "response": error_message, "response_code": 500}


def handler(event, context):
            
    if "queryStringParameters" not in event or "pathParameters" not in event or "user_id" not in event["pathParameters"] or "hard_mode" not in event["queryStringParameters"] or "word_length" not in event["queryStringParameters"]:
        # give error malformed request
        return _http_response(400, "Malformed Request")
    else:
        user_id = event["pathParameters"]["user_id"]
        word_length = event["queryStringParameters"]["word_length"]
        attempts_left = int(word_length)+1
        hard_mode = event["queryStringParameters"]["hard_mode"]
        dynamodb = boto3.resource('dynamodb')
        userTable = dynamodb.Table(os.environ['USER_TABLE'])
        gameTable = dynamodb.Table(os.environ['GAME_TABLE'])
        
        result = _getItem(userTable, "user_id", user_id)
        if not result["success"]:
            print("2")
            return _http_response(result["response_code"], result["response"])
        userObject = result["response"]
        
        game_id = str(uuid.uuid4())
        word="hello"
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

        result = _putItem(gameTable, gameObject)
        if not result["success"]:
            print("1")
            return _http_response(result["response_code"], result["response"])

        
        userObject["game_id"] = game_id
        print("mapping userid to gameid")
        print(userObject)
        result = _putItem(userTable, userObject)
        print(result)
        # return _http_response(result["response_code"])
        if not result["success"]:
            return _http_response(result["response_code"], result["response"])
        
        return _http_response(201, result["response"])
    
    
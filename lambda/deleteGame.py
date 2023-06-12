import json
import boto3
import os

"""
TODO:
- Use string formatting
- write tests?
"""
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
            return {"success": False, "response": "Error deleting item: "+item_id, "response_code": 500}
            
    except Exception as e:
        print(e)
        print("Exception deleting game from : "+game_id)
        return {"success": False, "response": "Exception deleting game from : "+item_id, "response_code": 500}

def handler(event, context):
    if "pathParameters" not in event or "queryStringParameters" not in event or "user_id" not in event["pathParameters"] or "game_id" not in event["pathParameters"]:
        return _http_response(400, "Invalid parameters")
    else:
        dynamoClient = boto3.resource("dynamodb")
        userTable = dynamoClient.Table(os.environ["USER_TABLE"])
        gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

        game_id = event["pathParameters"]["game_id"]
        user_id = event["pathParameters"]["user_id"]

        reply = _getItem(userTable, "user_id", user_id)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        user = reply["response"]
        user_game_id = user["game_id"]
        if(user_game_id!=game_id):
            return _http_response(403, "This user is not allowed to access this game id")

        reply = _deleteItem(gameTable, "game_id", game_id)

        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])

        user["game_id"] = ""
        reply = _putItem(userTable, user)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        
        return _http_response(200, "Game deleted successfully")
        

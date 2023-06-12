import json
import boto3
import uuid
import os

def _http_response(response_code, response_message):
    return {
                'statusCode': response_code,
                'body': json.dumps({"message":response_message})
            }

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
        dynamodb = boto3.resource('dynamodb')
        userTable = dynamodb.Table(os.environ['USER_TABLE'])
        user_id = str(uuid.uuid4())
        new_item = {
            "user_id": user_id,
            "game_id": ""
        }

        reply = _putItem(userTable, new_item)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        return _http_response(201,reply["response"])
    
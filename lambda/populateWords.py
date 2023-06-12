import json
import boto3
import uuid
import os
# import requests
import random

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
    # word_site = "https://www.mit.edu/~ecprice/wordlist.10000"

    # response = requests.get(word_site)
    # words = response.content.splitlines()
    # words = [i for i in words if len(i)>=5 or len(i)<=8]
    words = ["Apple","North","March","Snake","Quest","Banana","Purple","Winter","Sphere","Spirit","Journey","Diamond","Weather","Wisdom","Bicycle","Mountain","Elephant","Sunshine","Festival","Musician"]

    random.Random(4).shuffle(words)

    dynamodb = boto3.resource('dynamodb')
    wordTable = dynamodb.Table(os.environ['WORD_TABLE'])
    for word in words:
        wordObject = {
            "word_length": len(word),
            "word": word.lower(),
        }
        result = _putItem(wordTable, wordObject)
        if not result["success"]:
            return _http_response(result["response_code"], result["response"])

    return _http_response(200, "Successfully populated words table")
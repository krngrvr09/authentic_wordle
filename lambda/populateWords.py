import json
import boto3
import uuid
import os
# import requests
import random
from enum import Enum


class ResponseStatus(Enum):
    OK = 200
    CREATED = 201
    MALFORMED_REQUEST = 400
    INTERNAL_ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORISED = 403
    INVALID_GUESS = 400
    ATTEMPTS_EXCEEDED = 400
    GAME_OVER = 400


def _http_response(response_status, response_message):
    return {
                'statusCode': response_status.value,
                'body': json.dumps({"message":response_message, "status": response_status.name})
            }


def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to populate words table."
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while populating words table."
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


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
            return _http_response(result["status"], result["response"])

    return _http_response(ResponseStatus.CREATED, "Successfully populated words table")
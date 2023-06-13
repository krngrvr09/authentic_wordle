import json
import boto3
import uuid
import os
from enum import Enum
from wordle_utils import _http_response, _getItem, _putItem, _getRandomItem, ResponseStatus

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
    
    # Check if user already has an active game
    result = _getItem(gameTable, "game_id", userObject["game_id"])
    if result["success"] and result["response"]["status"] == "IN_PROGRESS":
        return _http_response(ResponseStatus.NOT_AUTHORISED, "User already has an active game, cannot create a new game")


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
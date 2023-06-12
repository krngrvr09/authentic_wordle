import json
import boto3
import os
from ast import literal_eval
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


def serialize(word):
        sword = [None]*26
        for i in range(26):
            sword[i] = []
        cidx=0
        for c in word:
            idx = ord(c) - ord('a')
            sword[idx].append(cidx)
            cidx+=1
        return sword


def valid(wordTable, word, word_length, hard_mode, guesses, responses):
        if len(word) != word_length:
            return {"success": False, "message": "Invalid input length"}
        for c in word:
            if not c.isalpha():
                return {"success": False, "message": "Invalid input character"}
        reply = _getItem(wordTable, "word_length", int(word_length), "word", word)
        
        if not reply["success"]:
            return {"success": False, "message": "Word not found in Wordle Dictionary"}
        if hard_mode=="1" and len(guesses)>0:
            response = literal_eval(responses[-1])
            guess = guesses[-1]
            for idx in range(len(word)):
                print(response[idx], " ", word[idx], " ", guess[idx])
                if response[idx]=="GREEN" and word[idx]!=guess[idx]:
                    return {"success":False, "message": "Correct letters not included in the guess under hard mode."}
        return {"success": True}


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


def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to create update game with the guess."
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while updating game with the guess."
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR}


def getGuessResponse(guess, target):
        res=[]
        idx=0
        for c in guess:
            if c not in target:
                res.append("GREY")
            elif target[idx]==c:
                res.append("GREEN")
            else:
                res.append("YELLOW")
            idx+=1
        return res


def handler(event, context):
    
    if "pathParameters" not in event or "queryStringParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters")

    pathParams = event["pathParameters"]
    queryParams = event["queryStringParameters"]
    if "user_id" not in pathParams or "game_id" not in pathParams or "guess" not in queryParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters")
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ['USER_TABLE'])
    gameTable = dynamoClient.Table(os.environ['GAME_TABLE'])
    wordTable = dynamoClient.Table(os.environ['WORD_TABLE'])

    user_id = pathParams["user_id"]
    game_id = pathParams["game_id"]
    guess = queryParams["guess"]
    
    # check mapping between game id and user id
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    user = reply["response"]
    if(user["game_id"]!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game id")
    
    # check if game exists
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    game = reply["response"]

    # check if game is over
    attempts_left = int(game["attempts_left"])
    if game["status"]!="IN_PROGRESS" or attempts_left<=0:
        return _http_response(ResponseStatus.ATTEMPTS_EXCEEDED, game)

    # validate guess
    word_length = int(game["word_length"])
    result = valid(wordTable, guess, word_length, game["hard_mode"], game["guesses"], game["responses"])
    if not result["success"]:
        return _http_response(ResponseStatus.INVALID_GUESS, result["message"])
    

    guessResponse = getGuessResponse(guess, game["word"])
    attempts_left -= 1
    if guessResponse == ["GREEN" for c in game["word"]]:
        game["status"] = "WON"
    elif attempts_left == 0:
        game["status"] = "LOST"
    game["guesses"].append(guess)
    game["responses"].append(str(guessResponse))
    game["attempts_left"]=str(attempts_left)
    reply = _putItem(gameTable, game)
    if not reply["success"]:
        return _http_response(reply["status"], reply["response"])
    return _http_response(ResponseStatus.CREATED, reply["response"])

import json
import boto3
import os
from ast import literal_eval
from enum import Enum, EnumMeta
from wordle_utils import _http_response, _getItem, _putItem, ResponseStatus, ApplicationStatus, GREEN, GREY, YELLOW, IN_PROGRESS, WON, LOST


def valid(wordTable, word, word_length, hard_mode, guesses, responses):
    """
    Verifies that the following properties are true:
    1. Word is of the right length
    2. Word contains only alphabets
    3. Word is present in the Wordle Dictionary
    4. If hard mode is enabled, the guess contains all the correct letters in the right position from the previous guess

    Args:
        wordTable (DynamoDB.Table): The DynamoDB table object
        word (str): The guess word to be validated
        word_length (int): The length of the word
        hard_mode (str): The hard mode flag
        guesses (list): The list of guesses made so far. eg. ["quest", "hello"]
        responses (list): The list of responses for the guesses made so far. eg. ["['GREEN', 'GREY', 'GREEN', 'YELLOW', 'GREEN']", "['GREY', 'GREY', 'GREY', 'YELLOW', 'GREEN']"]
    
    Returns:
        dict: A dictionary object containing a success flag and a message
    """
    if len(word) != word_length:
        return {"success": False, "message": "Invalid input length"}
    
    for c in word:
        if not c.isalpha():
            return {"success": False, "message": "Invalid input character"}
    
    reply = _getItem(wordTable, "word_length", int(word_length), "word", word)
    if not reply["success"]:
        return {"success": False, "message": "Word not found in Wordle Dictionary"}
    
    if hard_mode=="1" and len(guesses)>0:
        response = literal_eval(responses[-1]) # Convert string to list ["GREEN", "YELLOW", ..]
        guess = guesses[-1] # "quest"
        for idx in range(len(word)):
            print(response[idx], " ", word[idx], " ", guess[idx])
            if response[idx]==GREEN and word[idx]!=guess[idx]:
                return {"success":False, "message": "Correct letters not included in the guess under hard mode."}
    
    return {"success": True}


def getGuessResponse(guess, target):
        """
        Converts a guess into a response based on the target word.
        eg. guess = "chime", target = "chirp" => response = ["GREEN", "GREEN", "GREEN", "GREY", "GREY"]

        Args:
            guess (str): The guess word
            target (str): The target word
        
        Returns:
            list: Response as a list of colours(str)
        """
        res=[]
        idx=0
        for c in guess:
            if c not in target:
                res.append(GREY)
            elif target[idx]==c:
                res.append(GREEN)
            else:
                res.append(YELLOW)
            idx+=1
        return res


def handler(event, context):
    
    # Validate the request and request parameters
    if "pathParameters" not in event or "queryStringParameters" not in event:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters", ApplicationStatus.MISSING_PARAMETERS)

    pathParams = event["pathParameters"]
    queryParams = event["queryStringParameters"]
    if "user_id" not in pathParams or "game_id" not in pathParams or "guess" not in queryParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters", ApplicationStatus.MISSING_PARAMETERS)
    
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
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    user = reply["response"]
    if(user["game_id"]!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game id", ApplicationStatus.NOT_AUTHORISED)
    
    # check if game exists
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    game = reply["response"]

    # check if game is over
    attempts_left = int(game["attempts_left"])
    if game["status"]!=IN_PROGRESS or attempts_left<=0:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, game, ApplicationStatus.GAME_OVER)

    # validate guess
    word_length = int(game["word_length"])
    result = valid(wordTable, guess, word_length, game["hard_mode"], game["guesses"], game["responses"])
    if not result["success"]:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, result["message"], ApplicationStatus.INPUT_ERROR)
    
    # Get a response for the guess and update the game
    guessResponse = getGuessResponse(guess, game["word"])
    attempts_left -= 1
    if guessResponse == [GREEN for c in game["word"]]:
        game["status"] = WON
    elif attempts_left == 0:
        game["status"] = LOST
    game["guesses"].append(guess)
    game["responses"].append(str(guessResponse))
    game["attempts_left"]=str(attempts_left)
    
    # Write the updated game to the database
    reply = _putItem(gameTable, game)
    if not reply["success"]:
        return _http_response(reply["status"], reply["response"], reply["application_status"])
    
    # Return the updated game
    return _http_response(ResponseStatus.CREATED, reply["response"], reply["application_status"])

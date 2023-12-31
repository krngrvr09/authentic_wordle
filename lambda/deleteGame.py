import json
import boto3
import os
from enum import Enum
from wordle_utils import _http_response, _getItem, _putItem, _deleteItem, ResponseStatus, ApplicationStatus

def handler(event, context):
    
    # Validate request and request parameters
    if "pathParameters" not in event or event["pathParameters"] is None:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters", ApplicationStatus.MISSING_PARAMETERS)
    
    pathParams = event["pathParameters"]
    if "user_id" not in pathParams or "game_id" not in pathParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters", ApplicationStatus.MISSING_PARAMETERS)
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    game_id = pathParams["game_id"]
    user_id = pathParams["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    
    # Check if user is authorized to delete this game
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game", ApplicationStatus.NOT_AUTHORISED)

    # delete game
    reply = _deleteItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])

    # update user
    user["game_id"] = ""
    reply = _putItem(userTable, user)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    
    # return success
    return _http_response(ResponseStatus.OK, "Game deleted successfully",ApplicationStatus.OK)
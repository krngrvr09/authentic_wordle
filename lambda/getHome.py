import json
import boto3
import os
from enum import Enum
from urllib.parse import urljoin
from wordle_utils import _http_response, _getItem, ResponseStatus, ApplicationStatus


def handler(event, context):

    # If no query parameters are provided, return the home page
    if "queryStringParameters" not in event or event["queryStringParameters"] is None:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page", ApplicationStatus.OK)
    
    queryParams = event["queryStringParameters"]
    if "user_id" not in queryParams or "game_id" not in queryParams:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page", ApplicationStatus.OK)
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    game_id = queryParams["game_id"]
    user_id = queryParams["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    
    # Check if user is allowed to access this game
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game", ApplicationStatus.NOT_AUTHORISED)

    # Check if game exists
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])
    
    # Redirect to game page
    request_path = event['path']
    redirect_path = "/v1/users/{}/games/{}".format(user_id, game_id)
    redirect_url = urljoin(request_path, redirect_path)
    
    headers = {
        'Location': redirect_url,
    }
    return _http_response(ResponseStatus.TEMPORARY_REDIRECT, "Redirecting to the game.", ApplicationStatus.OK, headers)

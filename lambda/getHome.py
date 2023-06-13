import json
import boto3
import os
from enum import Enum
from urllib.parse import urljoin
from wordle_utils import _http_response, _getItem, ResponseStatus


def handler(event, context):

    # If no query parameters are provided, return the home page
    if "queryStringParameters" not in event:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    queryParams = event["queryStringParameters"]
    if queryParams is None or "user_id" not in queryParams or "game_id" not in queryParams:
        return _http_response(ResponseStatus.OK, "Successfully retrieved home page")
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])
    gameTable = dynamoClient.Table(os.environ["GAME_TABLE"])

    game_id = queryParams["game_id"]
    user_id = queryParams["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # Check if user is allowed to access this game
    user = reply["response"]
    user_game_id = user["game_id"]
    if(user_game_id!=game_id):
        return _http_response(ResponseStatus.NOT_AUTHORISED, "This user is not allowed to access this game")

    # Check if game exists
    reply = _getItem(gameTable, "game_id", game_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"])
    
    # Redirect to game page
    request_path = event['path']
    redirect_path = "/v1/users/{}/games/{}".format(user_id, game_id)
    redirect_url = urljoin(request_path, redirect_path)
    
    #TODO: CHeck if this works, if so add it to _http wrapper
    headers = {
        # 'Access-Control-Allow-Origin': '*',  # Replace * with the appropriate origin
        # 'Access-Control-Allow-Headers': 'Content-Type',
        # 'Access-Control-Allow-Methods': 'OPTIONS, POST, GET',  # Adjust the allowed methods as needed
        'Location': redirect_url,
    }
    response = {
        'statusCode': 302,
        'headers': headers,
        'body': 'test',
    }
    return response
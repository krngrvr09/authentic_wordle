import json
import boto3
import os
from enum import Enum
from wordle_utils import _http_response, _getItem, ResponseStatus, ApplicationStatus


def handler(event, context):
    
    # validate request and request parameters
    if "pathParameters" not in event or event["pathParameters"] is None:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing URL parameters", ApplicationStatus.MISSING_PARAMETERS)
    
    pathParams = event["pathParameters"]
    if "user_id" not in pathParams:
        return _http_response(ResponseStatus.MALFORMED_REQUEST, "Missing required URL parameters", ApplicationStatus.MISSING_PARAMETERS)
    
    dynamoClient = boto3.resource("dynamodb")
    userTable = dynamoClient.Table(os.environ["USER_TABLE"])

    user_id = event["pathParameters"]["user_id"]

    # Check if user exists
    reply = _getItem(userTable, "user_id", user_id)
    if not reply["success"]:
        return _http_response(reply["status"],reply["response"], reply["application_status"])

    # Return user
    return _http_response(ResponseStatus.OK, reply["response"], reply["application_status"])
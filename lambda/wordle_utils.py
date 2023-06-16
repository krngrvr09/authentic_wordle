import json
import uuid
import enum
# HTTP response status codes
class ResponseStatus(enum.Enum):
    OK = 200
    CREATED = 201
    TEMPORARY_REDIRECT = 302
    MALFORMED_REQUEST = 400
    NOT_AUTHORISED = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# Application Status Codes
class ApplicationStatus(enum.Enum):
    OK = 1
    CREATED = 2
    MISSING_PARAMETERS = 3
    NOT_AUTHORISED = 4
    INPUT_ERROR = 5
    GAME_OVER = 6
    DATABASE_ERROR = 7

# Game Status and Guess Colours
GREY = "GREY"
GREEN = "GREEN"
YELLOW = "YELLOW"
IN_PROGRESS = "IN_PROGRESS"
WON = "WON"
LOST = "LOST"


def _http_response(response_status, response_message, application_status, headers=None):
    """
    Builds a HTTP response object using the response status and message provided.

    Args:
        response_status (ResponseStatus): The HTTP response status code
        response_message (str): The message to be returned in the HTTP response body
        headers (dict, optional): The HTTP response headers. Defaults to None.
    
    Returns:
        dict: The HTTP response object
    """
    response_object = {
                'statusCode': response_status.value,
                'body': json.dumps({"message":response_message, "status": application_status.name})
            }
    if headers is not None:
        response_object["headers"] = headers
    return response_object


def _getItem(table, pk_name, pk_value, sk_name=None, sk_value=None):
    """
    Retrieves an item from the provided table using the provided primary key and sort key (if provided).

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        pk_name (str): The name of the primary key
        pk_value (str/int): The value of the primary key
        sk_name (str, optional): The name of the sort key. Defaults to None.
        sk_value (str/int, optional): The value of the sort key. Defaults to None.
    
    Returns:
        dict: The item retrieved from the table as a dictionary object if successful, otherwise a dictionary object containing an error message and status code
    """
    key = {
        pk_name: pk_value,
    }
    if sk_name is not None:
        key[sk_name] = sk_value
    
    try:
        itemObject = table.get_item(Key=key)
        if "Item" in itemObject:
            return {"success":True, "response":itemObject["Item"], "application_status": ApplicationStatus.OK}
        else:
            error_message = "{} with id: {} not found in {}".format(pk_name, str(pk_value), table.table_name)
            return {"success":False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.INPUT_ERROR}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from {}".format(pk_name, str(pk_value), table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.DATABASE_ERROR}


def _getRandomItem(table, partition_key, partition_key_value):
    #TODO: CHeck if this works, if not dont include in this function
    print(table.table_name)
    """
    Retrieves a random item from the provided table. Performs a scan
    on the table using partition_key and partition_key_value to filter
    the results. A random item is then selected from the results.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        partition_key (str): The name of the partition key
        partition_key_value (str/int): The value of the partition key
    
    Returns:
        dict: The item retrieved from the table as a dictionary object if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        keyConditionExpression = "{} = :partition_key_value".format(partition_key)
        response = table.query(
            KeyConditionExpression=keyConditionExpression,
            ExpressionAttributeValues={':partition_key_value': partition_key_value}
        )
        items = response['Items']
        n = len(items)
        if n == 0:
            return {"success":False, "response": "No items found in {}".format(table.table_name), "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.INPUT_ERROR}
        else:
            random_int = uuid.uuid4().int
            idx = random_int % n
            return {"success":True, "response": items[idx], "application_status": ApplicationStatus.OK}
    except Exception as e:
        print(e)
        error_message = "Exception while getting {}: {} from {}".format(partition_key, str(partition_key_value), table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.DATABASE_ERROR}


def _putItem(table, item):
    """
    Inserts a new item into the provided table.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        item (dict): The item to be inserted into the table
    
    Returns:
        dict: A dictionary object of the item inserted into the table if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item, "status": ResponseStatus.OK, "application_status": ApplicationStatus.OK}
        else:
            error_message = "Unable to write item to {}".format(table.table_name)
            return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.INPUT_ERROR}
    except Exception as e:
        print(e)
        error_message = "An exception occured while writing item to {}".format(table.table_name)
        return {"success": False, "response": error_message, "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.DATABASE_ERROR}


def _deleteItem(table, item_id_name, item_id):
    """
    Deletes an item from the provided table using the provided primary key.

    Args:
        table (DynamoDB.Table): The DynamoDB table object
        item_id_name (str): The name of the primary key
        item_id (str/int): The value of the primary key
    
    Returns:
        dict: A dictionary object containing a success message if successful, otherwise a dictionary object containing an error message and status code
    """
    try:
        response = table.delete_item(
                Key={
                    item_id_name: item_id
                }
            )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": "Item deleted successfully.", "application_status": ApplicationStatus.OK}
        else:
            return {"success": False, "response": "Error deleting item: {} in {}".format(str(item_id), table.table_name), "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.INPUT_ERROR}
            
    except Exception as e:
        print(e)
        return {"success": False, "response": "Exception deleting item with id: {} from {}".format(str(item_id), table.table_name), "status": ResponseStatus.INTERNAL_ERROR, "application_status": ApplicationStatus.DATABASE_ERROR}
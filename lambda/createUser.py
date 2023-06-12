import json
import boto3
import uuid

def handler(event, context):
        dynamodb = boto3.resource('dynamodb')
        userTable = dynamodb.Table('user')
        user_id = str(uuid.uuid4())
        new_item = {
            "user_id": user_id,
            "game_id": ""
        }
        try:
            response = userTable.put_item(Item=new_item)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print('Item created successfully')
                return {
                'statusCode': 201,
                'body': json.dumps({"status": "success","user_id":user_id})
            }
            else:
                return {
                    'statusCode': 409,
                    'body': json.dumps({"error": "Unable to create new user."})
                }
                print('Failed to create item')
        except Exception as e:
            print(e)
            return {
                    'statusCode': 500,
                    'body': json.dumps({"error": "An exception occured while creating a new user."})
                }
    # Add more attributes as needed

    
    
import json
import boto3
import os
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

def valid(wordTable, word, word_length):
        if len(word) != word_length:
            print("Invalid input length")
            return False
        for c in word:
            if not c.isalpha():
                print("Invalid input character")
                return False
        reply = _getItem(wordTable, "word_length", int(word_length), "word", word)
        
        if not reply["success"]:
            return False
        return True

def _http_response(response_code, response_message):
    return {
                'statusCode': response_code,
                'body': json.dumps({"message":response_message})
            }

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
            error_message = pk_name+" with id: "+str(pk_value)+" not found"
            return {"success":False, "response": error_message, "response_code": 404}
    except Exception as e:
        print(e)
        error_message = "Exception while getting "+pk_name+": "+str(pk_value)+" from DynamoDB"
        return {"success": False, "response": error_message, "response_code": 500}

def _putItem(table, item):
    try:
        response = table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {"success": True, "response": item}
        else:
            error_message = "Unable to create new game."
            return {"success": False, "response": error_message, "response_code": 422}
    except Exception as e:
        print(e)
        error_message = "An exception occured while creating a new game."
        return {"success": False, "response": error_message, "response_code": 500}

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
    # return _http_response(event)
    if "pathParameters" not in event or "queryStringParameters" not in event or "user_id" not in event["pathParameters"] or "game_id" not in event["pathParameters"] or "guess" not in event["queryStringParameters"]:
        return _http_response(400, "Invalid parameters")
    else:
        dynamoClient = boto3.resource("dynamodb")
        userTable = dynamoClient.Table(os.environ['USER_TABLE'])
        gameTable = dynamoClient.Table(os.environ['GAME_TABLE'])
        wordTable = dynamoClient.Table(os.environ['WORD_TABLE'])

        user_id = event["pathParameters"]["user_id"]
        game_id = event["pathParameters"]["game_id"]
        guess = event["queryStringParameters"]["guess"]
        
        # check mapping between game id and user id
        reply = _getItem(userTable, "user_id", user_id)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        user = reply["response"]
        if(user["game_id"]!=game_id):
            return _http_response(403, "This user is not allowed to access this game id")
        
        # check if game exists
        reply = _getItem(gameTable, "game_id", game_id)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        game = reply["response"]

        # validate guess
        word_length = int(game["word_length"])
        if not valid(wordTable, guess, word_length):
            return _http_response(400, "Not a valid guess")
        
        # check if game is over
        attempts_left = int(game["attempts_left"])
        if game["status"]!="IN_PROGRESS" or attempts_left<=0:
            return _http_response(200, game)


        res = getGuessResponse(guess, game["word"])
        attempts_left -= 1
        if res == ["GREEN" for c in game["word"]]:
            game["status"] = "WON"
        elif attempts_left == 0:
            game["status"] = "LOST"
        game["guesses"].append(guess)
        game["responses"].append(str(res))
        game["attempts_left"]=str(attempts_left)
        reply = _putItem(gameTable, game)
        if not reply["success"]:
            return _http_response(reply["response_code"], reply["response"])
        return _http_response(201, reply["response"])

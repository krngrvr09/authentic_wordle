import json
import boto3
import os
def serialize(word):
        """
        carbone -> [[1],[3],[0],[],[6],[],[],[],[],[],[],[],[],[5],[4],[],[],[2],[],[],[],[],[],[],[],[]]
        """
        sword = [None]*26
        for i in range(26):
            sword[i] = []
        cidx=0
        for c in word:
            idx = ord(c) - ord('a')
            sword[idx].append(cidx)
            cidx+=1
        return sword
"""
    - 0 means not guessed
    - 1 means guessed but not in the right place
    - 2 means guessed and in the right place
    - 3 means not in the word
"""
def getStatus(gl, tl):
        if len(tl)==0:
            return 3
        gidx = gl[0]
        if gidx in tl:
            gl.pop(0)
            return 2
        else:
            gl.pop(0)
            return 1

def valid(word, word_length):
        if len(word) != word_length:
            print("Invalid input length")
            return False
        for c in word:
            if not c.isalpha():
                print("Invalid input character")
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
    print("key: "+str(key))
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
        try:
            tmp = json.dumps(item)
            print("putting item into table")
            print(tmp)
        except Exception as e:
            return {"success": False, "response": "Error serializing json", "response_code": 500}
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
        # check mapping between game id and user id
        reply = _getItem(userTable, "user_id", user_id)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        
        user = reply["response"]
        user_game_id = user["game_id"]
        if(user_game_id!=game_id):
            return _http_response(403, "This user is not allowed to access this game id")
        
        guess = event["queryStringParameters"]["guess"]
        reply = _getItem(gameTable, "game_id", game_id)
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        gameObject = reply["response"]

        word_length = int(gameObject["word_length"])
        reply = _getItem(wordTable, "word_length", int(word_length), "word", guess)
        
        if not reply["success"]:
            return _http_response(reply["response_code"],reply["response"])
        
        attempts_left = int(gameObject["attempts_left"])
        if(attempts_left<=0):
            return _http_response(200, gameObject)

        if not valid(guess, word_length):
            return _http_response(400, "Not a valid guess")

        target = gameObject["word"]
        game_status = gameObject["status"]
        guesses = gameObject["guesses"]
        responses = gameObject["responses"]
        sgword = serialize(guess)
        sword = serialize(target)
        res=[]
        print("target: "+target+" guess: "+guess)
        print("sword: "+str(sword)+" sgword: "+str(sgword))
        for c in guess:
            idx = ord(c) - ord('a')
            gl = sgword[idx]
            tl = sword[idx]
            print("tl: "+str(tl)+" gl: "+str(gl))
            char_status = getStatus(gl, tl)
            # self.state[idx] = status
            res.append((c, char_status))
        attempts_left -= 1
        if res == [(c, 2) for c in target]:
            game_status = "WON"
            attempts_left = 0
        elif attempts_left == 0:
            game_status = "LOST"
        guesses.append(guess)
        responses.append(str(res))
        gameObject["responses"]=responses
        gameObject["guesses"]=guesses
        gameObject["status"]=game_status
        gameObject["attempts_left"]=str(attempts_left)
        reply = _putItem(gameTable, gameObject)
        if not reply["success"]:
            return _http_response(reply["response_code"], reply["response"])
        return _http_response(201, reply["response"])

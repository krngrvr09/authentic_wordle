
# Authentic Wordle

## Table of Contents
1. Directory Structure
2. DynamoDB Data Model
3. Design Decisions
4. Game/API Design
5. Future Work/Improvements

## Directory Structure (relevant files)
- root/
  - lambda/
    - `createGame.py`
    - `createUser.py`
    - `deleteGame.py`
    - `getGame.py`
    - `getHome.py`
    - `getUser.py`
    - `guess.py`
    - `populateWords.py`
    - `wordle_utils.py` - utility functions used all across
  - wordle_sdk/
    - `api_stack.py`
    - `db_stack.py`
    - `lambda_stack.py`
    - `wordle_cdk_stack.py`
  - `api.yaml` - formal API design
  - `notes.txt` - rough notes on the ideation about game/api design and data model
  - `solve.py` - An OO python game simulating Wordle to understand functions and data model
  
## DynamoDB Data Model
### User
- `user_id(string, Partition Key)` - UUID string uniquely identifying user
- `game_id(String)` - UUID string uniquely identifying game

### Game
- `game_id(string, Partition Key)` - UUID string uniquely identifying game
- `attempts_left(int)` - Number of attempts left in this game. Not allowed to continue if this number <=0
- `hard_mode(int)` - boolean variable with values 1/0
- `word_length(int)` - chosen by the user when creating the game
- `word(string)` - Randomly assigned to the game from the words table
- `status(string)` - IN_PROGRESS/WON/LOST
- `guesses(list)` - list of strings where each string is a guess that user made. useful to allow hard mode
- `responses(list)` - list of list of strings where each element is the response for the respective guess.
Eg. [“GREEN”,“GREEN”,“GREY”, “YELLOW”,“GREEN”] is a response for a 5 letter guess.

### Word
- `word_length(int, Partition Key)`
- `word(string, Sort Key)`

## Design Decisions

### Combining user & game data in a single table or having separate tables
I have 2 options here:
1. **Use 2 tables**: User and Game. GameTable will contain [game_id, word, attempts_left, status], UserTable will contain [user_id, game_id]. The spec doesn’t say anything about any other user information we'd have to store, eg. stats.
2. **Use 1 table**: Session. Since User and Game are so tightly linked and mapped 1:1, just have one table called Session. It will have [session_id, word, attempts_left, status]. Once the game is restarted, these values(Except session_id) are overwritten.

Comparison:
1. **Option 1 is better** if we have to evolve the design over time. If the game evolves, eventually session will be broken up into 2 tables.
2. **Option 1 is better** from a security standpoint. There is no authentication. User is assigned a unique ID when they start playing a game and it is stored in the browser to identify the user. All requests have this token as a parameter to identify the user in the backend. If this token gets leaked, all of the user's games can be manipulated by an attacker. In Option 2, the User's game can be manipulated by the pair (user_id, game_id). Even if both get leaked, then future games cannot be affected.
3. **Option 2 is better** because it has lower storage overhead. Right now I am assuming that if the game finishes it will never be accessed again. If any stats need to be computed, they should be computed/updated before the data is overwritten. In Option 1, if we want to save space, we'd have to send an extra DELETE request for that resource when beginning a new game. According to REST standards, I am hesitant to delete a record in a POST request for a new record. Although **Option 1 could be better** because it's more modular. In the future, if we want to scan over old games to do some analytics, we can just change the frontend to drop the DELETE request, instead of changing the backend.
4. **Option 2 is better** because it has a better/simpler fault tolerance model. In Option 1, we'll update two tables when generating a new game, so it might require "transactions". Option 1 could be okay because DELETE is idempotent.

Conclusion:

Going with **Option 1** because it is more modular, allows for better evolution of design, and can mitigate its associated downsides with some effort.

### Organizing the Words Table
We make 2 types of requests to the words table
1. Random Word Generation - less frequent
2. Guess Validity Check - more frequent

It is clear that the word_length should be the partition_key. Generating a random word boils down to picking a random key from dynamoDB. DynamoDB does not have native support for this. There are 2 ways to do it:
**Approach 1**: Use a scan operation to get all elements and pick one randomly once you know the total size of words. Make the word itself the sort key.

**Approach 2**: Assign each word a unique incrementing ID and store the size of the words set in a metadata table. Make this unique ID the sort key.
To search for a word when doing the Guess Validity Check, we can have a secondary local index on the “word” key.

**Approach 1** is simpler to implement but requires a DB scan which can be slow in the face of a large number of words.
**Approach 2** is complicated to implement and maintain, but is very fast. It also requires more space due to the secondary index.

I went with **Approach 1** because
1. the number of words is bounded and small therefore we can pay the price of DB scan.
2. Checking whether the word exists in the DB is a more frequent operation. Hence making the word itself the sort key is faster.

### High Consistency vs Eventual Consistency in DynamoDB
The question is should we switch DynamoDB to process the writes with “high consistency” or should we leave it to the default setting of Eventual Consistency

Comparison
1. **Eventual Consistency is better** because even though the workload is `read-modify-update`, a user only ever sees their own data. In the face of concurrent users accessing the DB, there will be no conflicts. A single user, in a normal scenario, will not write to the DB concurrently as they play the game serially. In the worst case, they can try to play from 2 devices at once and there is a small chance that they submit a guess at the same time and it results in a `lost-write` - Extra Guess. However, the possibility and incentive is minuscule compared to the effort required to mount this attack.
2. **High Consistency is better** in scenarios where the user does a `read-after-write` operation in succession. Which will happen in this case. However, eventual consistency converges in a matter of seconds and the user can simply refresh their browser to see the latest results.
One way to solve the `read-after-write` problem in Eventual Consistency is to send the guess_number with the guess. If the user has sent n guesses, we only approve this guess if it’s n+1. This way we guarantee `exactly-once semantics` because dynamoDB uses single leader replication. However, this seems to be hovering at the edge of **over-engineering**

Conclusion
Going with **eventual consistency** because there is no major reason to shift to high consistency.

### Passing user_id with game_id everytime vs only using game_id
The question is that if the `game_id` is globally unique, do we need to pass `user_id` in every request **(option 1)** or should we just use `game_id` **(option 2)**. In terms of API Design, this would look like a choice between `/user/{user_id}/games/{game_id}` vs `/games/{game_id}`

Comparison
- **Option 1 is better** because a malicious user would have to leak both `user_id` and `game_id` to mount an attack. In Option 2, just a `game_id` would work.
- **Option 1 is better** because the API hierarchy is more intuitive. “game” belongs to a “user” and is not an independent resource.

Conclusion
Going with **Option 1** because it serves a significant purpose in terms of utility and understanding without having a lot of overhead.

### REST API Best Practices vs Application-Specific Design
In the REST API we have “resources” and “methods” to manage those specific resources. API guidelines say that the methods should have a clear purpose that stems from the URL, Method Type and be reflected in the response code. For example, modifying resource B in the `POST` request for resource A, should be treated carefully. Here I will show 3 instances where I had to make a design choice about REST API design and what did I do:


1. Modifying the `user table` when a game is inserted in the `game table`. Here, I believe, it’s okay to modify a different table. Especially because it is a parent table. the change is intuitive and necessary.
2. Deleting the old game, after creating the new game. Since a user will only ever be playing one game, in my application I delete the games that are completed. I believe it’s not correct to delete old game in the `POST` request of new game. It is not intuitive. It might also be better to separate these requests, in case we want to change the behavior later on. Therefore, I provide a separate `DELETE` method.
3. Making a guess is a `POST` operation and not a `PUT` operation. Even though making a guess modifies an existing resource, I don't make a `PUT` operation because the standard recommends `PUT` operations to be idempotent. Since making a guess is not idempotent and can be thought of as creating a ‘hypothetical’ guess resource, I have chosen for it to be a `POST` operation.

## Game/API Design

**GET /**

The `/` endpoint will either return a static page or redirect to the game if there is an active one.
static page will ask user to create a game.
If the frontend finds a `user_id`, then it will send `POST /user/{user_id}/games`
If not, it will send a `POST /users` and then a `POST /users/{user_id}/games`

**GET /user/{user_id}/games/{game_id}**

Returns the current game state to the frontend. The frontend can decide which attributes to forward to the client.

**POST /users**

Creates a new user and returns the user object to the frontend. The frontend can decide which attributes to forward to the client.

**POST /users/{user_id}/games**

Creates a new game. Takes `hard_mode` and `word_length` as parameters. Returns the game object to the frontend. The frontend can decide which attributes to forward to the client.

**DELETE /users/{user_id}/games/{game_id}**

Deletes the game object associated with the game id and removes the mapping with `user_id`.

**POST /users/{user_id}/games/{game_id}/guess**

Updates the game object with the guess and returns the response as a list of colours. The frontend can decide what’s the best way to show it to the user.

**POST /words**

Populates the dynamoDB words table with words.

More details are in the `api.yaml` file present in the submission directory.

## Future Work/Improvements

Like any project, this project also has scope for improvements and work that can be done in the future. Some of these improvements/features include:
Expanding the Wordle dictionary
1. Right now we are limited by the 30s API gateway timeout to insert words into dynamoDB. This can be improved by requesting a beefier lambda instance and taking advantage of concurrency. Other methods include caching to improve DynamoDB insert latency. The primary reason seems to be the low provisioned throughput of a free-tier DynamoDB instance.
https://medium.com/skyline-ai/dynamodb-insert-performance-basics-in-python-boto3-5bc01919c79f
2. Write automated tests for the API
I couldn't do this due to lack of time, but would have liked to get this done.

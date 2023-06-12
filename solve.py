DEBUG = True
class WordFactory:
    fiveLetterWords = []
    sixLetterWords = []
    sevenLetterWords = []
    eightLetterWords = []

    @staticmethod
    def getWord(wordLen, index):
        if wordLen == 5:
            return WordFactory.fiveLetterWords[index]
        elif wordLen == 6:
            return WordFactory.sixLetterWords[index]
        elif wordLen == 7:
            return WordFactory.sevenLetterWords[index]
        elif wordLen == 8:
            return WordFactory.eightLetterWords[index]
        else:
            raise Exception("Invalid word length")
    
    @staticmethod
    def loadWords():
        with open("five.txt", "r") as f:
            WordFactory.fiveLetterWords = f.read().splitlines()
        with open("six.txt", "r") as f:
            WordFactory.sixLetterWords = f.read().splitlines()
        with open("seven.txt", "r") as f:
            WordFactory.sevenLetterWords = f.read().splitlines()
        with open("eight.txt", "r") as f:
            WordFactory.eightLetterWords = f.read().splitlines()
    
    @staticmethod
    def exists(word, wordLen):
        if wordLen == 5:
            return word in WordFactory.fiveLetterWords
        elif wordLen == 6:
            return word in WordFactory.sixLetterWords
        elif wordLen == 7:
            return word in WordFactory.sevenLetterWords
        elif wordLen == 8:
            return word in WordFactory.eightLetterWords
        else:
            raise Exception("Invalid word length")
class User:
    game = None
    def __init__(self, name):
        self.name = name
        self.wordIndex = {5:0,6:0,7:0,8:0}
    
    def getWord(self, wordLen):
        word = WordFactory.getWord(wordLen, self.wordIndex[wordLen])
        self.wordIndex[wordLen] += 1
        return word
    
    def createGame(self, wordLen):
        self.game = WordleGame(wordLen, self.getWord(wordLen))


    def guess(self, word):
        # input sanitization
        
        return self.game.guess(word)            


class WordleGame:
    def serialize(self, word):
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

    def __init__(self, wordLen, word):
        if wordLen < 5 or wordLen > 8:
            raise Exception("Invalid word length")
        self.wordLen = wordLen
        self.word = word
        self.sword = self.serialize(word)
        self.attempts_left = wordLen+1
        self.status = "IN_PROGRESS"
        if DEBUG:
            print("T: ", word)
        # self.state = [0] * 26
    

    def getStatus(self, gl, tl):
        if len(tl)==0:
            return 3
        gidx = gl[0]
        if gidx in tl:
            gl.pop(0)
            return 2
        else:
            gl.pop(0)
            return 1

    def valid(self, word):
        if len(word) != self.wordLen:
            print("Invalid input length")
            return False
        for c in word:
            if not c.isalpha():
                print("Invalid input character")
                return False
        return True

    def getRes(self, guess, target):
        res=[]
        idx=0
        print(guess, " ",target)
        for c in guess:
            if c not in target:
                res.append((c, 3))
            elif target[idx]==c:
                res.append((c, 2))
            else:
                res.append((c, 1))
            idx+=1
        return res

    def guess(self, word):
        """
        takes two serialized words and returns the list of tuples for the word, but also updated the state of the game.
        """
        if DEBUG:
            print("G: ", word, "A: ", self.attempts_left)
        if self.attempts_left == 0:
            raise Exception("No attempts left")
        if not self.valid(word):
            # print("Invalid input. Try again")
            return None
        if not WordFactory.exists(word, self.wordLen):
            print("Word does not exist. Try again")
            return None
        guess = word
        target = self.word
        res = self.getRes(guess, target)
        self.attempts_left -= 1
        if res == [(c, 2) for c in self.word]:
            self.status = "WON"
            self.attempts_left = 0
        elif self.attempts_left == 0:
            self.status = "LOST"
        return res


"""
word is sent as a word
word state is returned as a list of tuples [('c', 0), ('a', 1), ('t', 0)]
    - the numbers represent colours
    - or we can use actual colours.
game state is represented as a list of 26 numbers - each number representing a colour.
    - 0 means not guessed
    - 1 means guessed but not in the right place
    - 2 means guessed and in the right place
    - 3 means not in the word
There is a hard mode.
"""

def pretty_print_result(res):
    if res is None:
        return
    for c, status in res:
        if status == 0:
            print(c+"(BLACK)", end=" ")
        elif status == 1:
            print(c+"(YELLOW)", end=" ")
        elif status == 2:
            print(c+"(GREEN)", end=" ")
        elif status == 3:
            print(c+"(GRAY)", end=" ")
    print()

if __name__=="__main__":
    WordFactory.loadWords()
    user = User("test")
    user.createGame(5)
    while user.game.status == "IN_PROGRESS":
        guess = str(input())
        pretty_print_result(user.guess(guess))
    
    print(user.game.status)
    # guess = str(input())
    # pretty_print_result(user.guess(guess))
    # guess = str(input())
    # pretty_print_result(user.guess(guess))
    # guess = str(input())
    # pretty_print_result(user.guess(guess))
    # guess = str(input())
    # pretty_print_result(user.guess(guess))
    # guess = str(input())
    # pretty_print_result(user.guess(guess))
    
    
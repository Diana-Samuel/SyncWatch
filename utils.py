import random

def randomid(length: int) -> str:
    """
    Generates a random ID For Users,Posts,Groups, Etc. 
    Attr:
    length: int         # The length of the ID

    Output:
    ID: str             # ID with the length of Inputted Length 
    """
    
    # Create a variables that hold the max and min length of ID.
    minlen = ""
    maxlen = ""
    
    # Fill them with the range needed
    for i in range(int(length)):
        minlen += "0"
        maxlen += "9"
    
    # Create a random userID In the Needed Range
    userId = random.randint(int(minlen),int(maxlen))

    # If the length isn't the length given then fill the gap with "0"
    if len(str(userId)) != length:
        diff = length - len(str(userId))
        userId = str(userId)
        for _ in range(diff):
            userId = "0" + str(userId)
    
    return userId

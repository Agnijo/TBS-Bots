import discord

def removeExclamation(mention):
    if len(mention) > 2:
        if mention[2]=="!":
            mention="<@"+mention[3:]
    return str(mention)

def dmCheck(channel):
    if str(channel).startswith("Direct Message with"):
        return True
    return False

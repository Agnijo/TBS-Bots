import discord
import math
from random import shuffle

#Displays cards as a string
async def carddisplay(client,message,cardslist,cards,initstr):
    #Determine initial string for card message
    if initstr == 0:
        cardstr = "Current cards:\n"
    if initstr == 1:
        cardstr = "Game started with cards:\n"

    for i in range(len(cards)):
        for j in range(len(cardslist)):
            if cardslist[j] == cards[i]:
                cardstr = cardstr+cards[i]+", "
    cardstr = cardstr.rstrip(", ")
    await message.channel.send(cardstr)

#Assigns cards to players
def givecards(playerlist,cardslist,numeachcard):
    deck = []
    for i in range(len(cardslist)):
        deck.extend([cardslist[i]] * numeachcard)
    shuffle(deck)
    playercards = []
    for i in range(len(playerlist)):
        nexthand = [deck.pop()]
        nexthand.append(deck.pop())
        playercards.append(nexthand)
    centrecards = deck
    return playercards,centrecards

#Displays current game state
async def displaygame(client,message,playerlist,playerlives,playercredits,centrecards,revealedcards):
    messagestring = ""
    for i in range(len(playerlist)):
        if playercredits[i] >= 10:
            warningstring = ":warning:"
        else:
            warningstring = ""
        if playerlives[i] == 0:
            messagestring = messagestring + "~~{} has 0 cards.~~\n".format(playerlist[i].display_name)
        else:
            messagestring = messagestring + "{} has {} cards and {} credits{}.\n".format(playerlist[i].display_name,playerlives[i],playercredits[i],warningstring)
        messagestring = messagestring + "Revealed cards: "
        if playerlives[i] == 0:
            messagestring = messagestring + "{}, {}\n\n".format(revealedcards[i][0],revealedcards[i][1])
        elif playerlives[i] == 1:
            messagestring = messagestring + "{}, -----\n\n".format(revealedcards[i][0])
        else:
            messagestring = messagestring + "-----, -----\n\n"
    messagestring = messagestring + "There are {} centre cards.\n".format(len(centrecards))
    messagestring = messagestring + "It is {}'s turn!".format(playerlist[0].display_name)
    await message.channel.send(messagestring)

#Shows one player their cards
async def displaycards(player,cards):
    if len(cards) == 2:
        await player.send("You have the {} and the {}".format(cards[0],cards[1]))
    elif len(cards) == 1:
        await player.send("You have the {}".format(cards[0]))

#Cycles playerlist at end of turn
def cycleplayers(playerlist,playerlives,playercredits,playercards,revealedcards):
    while True:
        playerlist.append(playerlist.pop(0))
        playerlives.append(playerlives.pop(0))
        playercredits.append(playercredits.pop(0))
        playercards.append(playercards.pop(0))
        revealedcards.append(revealedcards.pop(0))
        if playerlives[0] != 0:
            break
    return playerlist,playerlives,playercredits,playercards,revealedcards

#Checks whether channel is DM
def dmCheck(channel):
    if str(channel).startswith("Direct Message with"):
        return True
    return False

#Removes exclamaion mark from mention in order to standardise it
def removeExclamation(mention):
    if len(mention) > 2:
        if mention[2]=="!":
            mention="<@"+mention[3:]
    return str(mention)

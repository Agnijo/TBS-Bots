import discord
import random
from helpcommands import *
from datetime import datetime
from random import shuffle
from utils import *
import math
import asyncio

client = discord.Client()
busyChannels = []
game = discord.Game(name="Coup")

minplayers = 2                  #Minimum number of players
maxplayers = 10                 #Maximum number of players
mincards = 5                    #Minimum number of types of cards
challengetimer = 10             #Number of seconds after a play in which someone may challenge it (for Ambassador/Inquisitor, where challenges must occur before the action)

#List of cards
cards = ["Duke","Captain","Assassin","Contessa","Ambassador"]

#Default cards
defaultcards = ["Duke","Captain","Assassin","Contessa","Ambassador"]

#List of actions that can be challenged at a point where the next turn can be taken
challengelist = ["Duke","Duke Block"]

@client.event
async def on_ready():
    print("Connected!")
    print("Username: " + client.user.name)
    print("ID: " + str(client.user.id))
    await client.change_presence(activity = game)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!hello":
        msg = "Greetings {0.author.mention}".format(message)
        await message.channel.send(msg)

    if message.content == "!coup":
        if message.channel in busyChannels:
            await message.channel.send("Channel busy with another activity.")
        else:
            busyChannels.append(message.channel)
            await message.channel.send("Starting **Coup** in `#"+message.channel.name+"`...")
            await coup(client,message)
            busyChannels.remove(message.channel)

    if message.content == "!help":
        await helpcommand(client, message)

    if message.content == "!cards":
        await helpcards(client, message)
    
    if message.content == "!rules":
        await rules(client, message)

async def coup(client,message):

    #Declarations
    gamestate = 0               #State of game
    playerlist = []             #List of players
    cardslist = []              #List of types of cards
    playerlives = []            #Number of lives each player has
    playercredits = []          #Number of credits each player has
    playercards = []            #Type of cards each player has
    centrecards = []            #Cards in the centre
    revealedcards = []          #Cards revealed by each player

    if gamestate == 0:          #Login phase
        gamestate,playerlist = await login(client,message)
    if gamestate == 2:          #Card choosing phase
        gamestate,cardslist = await choosecards(client,message,playerlist)
    if gamestate == 3:
        playerlives = [2] * len(playerlist)
        playercredits = [2] * len(playerlist)
        numeachcard = max(3,math.ceil((len(playerlist)*2+3)/len(cardslist)))
        await message.channel.send("There are {} of each card!".format(numeachcard))
        #Assigns cards
        playercards,centrecards = givecards(playerlist,cardslist,numeachcard)
        for i in range(len(playerlist)):
            revealedcards.append([])
        #Main game
        await maingame(client,message,playerlist,cardslist,playerlives,playercredits,playercards,centrecards,revealedcards)
    
#Login phase
async def login(client,message):
    gamestate = 1
    playerlist = []
    await message.channel.send("```Login Phase Triggered```\nThe game of Coup is about to begin.\n*Type !join to enter the game. ({}-{} players only.)*\n".format(minplayers,maxplayers))
    while gamestate == 1:
        def channel_check(m):
            return m.channel == message.channel
        reply = await client.wait_for("message", check=channel_check)
        if reply.content == "!join":
            if len(playerlist) <= maxplayers:
                if reply.author not in playerlist:
                    await message.channel.send("{} has joined the game.".format(reply.author.display_name))
                    playerlist.append(reply.author)
                else:
                    await message.channel.send("{} is already in the game.".format(reply.author.display_name))
            else:
                await message.channel.send("The game is full.")
        if reply.content == "!quit":
            if reply.author in playerlist:
                await message.channel.send("{} has left the game.".format(reply.author.display_name))
                playerlist.remove(reply.author)
            else:
                await message.channel.send("{} wasn't in the game.".format(reply.author.display_name))
        if reply.content == "!stop" and reply.author in playerlist:
            await message.channel.send("The game has been stopped.")
            gamestate = 0
        if reply.content == "!start" and reply.author in playerlist:
            if len(playerlist) < minplayers:
                await message.channel.send("Not enough players. (Need {} to start)".format(minplayers))
            else:
                random.seed(datetime.now())
                shuffle(playerlist)
                gamestate = 2
    return gamestate,playerlist

#Choosing which cards will be in play
async def choosecards(client,message,playerlist):
    gamestate = 2
    cardslist = defaultcards.copy()
    await message.channel.send("```Card Choosing Phase Triggered```")
    await carddisplay(client,message,cardslist,cards,0)
    while gamestate == 2:
        def player_check(m):
            return m.channel == message.channel and m.author in playerlist
        reply = await client.wait_for("message", check=player_check)
        replylist = reply.content.split()
        if replylist[0] == "!add":
            for i in range(len(replylist)):
                for j in range(len(cards)):
                    cardshortstr = "".join(cards[j].lower().split())
                    if replylist[i] == cardshortstr:
                        if cards[j] not in cardslist:
                            cardslist.append(cards[j])
            await message.channel.send("Cards have been added.")
            await carddisplay(client,message,cardslist,cards,0)
        if replylist[0] == "!remove":
            for i in range(len(replylist)):
                for j in range(len(cards)):
                    cardshortstr = "".join(cards[j].lower().split())
                    if replylist[i] == cardshortstr and cards[j] in cardslist:
                        cardslist.remove(cards[j])
            await message.channel.send("Cards have been removed.")
            await carddisplay(client,message,cardslist,cards,0)
        if replylist[0] == "!stop":
            await message.channel.send("The game has been stopped.")
            gamestate = 0
        if replylist[0] == "!start":
            if len(cardslist) >= mincards:
                await carddisplay(client,message,cardslist,cards,1)
                gamestate = 3
            else:
                await message.channel.send("There are currently {} cards. {} needed to start.".format(len(cardslist),mincards))
    return gamestate,cardslist

#For dealing with deaths
async def processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum):
    if playerlives[deathnum] == 1:
        playerlives[deathnum] = 0
        lostcard = playercards[deathnum].pop()
        await message.channel.send("{} is now out of the game and revealed their {}!".format(playerlist[deathnum].display_name,lostcard))
        revealedcards[deathnum].append(lostcard)
    elif playerlives[deathnum] == 2:
        def lostcard_check(m):
            return dmCheck(m.channel) and m.author == playerlist[deathnum]

        playerlives[deathnum] = 1
        await message.channel.send("{} has lost influence so must discard a card!".format(playerlist[deathnum].display_name))
        while True:
            await playerlist[deathnum].send("Please choose a card to discard.")
            discardreply = await client.wait_for('message', check=lostcard_check)
            if discardreply.content not in playercards[deathnum]:
                await playerlist[deathnum].send("Invalid response. (Type the name of the card you wish to discard.)")
                continue
            break
        lostcard = discardreply.content
        playerlives[deathnum] = 1
        playercards[deathnum].remove(lostcard)
        await displaycards(playerlist[deathnum],playercards[deathnum])
        await message.channel.send("{} has lost their {}!".format(playerlist[deathnum].display_name,lostcard))
        revealedcards[deathnum].append(lostcard)
    return playerlives,playercards,revealedcards


#For dealing with challenges
async def processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,challengeauthor):

    #Gets number of challenger and challenged
    challengernum = 0
    challengednum = 0
    for i in range(len(playerlist)):
        if playerlist[i] == challengeauthor:
            challengernum = i
        if playerlist[i] == prevaction[1]:
            challengednum = i

    challengetype = prevaction[0]

    deathnum = challengednum

    challengecard = ""
            
    if challengetype in ["Duke","Duke Block"]:
        challengecard = "Duke"
    elif challengetype in ["Captain","Captain Block"]:
        challengecard = "Captain"
    elif challengetype == "Assassin":
        challengecard = "Assassin"
    elif challengetype == "Contessa Block":
        challengecard = "Contessa"
    elif challengetype in ["Ambassador","Ambassador Block"]:
        challengecard = "Ambassador"

    await message.channel.send("{} challenged {}'s claim of {}!".format(playerlist[challengernum].display_name,playerlist[challengednum].display_name,challengecard))

    #Check whether the challenge was correct or not
    if challengecard in playercards[challengednum]:
        await message.channel.send("{} has revealed that they have a {}!".format(playerlist[challengednum].display_name,challengecard))
        playercards[challengednum].remove(challengecard)
        centrecards.append(challengecard)
        shuffle(centrecards)
        newcard = centrecards.pop()
        playercards[challengednum].append(newcard)
        await playerlist[challengednum].send("You drew the {}!".format(newcard))
        await displaycards(playerlist[challengednum],playercards[challengednum])
        await message.channel.send("{} has drawn a new card from the centre.".format(playerlist[challengednum].display_name))
        deathnum = challengernum
        #Apply effect of unsuccessfully-challenged action
        if challengetype == "Captain":
            targetnum = prevaction[2]
            await message.channel.send("{} stole from {}!".format(playerlist[challengednum].display_name,playerlist[targetnum].display_name))
            if playercredits[targetnum] == 1:
                playercredits[challengednum] += 1
                await message.channel.send("{} stole 1 credit and now has {}!".format(playerlist[challengednum].display_name,playercredits[challengednum]))
                playercredits[targetnum] = 0
                await message.channel.send("{} now has 0 credits!".format(playerlist[targetnum].display_name))
            else:
                playercredits[challengednum] += 2
                await message.channel.send("{} stole 2 credit and now has {}!".format(playerlist[challengednum].display_name,playercredits[challengednum]))
                playercredits[targetnum] -= 2
                await message.channel.send("{} now has {} credits!".format(playerlist[targetnum].display_name,playercredits[targetnum]))
        elif challengetype == "Assassin":
            playerlives,playercards,revealedcards = await processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum)
            if playerlives[deathnum] == 0:
                return playerlives,playercredits,playercards,centrecards,revealedcards
        elif challengetype == "Ambassador":
            await message.channel.send("{} has drawn two cards from the centre.".format(playerlist[0].display_name))
            numdrawing = 2
            playercards,centrecards = await drawcards(playerlist,playerlives,playercards,centrecards,numdrawing)
            await message.channel.send("{} has chosen their card.".format(playerlist[0].display_name))
    else:
        await message.channel.send("{} does not have a {}!".format(playerlist[challengednum].display_name,challengecard))
        #Nullify effect of successfully-challenged action
        if challengetype == "Duke":
            await message.channel.send("{} has to give back the money they took from tax!".format(playerlist[challengednum].display_name))
            playercredits[challengednum] -= 3
        elif challengetype == "Duke Block":
            foreignaidnum = prevaction[2]
            await message.channel.send("{} can take Foreign Aid unobstructed!".format(playerlist[foreignaidnum].display_name))
            playercredits[foreignaidnum] += 2
        elif challengetype in ["Captain Block","Ambassador Block"]:
            await message.channel.send("{} stole from {}!".format(playerlist[0].display_name,playerlist[challengednum].display_name))
            if playercredits[challengednum] == 1:
                playercredits[0] += 1
                await message.channel.send("{} stole 1 credit and now has {}!".format(playerlist[0].display_name,playercredits[0]))
                playercredits[challengednum] = 0
                await message.channel.send("{} now has 0 credits!".format(playerlist[challengednum].display_name))
            else:
                playercredits[0] += 2
                await message.channel.send("{} stole 2 credit and now has {}!".format(playerlist[0].display_name,playercredits[0]))
                playercredits[challengednum] -= 2
                await message.channel.send("{} now has {} credits!".format(playerlist[challengednum].display_name,playercredits[challengednum]))
        elif challengetype == "Contessa Block":
            playerlives,playercards,revealedcards = await processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum)
            if playerlives[deathnum] == 0:
                return playerlives,playercredits,playercards,centrecards,revealedcards

    playerlives,playercards,revealedcards = await processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum)

    return playerlives,playercredits,playercards,centrecards,revealedcards

#For dealing with Ambassador/Inquisitor drawing cards from centre and choosing which to keep
async def drawcards(playerlist,playerlives,playercards,centrecards,numdrawing):

    def draw_check(m):
        return dmCheck(m.channel) and m.author == playerlist[0]

    drawncards = []
    shuffle(centrecards)
    drawncardstring = "You drew the "
    for i in range(numdrawing):
        newcard = centrecards.pop()
        drawncards.append(newcard)
        drawncardstring = drawncardstring + newcard + ", "
    drawncardstring = drawncardstring.rstrip(", ") + "!"
    await playerlist[0].send(drawncardstring)
    newcards = playercards[0].copy()
    newcards.extend(drawncards)
    newcardstring = "You now have the "
    for i in range(len(newcards)):
        newcardstring = newcardstring + newcards[i] + ", "
    newcardstring = newcardstring.rstrip(", ") + "!"
    await playerlist[0].send(newcardstring)
    playercards[0] = []
    for i in range(playerlives[0]):
        await playerlist[0].send("Choose a card to keep!")
        while True:
            drawreply = await client.wait_for('message', check=draw_check)
            if drawreply.content in newcards:
                keptcard = drawreply.content
                newcards.remove(keptcard)
                playercards[0].append(keptcard)
                await playerlist[0].send("You have kept the {}!".format(keptcard))
                break
            await playerlist[0].send("Invalid command! (Type the name of a card you wish to keep, with capitalisation.)")
    await displaycards(playerlist[0],playercards[0])
    centrecards.extend(newcards)
    return playercards,centrecards

#Main game
async def maingame(client,message,playerlist,cardslist,playerlives,playercredits,playercards,centrecards,revealedcards):

    def channel_check(m):
        return m.channel == message.channel

    #Display game state
    await displaygame(client,message,playerlist,playerlives,playercredits,centrecards,revealedcards)

    #Display cards to players
    for i in range(len(playerlist)):
        await displaycards(playerlist[i],playercards[i])

    #Previous action (for challenging purposes)
    prevaction = ["None"]
    
    while True:

        activeplayerlist = []
        for i in range(len(playerlist)):
            if playerlives[i] > 0:
                activeplayerlist.append(playerlist[i])

        #If only one player is left, it's game over
        if len(activeplayerlist) == 1:
            break

        displayneeded = False
        turnfinished = False
        
        #Inner loop to actually get a message
        while True:
            reply = await client.wait_for('message', check=channel_check)
            if reply.author not in activeplayerlist:
                continue
            
            #If blocking Foreign Aid
            if reply.content == "block" and prevaction[0] == "Foreign Aid":
                if reply.author == prevaction[1]:
                    await message.channel.send("You cannot block your own Foreign Aid!")
                    continue
                foreignaidnum = 0
                for i in range(len(playerlist)):
                    if playerlist[i] == prevaction[1]:
                        foreignaidnum = i
                await message.channel.send("{} blocked {}'s Foreign Aid, claiming Duke!".format(reply.author.display_name,playerlist[foreignaidnum].display_name))
                playercredits[foreignaidnum] -= 2
                displayneeded = True
                prevaction = ["Duke Block",reply.author,foreignaidnum]
                break
                
            #If challenging a claim
            if reply.content == "challenge":
                if prevaction[0] not in challengelist:
                    await message.channel.send("You cannot challenge this action!")
                    continue
                if len(prevaction) < 2:
                    continue
                if reply.author == prevaction[1]:
                    await message.channel.send("You cannot challenge your own claim!")
                    continue
                challengeauthor = reply.author

                playerlives,playercredits,playercards,centrecards,revealedcards = await processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,challengeauthor)

                displayneeded = True
                prevaction = ["None"]
                if playerlives[0] == 0:
                    turnfinished = True
                break

            #From here onwards, only take commands from the current player.
            if reply.author != playerlist[0]:
                await message.channel.send("It is not your turn!")
                continue

            #If current player has 10 or more coins, must coup.
            if playercredits[0] >= 10 and not reply.content.startswith("coup"):
                await message.channel.send("If you have 10 or more credits, you must coup!")
                continue

            #If taking income
            if reply.content == "income":
                playercredits[0] += 1
                await message.channel.send("{} took Income and now has {} credits!".format(playerlist[0].display_name,playercredits[0]))
                displayneeded = True
                turnfinished = True
                prevaction = ["None"]
                break

            #If taking foreign aid
            if reply.content == "foreignaid":
                playercredits[0] += 2
                await message.channel.send("{} took Foreign Aid and now has {} credits!".format(playerlist[0].display_name,playercredits[0]))
                displayneeded = True
                turnfinished = True
                prevaction = ["Foreign Aid",playerlist[0]]
                break

            #If launching a coup
            if reply.content.startswith("coup"):
                if playercredits[0] < 7:
                    await message.channel.send("You need to have at least 7 credits to launch a coup.")
                    continue
                replylist = reply.content.split()
                mentionvalid = False
                if len(replylist) == 2:
                    targetnum = -1
                    replymention = removeExclamation(replylist[1])
                    for i in range(len(playerlist)):
                        if replymention == removeExclamation(playerlist[i].mention):
                            targetnum = i
                    if targetnum != -1:
                        mentionvalid = True
                if not mentionvalid:
                    await message.channel.send("Invalid command! (To launch a coup on @example, type coup @example.)")
                    continue
                if targetnum == 0:
                    await message.channel.send("You cannot coup yourself.")
                    continue
                if playerlives[targetnum] == 0:
                    await message.channel.send("You cannot coup a dead player.")
                    continue
                playercredits[0] -= 7
                await message.channel.send("{} launched a coup on {}!".format(playerlist[0].display_name,playerlist[targetnum].display_name))

                deathnum = targetnum
                playerlives,playercards,revealedcards = await processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum)
                
                displayneeded = True
                turnfinished = True
                prevaction = ["None"]
                break

            #If claiming Duke
            if reply.content == "duke" and "Duke" in cardslist:
                playercredits[0] += 3
                await message.channel.send("{} took tax as a Duke and now has {} credits!".format(playerlist[0].display_name,playercredits[0]))
                displayneeded = True
                turnfinished = True
                prevaction = ["Duke",playerlist[0]]
                break

            #If claiming Captain
            if reply.content.startswith("captain") and "Captain" in cardslist:
                replylist = reply.content.split()
                mentionvalid = False
                if len(replylist) == 2:
                    targetnum = -1
                    replymention = removeExclamation(replylist[1])
                    for i in range(len(playerlist)):
                        if replymention == removeExclamation(playerlist[i].mention):
                            targetnum = i
                    if targetnum != -1:
                        mentionvalid = True
                if not mentionvalid:
                    await message.channel.send("Invalid command! (To use the Captain's ability on @example, type captain @example.)")
                    continue
                if targetnum == 0:
                    await message.channel.send("You cannot steal from yourself.")
                    continue
                if playerlives[targetnum] == 0:
                    await message.channel.send("You cannot steal from a dead player.")
                    continue
                if playercredits[targetnum] == 0:
                    await message.channel.send("You cannot steal from someone who has no credits.")
                    continue
                prevaction = ["Captain",playerlist[0],targetnum]
                break

            #If claiming Assassin
            if reply.content.startswith("assassin") and "Assassin" in cardslist:
                if playercredits[0] < 3:
                    await message.channel.send("You need to have at least 3 credits to assassinate.")
                    continue
                replylist = reply.content.split()
                mentionvalid = False
                if len(replylist) == 2:
                    targetnum = -1
                    replymention = removeExclamation(replylist[1])
                    for i in range(len(playerlist)):
                        if replymention == removeExclamation(playerlist[i].mention):
                            targetnum = i
                    if targetnum != -1:
                        mentionvalid = True
                if not mentionvalid:
                    await message.channel.send("Invalid command! (To use the Assassin's ability on @example, type assassin @example.)")
                    continue
                if targetnum == 0:
                    await message.channel.send("You cannot assassinate yourself.")
                    continue
                if playerlives[targetnum] == 0:
                    await message.channel.send("You cannot assassinate a dead player.")
                    continue
                playercredits[0] -= 3
                prevaction = ["Assassin",playerlist[0],targetnum]
                break

            #If claiming Ambassador
            if reply.content == "ambassador" and "Ambassador" in cardslist:
                await message.channel.send("{} has claimed Ambassador! Other people have {} seconds to challenge their claim.".format(playerlist[0].display_name,challengetimer))

                async def challengescript(client,message,playerlist,activeplayerlist):
                    while True:
                        challengenum = 0
                        challengereply = await client.wait_for('message', check=channel_check)
                        if challengereply.author not in activeplayerlist:
                            continue
                        for i in range(len(playerlist)):
                            if challengereply.author == playerlist[i]:
                                challengenum = i
                        if challengereply.content == "challenge":
                            if challengenum == 0:
                                await message.channel.send("You cannot challenge your own claim!")
                                continue
                            break
                    return challengenum

                #Wait for either a challenge or for the countdown
                try:
                    challengenum = await asyncio.wait_for(challengescript(client,message,playerlist,activeplayerlist),timeout=challengetimer)
                    #If challenged
                    prevaction = ["Ambassador",playerlist[0]]
                    replyauthor = playerlist[challengenum]

                    playerlives,playercredits,playercards,centrecards,revealedcards = await processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,replyauthor)
                except asyncio.exceptions.TimeoutError:
                    #If there was no challenge
                    await message.channel.send("{} has drawn two cards from the centre.".format(playerlist[0].display_name))
                    numdrawing = 2
                    playercards,centrecards = await drawcards(playerlist,playerlives,playercards,centrecards,numdrawing)
                    await message.channel.send("{} has chosen their card.".format(playerlist[0].display_name))
                displayneeded = True
                turnfinished = True
                prevaction = ["None"]
                break

            #Otherwise, it's an invalid command
            await message.channel.send("Invalid command! (Type income, foreignaid, or coup @example to perform those actions, or type the name of the card you wish to use.)")

        #Once it's got the necessary message, take action accordingly

        #Check for Captain
        if prevaction[0] == "Captain":
            targetnum = prevaction[2]
            await message.channel.send("{} has targeted {} with the Captain!".format(prevaction[1].display_name,playerlist[targetnum].display_name))
            await message.channel.send("{} must either challenge, pass, or block with a card that can block stealing.".format(playerlist[targetnum].display_name))
            await message.channel.send("(Other people may also challenge, but may not block.)")
            while True:
                captainreply = await client.wait_for('message', check=channel_check)
                if captainreply.author not in activeplayerlist:
                    continue

                #If someone challenges the claim
                if captainreply.content == "challenge":
                    if captainreply.author == prevaction[1]:
                        await message.channel.send("You cannot challenge your own claim!")
                        continue
                    
                    replyauthor = captainreply.author

                    playerlives,playercredits,playercards,centrecards,revealedcards = await processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,replyauthor)

                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break

                #From here onwards, only take commands from the target
                if captainreply.author != playerlist[targetnum]:
                    await message.channel.send("You are not the target!")
                    continue

                #If the target passes
                if captainreply.content == "pass":
                    await message.channel.send("{} has chosen to pass!".format(playerlist[targetnum].display_name))
                    if playercredits[targetnum] == 1:
                        playercredits[0] += 1
                        await message.channel.send("{} stole 1 credit and now has {}!".format(playerlist[0].display_name,playercredits[0]))
                        playercredits[targetnum] = 0
                        await message.channel.send("{} now has 0 credits!".format(playerlist[targetnum].display_name))
                    else:
                        playercredits[0] += 2
                        await message.channel.send("{} stole 2 credit and now has {}!".format(playerlist[0].display_name,playercredits[0]))
                        playercredits[targetnum] -= 2
                        await message.channel.send("{} now has {} credits!".format(playerlist[targetnum].display_name,playercredits[targetnum]))
                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break

                #If the target blocks
                if captainreply.content.startswith("block"):
                    captainreplylist = captainreply.content.split()
                    if len(captainreplylist) == 2:
                        blockcard = captainreplylist[1]
                        if blockcard == "captain":
                            prevaction = ["Captain Block",captainreply.author]
                            break
                        if blockcard == "ambassador" and "Ambassador" in cardslist:
                            prevaction = ["Ambassador Block",captainreply.author]
                            break
                    await message.channel.send("You must state the card with which you wish to block.")
                    continue                

                #Otherwise, it's an invalid command
                await message.channel.send("Invalid command! (Type challenge, pass, or block with a card e.g. block captain or block ambassador)")

        #Check for Assassin
        if prevaction[0] == "Assassin":
            targetnum = prevaction[2]
            await message.channel.send("{} has targeted {} with the Assassin!".format(prevaction[1].display_name,playerlist[targetnum].display_name))
            await message.channel.send("{} must either challenge, pass, or block with the Contessa.".format(playerlist[targetnum].display_name))
            await message.channel.send("(Other people may also challenge, but may not block.)")
            while True:
                assassinreply = await client.wait_for('message', check=channel_check)
                if assassinreply.author not in activeplayerlist:
                    continue

                #If someone challenges the claim
                if assassinreply.content == "challenge":
                    if assassinreply.author == prevaction[1]:
                        await message.channel.send("You cannot challenge your own claim!")
                        continue
                    
                    replyauthor = assassinreply.author

                    playerlives,playercredits,playercards,centrecards,revealedcards = await processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,replyauthor)

                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break

                #From here onwards, only take commands from the target
                if assassinreply.author != playerlist[targetnum]:
                    await message.channel.send("You are not the target!")
                    continue

                #If the target passes
                if assassinreply.content == "pass":
                    await message.channel.send("{} has chosen to pass!".format(playerlist[targetnum].display_name))

                    deathnum = targetnum
                    playerlives,playercards,revealedcards = await processdeath(client,message,playerlist,playerlives,playercards,revealedcards,deathnum)

                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break
                
                #If the target blocks
                if assassinreply.content == "block" and "Contessa" in cardslist:
                    prevaction = ["Contessa Block",assassinreply.author]
                    break        

                #Otherwise, it's an invalid command
                await message.channel.send("Invalid command! (Type challenge, pass, or block)")

        #Check for Captain/Assassin being blocked
        if prevaction[0] in ["Captain Block","Ambassador Block","Contessa Block"]:
            if prevaction[0] == "Captain Block":
                actioncard = "Captain"
                blockcard = "Captain"
            if prevaction[0] == "Ambassador Block":
                actioncard = "Captain"
                blockcard = "Ambassador"
            if prevaction[0] == "Contessa Block":
                actioncard = "Assassin"
                blockcard = "Contessa"
            await message.channel.send("{} blocked the {} using the {}!".format(prevaction[1].display_name,actioncard,blockcard))
            await message.channel.send("{} must either challenge or pass.".format(playerlist[0].display_name))
            await message.channel.send("(Other people may also challenge.)")
            while True:
                blockreply = await client.wait_for('message', check=channel_check)
                if blockreply.author not in activeplayerlist:
                    continue

                #If someone challenges the claim
                if blockreply.content == "challenge":
                    if blockreply.author == prevaction[1]:
                        await message.channel.send("You cannot challenge your own claim!")
                        continue
                    
                    replyauthor = blockreply.author

                    playerlives,playercredits,playercards,centrecards,revealedcards = await processchallenge(client,message,playerlist,playerlives,playercredits,playercards,centrecards,revealedcards,prevaction,replyauthor)
                    
                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break

                #From here onwards, only take commands from the Captain/Assassin user.
                if reply.author != playerlist[0]:
                    await message.channel.send("You are not the {} user!".format(actioncard))
                    continue

                #If the Captain/Assassin user passes
                if blockreply.content == "pass":
                    await message.channel.send("{} has chosen to pass!".format(playerlist[0].display_name))
                    displayneeded = True
                    turnfinished = True
                    prevaction = ["None"]
                    break

                #Otherwise, it's an invalid command
                await message.channel.send("Invalid command! (Type challenge or pass)")

        #Cycle the players if a turn is finished
        if turnfinished:
            playerlist,playerlives,playercredits,playercards,revealedcards = cycleplayers(playerlist,playerlives,playercredits,playercards,revealedcards)
        
        if displayneeded:
            await displaygame(client,message,playerlist,playerlives,playercredits,centrecards,revealedcards)

    #Deal with game over
    winner = activeplayerlist[0]
    await message.channel.send("The game is over!")
    await message.channel.send("Congratulations to the winner {}!".format(winner.display_name))

client.run('TOKEN')

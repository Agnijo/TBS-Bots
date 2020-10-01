import discord
import random
from helpcommands import *
from utils import *
from botai import *
from elo import *
from random import shuffle
from datetime import datetime
from time import sleep

client = discord.Client()
busyChannels = []
game = discord.Game(name="6 Nimmt!")

maxcardnum = 105
maxplayers = 10
startpts = 66
handsize = 10
numofrows = 4
rowlength = 5

newcards = ["Barricade","Beef Up","First Choice","Ranch Salad"]

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

    if message.content == "!6nimmt":
        if message.channel in busyChannels:
            await message.channel.send("Channel busy with another activity.")
        else:
            busyChannels.append(message.channel)
            await message.channel.send("Starting **6 Nimmt!** in `#"+message.channel.name+"`...")
            await sixnimmt(client,message)
            busyChannels.remove(message.channel)

    if message.content == "!help":
        await helpcommand(client, message)

    if message.content == "!help newcards":
        await helpnewcards(client, message)

    if message.content == "!help bot":
        await helpbot(client, message)
    
    if message.content == "!rules":
        await rules(client, message)

    if message.content.startswith("!elo"):
        messagelist = message.content.split()
        if len(messagelist) > 1:
            messagemention = removeExclamation(messagelist[1])
        else:
            messagemention = removeExclamation(message.author.mention)
        elovalue = fetchelo(messagemention)
        if elovalue == 0:
            await message.channel.send("Could not find an elo for this player.")
        else:
            await message.channel.send("{} has elo {}.".format(messagemention,elovalue))        

async def sixnimmt(client,message):

    #Declarations
    gamestate = 0               #State of game
    playerlist = []             #List of players
    playingbot = False          #Is the bot playing?
    playingnewcards = False     #Are we playing with new cards?
    guaranteednewcards = False  #Are all new cards guaranteed?
    multinewcards = False       #Are there multiple of each new card?
    playerpoints = []           #Number of points each player has
    playercards = []            #Cards possessed by each player
    rows = []                   #Cards in each row
    roweffects = []             #Effects applied to each row (caused by new cards)
    unseencards = set()         #Cards not yet seen by bot
    
    if gamestate == 0:          #Login phase
        gamestate,playerlist,playingbot,playingnewcards,guaranteednewcards,multinewcards,playerpoints = await login(client,message)

    while gamestate == 2 or gamestate == 3:
        if gamestate == 2:      #Dealing cards at start of round
            playercards,rows,roweffects,unseencards = await loadround(client,message,playerlist,playingbot,playingnewcards,guaranteednewcards,multinewcards)
            gamestate = 3
        if gamestate == 3:      #Taking turn
            playerpoints,playercards,rows,roweffects,unseencards = await taketurn(client,message,playerlist,playingbot,playerpoints,playercards,rows,roweffects,unseencards)
            #Check for round or game end
            if len(playercards[0]) == 0:
                gameended = False
                for i in range(len(playerlist)):
                    if playerpoints[i] <= 0:
                        gameended = True
                if gameended:
                    gamestate = 4
                else:
                    gamestate = 2
        if gamestate == 4:      #Game end
            await gameend(client,message,playerlist,playingbot,playerpoints)
    
#Login phase
async def login(client,message):
    gamestate = 1
    playerlist = []
    playingbot = False
    playingnewcards = False
    guaranteednewcards = False
    multinewcards = False
    playerpoints = []
    await message.channel.send("```Login Phase Triggered```\nThe game of 6 Nimmt! is about to begin.\n*Type !join to enter the game. (2-{} players only, or {} if playing with the bot.)*\n".format(maxplayers,maxplayers-1))
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
        replylist = reply.content.split()
        if replylist[0] == "!start" and reply.author in playerlist:
            if len(playerlist) < 2 and "bot" not in replylist:
                await message.channel.send("Cannot start without at least 2 players.")
            else:
                gamemodestr = ""
                if "bot" in replylist and len(playerlist) < maxplayers:
                    playingbot = True
                    playerlist.append(client.user)
                    gamemodestr = gamemodestr + "Bot, "
                if "multinewcards+" in replylist:
                    playingnewcards = True
                    guaranteednewcards = True
                    multinewcards = True
                    gamemodestr = gamemodestr + "Guaranteed multiple new cards, "
                elif "multinewcards" in replylist:
                    playingnewcards = True
                    multinewcards = True
                    gamemodestr = gamemodestr + "Multiple new cards, "                
                elif "newcards+" in replylist:
                    playingnewcards = True
                    guaranteednewcards = True
                    gamemodestr = gamemodestr + "Guaranteed new cards, "
                elif "newcards" in replylist:
                    playingnewcards = True
                    gamemodestr = gamemodestr + "New cards, "
                gamemodestr = gamemodestr.rstrip(", ")
                if gamemodestr != "":
                    gamemodestr = " ({})".format(gamemodestr)
                random.seed(datetime.now())
                playerpoints = [startpts] * len(playerlist)
                await message.channel.send("Game started!{}".format(gamemodestr))
                gamestate = 2
    return gamestate,playerlist,playingbot,playingnewcards,guaranteednewcards,multinewcards,playerpoints

#Shuffles deck and assigns cards
async def loadround(client,message,playerlist,playingbot,playingnewcards,guaranteednewcards,multinewcards):
    if multinewcards:
        actualnewcards = ["First Choice"]
        for i in range(numofrows):
            if i != numofrows - 1:
                actualnewcards.append("Barricade {}".format(i+1))
            actualnewcards.append("Beef Up {}".format(i+1))
            actualnewcards.append("Ranch Salad {}".format(i+1))    
    else:
        actualnewcards = newcards.copy()
    deck = list(range(maxcardnum))
    deck.pop(0)
    numplayercards = len(playerlist)*handsize
    if guaranteednewcards:
        numcards = max([0,numplayercards-len(actualnewcards)])
        shuffle(deck)
        remainingdeck = deck[numcards:]
        deck = deck[:numcards]
    if playingnewcards:
        deck.extend(actualnewcards)
    shuffle(deck)
    playercards = []
    for i in range(len(playerlist)):
        playercards.append(sorthand(deck[:handsize]))
        deck = deck[handsize:]
    if guaranteednewcards:
        deck = remainingdeck
    rows = []
    roweffects = []
    for i in range(numofrows):
        roweffects.append([])
        newcard = deck.pop(0)
        while type(newcard) != int:
            newcard = deck.pop(0)
        rows.append([newcard])
    if playingbot:
        unseencards = set(range(maxcardnum))
        unseencards.discard(0)
        if playingnewcards:
            unseencards.update(actualnewcards)
        for i in range(numofrows):
            unseencards.discard(rows[i][0])
    else:
        unseencards = set()
    await message.channel.send("A new round has started!\nCards have been dealt for the beginning of the new round.")
    numhumans = len(playerlist)
    if playingbot:
        numhumans -= 1
    for i in range(numhumans):
        await playerlist[i].send("A new round has started!\nCards have been dealt for the beginning of the new round.")
    return playercards,rows,roweffects,unseencards

#A turn of 6 nimmt!
async def taketurn(client,message,playerlist,playingbot,playerpoints,playercards,rows,roweffects,unseencards):

    #Remove barricade from roweffects (it only lasts one turn)
    for i in range(len(rows)):
        if "Barricade" in roweffects[i]:
            roweffects[i].remove("Barricade")

    #Number of humans (since bot doesn't need to be DMed), and bot name
    if playingbot:
        numhumans = len(playerlist) - 1
        botname = playerlist[-1].display_name
    else:
        numhumans = len(playerlist)

    humanlist = playerlist[:numhumans]

    #Send to channel and all humans
    async def sendtoall(humanlist,messagestr):
        await message.channel.send(messagestr)
        for i in range(len(humanlist)):
            await humanlist[i].send(messagestr)

    #Displays current state of game (and sends table to all humans(
    messagestring = ""
    for i in range(len(playerlist)):
        messagestring = messagestring + "{} has {} points.\n".format(playerlist[i].display_name,playerpoints[i])
    await sendtoall(humanlist,messagestring)
    await sendtoall(humanlist,tablestring(rowlength,rows,roweffects))

    playedcards = [0] * len(playerlist)

    #Shows every human their hands (and the table)
    playertablemessages = []
    for i in range(numhumans):
        handstring = ""
        for j in range(len(playercards[i])):
            handstring = handstring + str(playercards[i][j]) + ", "
        handstring = handstring.rstrip(", ")
        await playerlist[i].send("Your hand is:\n{}\nType the card you wish to play.".format(handstring))

    #Check if card played is valid
    def card_check(msg):
        if dmCheck(msg.channel) and msg.author in playerlist:
            return True
        return False

    #If bot is playing, generate bot's card from its AI
    if playingbot:
        playedcards[-1] = botchoosecard(playercards[-1],unseencards,rowlength,rows,roweffects,numhumans)
        await message.channel.send("{} has chosen their card!".format(botname))

    #Gets everyone's played cards
    while 0 in playedcards:
        cardmessage = await client.wait_for("message", check=card_check)
        for i in range(numhumans):
            if cardmessage.author == playerlist[i]:
                validcard = False
                for j in range(len(playercards[i])):
                    if cardmessage.content == str(playercards[i][j]):
                        validcard = True
                        await playerlist[i].send("You have chosen to play {}.".format(playercards[i][j]))
                        if playedcards[i] == 0:
                            await message.channel.send("{} has chosen their card!".format(playerlist[i].display_name))
                        playedcards[i] = playercards[i][j]
                if not validcard:
                    await playerlist[i].send("Invalid card.")

    #Removes played cards from hands
    for i in range(len(playerlist)):
        cardindex = 0
        for j in range(len(playercards[i])):
            if playedcards[i] == playercards[i][j]:
                cardindex = j
        playercards[i].pop(cardindex)

    #Bot has now seen played cards
    unseencards.difference_update(playedcards)

    #Determines player order
    sortedplayedcards = sorthand(playedcards)
    playerorder = []
    for i in range(len(playerlist)):
        for j in range(len(playerlist)):
            if playedcards[j] == sortedplayedcards[i]:
                playerorder.append(j)
    playermessages = []
    messagestring = ""
    for i in range(len(playerlist)):
        messagestring = messagestring + "{} played {}!\n".format(playerlist[playerorder[i]].display_name,sortedplayedcards[i])
    await sendtoall(humanlist,messagestring)

    #Displays table to all players
    tablemessage = await message.channel.send(tablestring(rowlength,rows,roweffects))
    playertablemessages = []
    for i in range(len(humanlist)):
        playertablemessages.append(await playerlist[i].send(tablestring(rowlength,rows,roweffects)))

    rightcards = []
    for i in range(numofrows):
        rightcards.append(rows[i][-1])

    for i in range(len(playerlist)):

        sleep(3)

        curplayer = playerlist[playerorder[i]]

        #Is this the bot's card?
        botplayingnow = False
        if playingbot and playerorder[i] == len(playerlist)-1:
            botplayingnow = True

        def choose_row_check(msg):
            if msg.author == curplayer:
                if msg.channel == message.channel or dmCheck(msg.channel):
                    try: 
                        rownum = int(msg.content)
                    except ValueError:
                        return False
                    if rownum > 0 and rownum <= numofrows:
                        if "Barricade" in roweffects[rownum-1]:
                            return False
                        return True
            return False
        
        cardplayed = sortedplayedcards[i]
        
        #If card played is special
        if type(cardplayed) != int:
            if cardplayed.startswith("Barricade"):
                if botplayingnow:
                    cardrow = botchooserow(sortedplayedcards,i,rowlength,rows,roweffects)
                    await sendtoall(humanlist,"{} barricaded row {}!".format(botname,cardrow+1))
                else:
                    await message.channel.send("{} must choose which row to barricade.\n(Type a number between 1 and {})".format(curplayer.mention,numofrows))
                    await curplayer.send("You must choose which row to barricade.\n(Type a number between 1 and {})".format(numofrows))
                    rowmessage = await client.wait_for("message", check=choose_row_check)
                    await sendtoall(humanlist,"{} barricaded row {}!".format(curplayer.display_name,rowmessage.content))
                    cardrow = int(rowmessage.content)-1
                roweffects[cardrow].append("Barricade")
                roweffects[cardrow] = sorthand(roweffects[cardrow])            
            elif cardplayed.startswith("Beef Up"):
                if botplayingnow:
                    cardrow = botchooserow(sortedplayedcards,i,rowlength,rows,roweffects)
                    await sendtoall(humanlist,"{} beefed up row {}!".format(botname,cardrow+1))
                else:
                    await message.channel.send("{} must choose which row to beef up.\n(Type a number between 1 and {})".format(curplayer.mention,numofrows))
                    await curplayer.send("You must choose which row to beef up.\n(Type a number between 1 and {})".format(numofrows))
                    rowmessage = await client.wait_for("message", check=choose_row_check)
                    await sendtoall(humanlist,"{} beefed up row {}!".format(curplayer.display_name,rowmessage.content))
                    cardrow = int(rowmessage.content)-1
                roweffects[cardrow].append("Beef Up")
                roweffects[cardrow] = sorthand(roweffects[cardrow])
            elif cardplayed == "First Choice":
                if botplayingnow:
                    cardrow = botchooserow(sortedplayedcards,i,rowlength,rows,roweffects)
                    await sendtoall(humanlist,"{} made row {} First Choice!".format(botname,cardrow+1))
                else:
                    await message.channel.send("{} must choose which row to to make First Choice.\n(Type a number between 1 and {})".format(curplayer.mention,numofrows))
                    await curplayer.send("You must choose which row to make First Choice.\n(Type a number between 1 and {})".format(numofrows))
                    rowmessage = await client.wait_for("message", check=choose_row_check)
                    await sendtoall(humanlist,"{} made row {} First Choice!".format(curplayer.display_name,rowmessage.content))
                    cardrow = int(rowmessage.content)-1
                roweffects[cardrow].append("First Choice")
                roweffects[cardrow] = sorthand(roweffects[cardrow])
            elif cardplayed.startswith("Ranch Salad"):
                if botplayingnow:
                    cardrow = botchooserow(sortedplayedcards,i,rowlength,rows,roweffects)
                    await sendtoall(humanlist,"{} used Ranch Salad on row {}!".format(botname,cardrow+1))
                else:
                    await message.channel.send("{} must choose which row to use Ranch Salad on.\n(Type a number between 1 and {})".format(curplayer.mention,numofrows))
                    await curplayer.send("You must choose which row to use Ranch Salad on.\n(Type a number between 1 and {})".format(numofrows))
                    rowmessage = await client.wait_for("message", check=choose_row_check)
                    await sendtoall(humanlist,"{} used Ranch Salad on row {}!".format(curplayer.display_name,rowmessage.content))
                    cardrow = int(rowmessage.content)-1
                roweffects[cardrow].append("Ranch Salad")
                roweffects[cardrow] = sorthand(roweffects[cardrow])
        else:
            #Determines which row a card should go in, if any
            maxright = 0
            cardrow = -1
            for j in range(numofrows):
                if rightcards[j] < cardplayed and rightcards[j] > maxright and "Barricade" not in roweffects[j]:
                    maxright = rightcards[j]
                    cardrow = j

            #If the card is too low to go in any row:
            if cardrow == -1:
                firstchoicerow = -1
                for j in range(numofrows):
                    if "First Choice" in roweffects[j] and "Barricade" not in roweffects[j]:
                        firstchoicerow = j
                #If row is not forced by First Choice:
                if firstchoicerow == -1:
                    if botplayingnow:
                        cardrow = botchooserow(sortedplayedcards,i,rowlength,rows,roweffects)
                        await sendtoall(humanlist,"{} took row {}!".format(botname,cardrow+1))
                    else:
                        await message.channel.send("{} played {} and must therefore choose which row to take.\n(Type a number between 1 and {})".format(curplayer.mention,cardplayed,numofrows))
                        await curplayer.send("You must choose which row to take.\n(Type a number between 1 and {})".format(numofrows))
                        rowmessage = await client.wait_for("message", check=choose_row_check)
                        await sendtoall(humanlist,"{} took row {}!".format(curplayer.display_name,rowmessage.content))
                        cardrow = int(rowmessage.content)-1
                else:
                    await sendtoall(humanlist,"{} took row {} because of First Choice!".format(curplayer.display_name,firstchoicerow+1))
                    cardrow = firstchoicerow
                beeftaken = rowbeefcalc(rows[cardrow],roweffects[cardrow])
                roweffects[cardrow] = []
                await sendtoall(humanlist,"{} took {} beef heads!".format(curplayer.display_name,beeftaken))
                playerpoints[playerorder[i]] -= beeftaken
                rows[cardrow] = [cardplayed]
                rightcards[cardrow] = cardplayed
            #If it is going into a full row:
            elif len(rows[cardrow]) == rowlength:
                beeftaken = rowbeefcalc(rows[cardrow],roweffects[cardrow])
                roweffects[cardrow] = []
                await sendtoall(humanlist,"{} took {} beef heads!".format(curplayer.display_name,beeftaken))
                playerpoints[playerorder[i]] -= beeftaken
                rows[cardrow] = [cardplayed]
                rightcards[cardrow] = cardplayed
            #Otherwise, put it at the end of the correct row.
            else:
                rows[cardrow].append(cardplayed)
                rightcards[cardrow] = cardplayed

        #Edit tablemessage
        await tablemessage.edit(content=tablestring(rowlength,rows,roweffects))
        for i in range(len(humanlist)):
            await playertablemessages[i].edit(content=tablestring(rowlength,rows,roweffects))

    return playerpoints,playercards,rows,roweffects,unseencards

#End of game
async def gameend(client,message,playerlist,playingbot,playerpoints):
    numhumans = len(playerlist)
    if playingbot:
        numhumans -= 1
    for i in range(numhumans):
        await playerlist[i].send("The game has ended!")
    messagestring = "The game has ended!\n"
    maxscore = playerpoints[0]-1
    winlist = []
    for i in range(len(playerlist)):
        messagestring = messagestring + "{} finished with {} points!\n".format(playerlist[i].display_name,playerpoints[i])
        if playerpoints[i] == maxscore:
            winlist.append(i)
        elif playerpoints[i] > maxscore:
            maxscore = playerpoints[i]
            winlist = [i]
    #If the winner is unique
    if len(winlist) == 1:
        messagestring = messagestring + "{} is the winner!".format(playerlist[winlist[0]].display_name)
    else:
        winstring = ""
        for j in range(len(winlist)):
            winstring = "{}, ".format(playerlist[winlist[j]].display_name)
        winstring = winstring.rstrip(", ")
        winstring = winstring + " are the joint winners!"
        messagestring = messagestring + winstring
    await message.channel.send(messagestring)
    #Deal with elos
    playerelochange,newplayerelo = updateelos(playerlist,playerpoints)
    messagestring = ""
    for i in range(len(playerlist)):
        if playerelochange[i] >= 0:
            messagestring = messagestring + "{} has gained {} elo points and has a new elo of {}.\n".format(playerlist[i].display_name,playerelochange[i],newplayerelo[i])
        else:
            messagestring = messagestring + "{} has lost {} elo points and has a new elo of {}.\n".format(playerlist[i].display_name,-playerelochange[i],newplayerelo[i])
    await message.channel.send(messagestring)

client.run('TOKEN')

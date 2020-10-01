import discord
import random
from helpcommands import *
from elo import *
from datetime import datetime
from random import shuffle,randint

client = discord.Client()
busyChannels = []
game = discord.Game(name="Perudo")

diefaces = 6                        #Number of faces on a die
startingdice = 5                    #How many dice each player starts with
maxplayers = 6                      #Maximum number of players

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

    if message.content == "!perudo":
        if message.channel in busyChannels:
            await message.channel.send("Channel busy with another activity.")
        else:
            busyChannels.append(message.channel)
            await message.channel.send("Starting **Perudo** in `#"+message.channel.name+"`...")
            await perudo(client,message)
            busyChannels.remove(message.channel)

    if message.content == "!help":
        await helpcommand(client, message)

    if message.content == "!help abilities":
        await helpabilities(client, message)
    
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

async def perudo(client,message):

    #Declarations
    gamestate = 0               #State of game
    playerlist = []             #List of players
    freebidding = False         #Can players bid freely, or are they restricted to BGA rules?
    calza = False               #Can players call calza to gain dice?
    abilities = False           #Do players have their special abilities?
    playerposition = []         #Position of each player (1 for first, 2 for second, and so on)
    activeplayerlist = []       #List of players who are still in
    playerdicenum = []          #Number of dice each player has
    playerdice = []             #Each player's dice
    playerabilities = []        #Each player's abilities (0 is not unlocked, 1 is unlocked, 2 is used) 
    curplayer = 0               #Current player
    firstturn = True            #Is this the first turn of the round?
    palifico = False            #Is this a palifico round?
    currentbid = []             #Current bid (e.g.[5,6] means five sixes)

    if gamestate == 0:          #Login phase
        gamestate,playerlist,freebidding,calza,abilities,playerposition,activeplayerlist,playerdicenum,playerabilities = await login(client,message)
        curplayer = 0

    while gamestate == 2 or gamestate == 3:
        if gamestate == 2:      #Rolling dice at start of round
            playerdice = await rolldice(client,message,activeplayerlist,playerdicenum,palifico)
            firstturn = True
            currentbid = []
            gamestate = 3

        if gamestate == 3:      #Taking a turn
            gamestate,playerposition,activeplayerlist,playerdicenum,playerdice,playerabilities,curplayer,firstturn,palifico,currentbid = await taketurn(client,message,playerlist,freebidding,calza,abilities,playerposition,activeplayerlist,playerdicenum,playerdice,playerabilities,curplayer,firstturn,palifico,currentbid)

    if gamestate == 4:          #End of game
        await gameend(client,message,playerlist,playerposition)

#Login phase
async def login(client,message):
    gamestate = 1
    playerlist = []
    freebidding = False
    calza = False
    abilities = False
    playerdicenum = []
    playerabilities = []
    await message.channel.send("```Login Phase Triggered```\nThe game of Perudo is about to begin.\n*Type !join to enter the game. (2-{} players only.)*\n".format(maxplayers))
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
            if len(playerlist) < 2:
                await message.channel.send("Not enough players.")
            else:
                gamemodestr = ""
                if "freebidding" in replylist:
                    freebidding = True
                    gamemodestr = gamemodestr + "Free bidding, "
                if "calza" in replylist:
                    calza = True
                    gamemodestr = gamemodestr + "Calza, "
                if "abilities" in replylist:
                    abilities = True
                    gamemodestr = gamemodestr + "Special abilities, "
                    for i in range(len(playerlist)):
                        playerabilities.append([0,0,0])
                gamemodestr = gamemodestr.rstrip(", ")
                if gamemodestr != "":
                    gamemodestr = " ({})".format(gamemodestr)
                random.seed(datetime.now())
                shuffle(playerlist)
                playerposition = [1] * len(playerlist)
                activeplayerlist = playerlist.copy()
                playerdicenum = [startingdice] * len(playerlist)
                await message.channel.send("Game started!{}".format(gamemodestr))
                gamestate = 2
    return gamestate,playerlist,freebidding,calza,abilities,playerposition,activeplayerlist,playerdicenum,playerabilities

async def rolldice(client,message,activeplayerlist,playerdicenum,palifico):
    #Rolls dice and shows each player their dice
    playerdice = []
    for i in range(len(activeplayerlist)):
        playerdice.append([])
        for j in range(playerdicenum[i]):
            playerdice[i].append(randint(1,diefaces))
        playerdice[i].sort()
        dicestr = ""
        for j in range(len(playerdice[i])):
            dicestr = dicestr + str(playerdice[i][j]) + ", "
        dicestr = dicestr.rstrip(", ")
        await activeplayerlist[i].send("You rolled:\n{}".format(dicestr))

    #Displays message at start of each round
    messagestring = "Dice have been rolled for the start of this round.\n"
    for i in range(len(activeplayerlist)):
        messagestring = messagestring + "{} has {} dice\n".format(activeplayerlist[i].display_name,playerdicenum[i])
    if palifico:
        messagestring = messagestring + "This is a palifico round!"
    await message.channel.send(messagestring)
    return playerdice

async def taketurn(client,message,playerlist,freebidding,calza,abilities,playerposition,activeplayerlist,playerdicenum,playerdice,playerabilities,curplayer,firstturn,palifico,currentbid):
    def player_check(m):
        if m.channel == message.channel and m.author in activeplayerlist:
            return True
        return False

    #Function for revealing counting dice at end of round
    async def diecount(client,message,activeplayerlist,playerdice,palifico,currentbid):
        messagestring = ""
        numdice = [0] * diefaces
        for i in range(len(activeplayerlist)):
            playerstr = ""
            for j in range(len(playerdice[i])):
                playerstr = playerstr + str(playerdice[i][j]) + ", "
                numdice[playerdice[i][j]-1] += 1
            playerstr = playerstr.rstrip(", ")
            messagestring = messagestring + "{} had {}\n".format(activeplayerlist[i].display_name,playerstr)
        await message.channel.send(messagestring)
        
        if currentbid[1] == 1 or palifico:
            numofbid = numdice[currentbid[1]-1]
        else:
            numofbid = numdice[0] + numdice[currentbid[1]-1]

        await message.channel.send("There were {} {}s!".format(numofbid,currentbid[1]))

        return numofbid
    
    await message.channel.send("It is {}'s turn.".format(activeplayerlist[curplayer].display_name))
    waiting = True
    while waiting:
        command = await client.wait_for('message', check=player_check)

        losingplayer = 0
        playerlosedie = False       #Did someone lose a die?

        #Check for calza
        if command.content == "calza":
            if not calza:
                await message.channel.send("Calling calza is disabled.")
                continue
            if firstturn:
                await message.channel.send("You cannot call calza on the first turn.")
                continue
            if command.author == activeplayerlist[curplayer-1]:
                await message.channel.send("You cannot call calza on your own bid.")
                continue

            numofbid = await diecount(client,message,activeplayerlist,playerdice,palifico,currentbid)

            prevplayer = curplayer - 1
            
            for i in range(len(activeplayerlist)):
                if command.author == activeplayerlist[i]:
                    curplayer = i

            if currentbid[0] == numofbid:
                await message.channel.send("{} called calza successfully on {}!".format(activeplayerlist[curplayer].display_name,activeplayerlist[prevplayer].display_name))
                newdicenum = playerdicenum[curplayer]+1
                if newdicenum > startingdice:
                    newdicenum = startingdice
                    await message.channel.send("{} was at the maximum number of dice and thus has {} dice.".format(activeplayerlist[curplayer].display_name,newdicenum))
                else:
                    await message.channel.send("{} has gained a die and now has {} dice.".format(activeplayerlist[curplayer].display_name,newdicenum))
                playerdicenum[curplayer] = newdicenum
                gamestate = 2
                palifico = False
                break
            else:
                losingplayer = curplayer
                await message.channel.send("{} called calza unsuccessfully on {}!".format(activeplayerlist[curplayer].display_name,activeplayerlist[prevplayer].display_name))
                playerlosedie = True
        
        if command.author != activeplayerlist[curplayer]:
            await message.channel.send("It is not your turn!")
            continue

        #Check for dudo
        if command.content == "dudo":
            if firstturn:
                await message.channel.send("You cannot call dudo on the first turn.")
                continue

            #Dudo has been called! Reveal everyone's dice
            numofbid = await diecount(client,message,activeplayerlist,playerdice,palifico,currentbid)

            prevplayer = curplayer - 1

            if currentbid[0] > numofbid:
                losingplayer = prevplayer
                await message.channel.send("{} called dudo successfully on {}!".format(activeplayerlist[curplayer].display_name,activeplayerlist[prevplayer].display_name))
            else:
                losingplayer = curplayer
                await message.channel.send("{} called dudo unsuccessfully on {}!".format(activeplayerlist[curplayer].display_name,activeplayerlist[prevplayer].display_name))
            playerlosedie = True

        #If someone lost a die
        if playerlosedie:
            newdicenum = playerdicenum[losingplayer]-1
            playerdicenum[losingplayer] = newdicenum
            await message.channel.send("{} has lost a die and now has {} dice.".format(activeplayerlist[losingplayer].display_name,newdicenum))

            if newdicenum == 1:
                palifico = True
            else:
                palifico = False

            #Do they gain abilities?
            if abilities:
                if newdicenum == 3 and playerabilities[losingplayer][0] == 0:
                    await message.channel.send("{} unlocked the ability to match the previous bid! (Type \"match\" to use.)".format(activeplayerlist[losingplayer].display_name))
                    playerabilities[losingplayer][0] = 1
                if newdicenum == 2 and playerabilities[losingplayer][1] == 0:
                    await message.channel.send("{} unlocked the ability to reroll their own dice! (Type \"reroll\" to use.)".format(activeplayerlist[losingplayer].display_name))
                    playerabilities[losingplayer][1] = 1
                if newdicenum == 1 and playerabilities[losingplayer][2] == 0:
                    await message.channel.send("{} unlocked the ability to see another player's dice! (Type \"see @playername\" to use.)".format(activeplayerlist[losingplayer].display_name))
                    playerabilities[losingplayer][2] = 1
            curplayer = losingplayer

            if newdicenum == 0:
                await message.channel.send("{} is out of the game!".format(activeplayerlist[losingplayer].display_name))
                actualplayer = 0
                for i in range(len(playerlist)):
                    if playerlist[i] == activeplayerlist[curplayer]:
                        actualplayer = i
                playerposition[actualplayer] = len(activeplayerlist)
                activeplayerlist.pop(curplayer)
                playerdicenum.pop(curplayer)
                if abilities:
                    playerabilities.pop(curplayer)
                if curplayer == len(activeplayerlist) or curplayer == -1:
                    curplayer = 0

            if len(activeplayerlist) == 1:
                gamestate = 4
            else:
                gamestate = 2
            break

        commandlist = command.content.split()

        #Check for use of abilities
        #Match bid:
        if command.content == "match":
            if not abilities:
                await message.channel.send("Abilities are disabled.")
                continue
            if playerabilities[curplayer][0] == 0:
                await message.channel.send("You have not yet unlocked this ability.")
                continue
            if playerabilities[curplayer][0] == 2:
                await message.channel.send("You have already used this ability.")
                continue
            if firstturn:
                await message.channel.send("You cannot match on the first turn.")
                continue
            await message.channel.send("{} matched the previous bid!".format(activeplayerlist[curplayer].display_name))
            playerabilities[curplayer][0] = 2
            gamestate = 3
            firstturn = False
            curplayer += 1
            if curplayer == len(activeplayerlist):
                curplayer = 0
            break
        #Reroll dice:
        if command.content == "reroll":
            if not abilities:
                await message.channel.send("Abilities are disabled.")
                continue
            if playerabilities[curplayer][1] == 0:
                await message.channel.send("You have not yet unlocked this ability.")
                continue
            if playerabilities[curplayer][1] == 2:
                await message.channel.send("You have already used this ability.")
                continue
            await message.channel.send("{} rerolled!".format(activeplayerlist[curplayer].display_name))
            playerabilities[curplayer][1] = 2
            for i in range(len(playerdice[curplayer])):
                playerdice[curplayer][i] = randint(1,diefaces)
            playerdice[curplayer].sort()
            dicestr = ""
            for i in range(len(playerdice[curplayer])):
                dicestr = dicestr + str(playerdice[curplayer][i]) + ", "
            dicestr = dicestr.rstrip(", ")
            await activeplayerlist[curplayer].send("You rolled:\n{}".format(dicestr))
            continue
        #See other player's dice:
        if commandlist[0] == "see":
            if not abilities:
                await message.channel.send("Abilities are disabled.")
                continue
            if playerabilities[curplayer][2] == 0:
                await message.channel.send("You have not yet unlocked this ability.")
                continue
            if playerabilities[curplayer][2] == 2:
                await message.channel.send("You have already used this ability.")
                continue
            targetstr = commandlist[1]
            if len(targetstr) > 2:
                if targetstr[2]=="!":
                    targetstr="<@"+targetstr[3:]
            targetnum = -1
            for i in range(len(activeplayerlist)):
                mentionstr = activeplayerlist[i].mention
                if len(mentionstr) > 2:
                    if mentionstr[2]=="!":
                        mentionstr="<@"+mentionstr[3:]
                if mentionstr == targetstr:
                    targetnum = i
            if targetnum == -1:
                await message.channel.send("Invalid command.\nType \"see @playername\" to see their dice.")
                continue
            await message.channel.send("{} saw {}'s dice!.".format(activeplayerlist[curplayer].display_name,activeplayerlist[targetnum].display_name))
            playerabilities[curplayer][2] = 2
            dicestr = ""
            for i in range(len(playerdice[targetnum])):
                dicestr = dicestr + str(playerdice[targetnum][i]) + ", "
            dicestr = dicestr.rstrip(", ")
            await activeplayerlist[curplayer].send("{} has:\n{}".format(activeplayerlist[targetnum].display_name,dicestr))
            continue
        
        badcommand = False
        if len(commandlist) != 2:
            badcommand = True
        else:
            try:
                numdicebid = int(commandlist[0])
                valdicebid = int(commandlist[1])
                assert numdicebid > 0
                assert valdicebid > 0
                assert valdicebid <= diefaces
            except:
                badcommand = True
        if badcommand:
            await message.channel.send("Invalid command.\nType the number of dice you wish to bid followed by the value you wish to bid.\n(e.g. Type \"5 6\" to bid 5 sixes)")
            continue

        #Now the bid is well-formed (though not necessarily legal)
        if not firstturn and palifico and valdicebid != currentbid[1]:
            await message.channel.send("In palifico, you cannot change the number.")
            continue
        if freebidding:
            if not firstturn:
                if currentbid[1] == 1:
                    oldvalue = (currentbid[0]*2+1)*diefaces + 1
                else:
                    oldvalue = currentbid[0]*diefaces + currentbid[1]
                if valdicebid == 1:
                    newvalue = (numdicebid*2+1)*diefaces + 1
                else:
                    newvalue = numdicebid*diefaces + valdicebid
                if newvalue <= oldvalue:
                    await message.channel.send("You must increase the value of the bid.")
                    continue
        else:
            if firstturn:
                if valdicebid == 1 and not palifico:
                    await message.channel.send("You cannot bid ones on the first turn, except in palifico.")
                    continue
            else:
                if valdicebid < currentbid[1] and valdicebid != 1:
                    await message.channel.send("You cannot bid a lower number, unless you are bidding 1.")
                    continue
                if valdicebid == currentbid[1] and numdicebid <= currentbid[0]:
                    await message.channel.send("If you are bidding the same number, you must increase the number of dice.")
                    continue
                if valdicebid > currentbid[1] and currentbid[1] != 1 and numdicebid != currentbid[0]:
                    await message.channel.send("If you are bidding a higher number, you must bid the same number of dice.")
                    continue
                if valdicebid != 1 and currentbid[1] == 1 and numdicebid <= currentbid[0]*2:
                    await message.channel.send("You must bid strictly more than twice the previous bid.")
                    continue
                if valdicebid == 1 and currentbid[1] != 1 and currentbid[0] > numdicebid*2:
                    await message.channel.send("If you are bidding 1, you must bid at least half the previous bid.")
                    continue

        #Bid should be legal now.
        currentbid = [numdicebid,valdicebid]
        gamestate = 3
        firstturn = False
        curplayer += 1
        if curplayer == len(activeplayerlist):
            curplayer = 0
        waiting = False
        
    return gamestate,playerposition,activeplayerlist,playerdicenum,playerdice,playerabilities,curplayer,firstturn,palifico,currentbid
    
#End of game
async def gameend(client,message,playerlist,playerposition):
    await message.channel.send("The game has ended! The leaderboard is:")
    messagestring = ""
    sortedplayerlist = []
    for i in range(len(playerlist)):
        for j in range(len(playerlist)):
            if playerposition[j] == i+1:
                sortedplayerlist.append(playerlist[j])
                messagestring = messagestring + "{}: {}\n".format(i+1,playerlist[j].display_name)
    messagestring = messagestring + "Congratulations to {}, the winner!".format(sortedplayerlist[0].display_name)
    await message.channel.send(messagestring)

    #Deal with elos
    playerpoints = []
    for i in range(len(playerlist)):
        playerpoints.append(len(playerlist)-playerposition[i])
    playerelochange,newplayerelo = updateelos(playerlist,playerpoints)
    messagestring = ""
    for i in range(len(playerlist)):
        if playerelochange[i] >= 0:
            messagestring = messagestring + "{} has gained {} elo points and has a new elo of {}.\n".format(playerlist[i].display_name,playerelochange[i],newplayerelo[i])
        else:
            messagestring = messagestring + "{} has lost {} elo points and has a new elo of {}.\n".format(playerlist[i].display_name,-playerelochange[i],newplayerelo[i])
    await message.channel.send(messagestring)


client.run('TOKEN')

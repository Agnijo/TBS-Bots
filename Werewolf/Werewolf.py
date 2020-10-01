import discord
import random
from helpcommands import *
from utils import *
import copy
from datetime import datetime
from random import shuffle
import asyncio

client = discord.Client()
busyChannels = []
game = discord.Game(name="Werewolf")

minplayers = 4                  #Minimum number of players
maxplayers = 13                 #Maximum number of players
daytimer = 10                   #How many minutes the day should last
centrecards = 3                 #How many centre cards are there?

#List of roles
roles = ["Doppelganger","Werewolf","Minion","Apprentice Tanner","Mason","Seer","Apprentice Seer","Robber","Troublemaker","Village Idiot","Drunk","Insomniac","Squire","Villager","Hunter","Tanner"]

#Roles that there can be multiple of
multiroles = ["Werewolf","Mason","Villager"]

#Roles that cannot pass on their action
cannotpass = ["Doppelganger","Drunk"]

#Roles that automatically pass if the Doppelganger gets them
doppelpass = ["Werewolf","Minion","Apprentice Tanner","Mason","Insomniac","Squire","Villager","Hunter","Tanner"]

#Order of roles to be displayed during day
roleorder = ["Doppelganger","Werewolf","Minion","Apprentice Tanner","Mason","Seer","Apprentice Seer","Robber","Troublemaker","Village Idiot","Drunk","Insomniac","Squire"]

#Default roles for different numbers of players
defaultroles = [
["Doppelganger","Werewolf","Werewolf","Seer","Robber","Troublemaker","Drunk"],
["Doppelganger","Werewolf","Werewolf","Seer","Robber","Troublemaker","Drunk","Insomniac"],
["Doppelganger","Werewolf","Werewolf","Seer","Robber","Troublemaker","Drunk","Insomniac","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Seer","Robber","Troublemaker","Drunk","Insomniac","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Seer","Robber","Troublemaker","Drunk","Insomniac","Hunter","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Mason","Mason","Seer","Robber","Troublemaker","Drunk","Insomniac","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Mason","Mason","Seer","Robber","Troublemaker","Drunk","Insomniac","Hunter","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Mason","Mason","Seer","Robber","Troublemaker","Drunk","Insomniac","Villager","Hunter","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Mason","Mason","Seer","Robber","Troublemaker","Drunk","Insomniac","Villager","Villager","Hunter","Tanner"],
["Doppelganger","Werewolf","Werewolf","Minion","Mason","Mason","Seer","Robber","Troublemaker","Drunk","Insomniac","Villager","Villager","Villager","Hunter","Tanner"]
]

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

    if message.content == "!werewolf":
        if message.channel in busyChannels:
            await message.channel.send("Channel busy with another activity.")
        else:
            busyChannels.append(message.channel)
            await message.channel.send("Starting **Werewolf** in `#"+message.channel.name+"`...")
            await werewolf(client,message)
            busyChannels.remove(message.channel)

    if message.content == "!help":
        await helpcommand(client, message)

    if message.content == "!roles":
        await helproles(client, message)
    
    if message.content == "!rules":
        await rules(client, message)

async def werewolf(client,message):

    #Declarations
    gamestate = 0               #State of game
    playerlist = []             #List of players
    roleslist = []              #List of roles in the game
    startplayerroles = []       #Initial roles given to players
    startcentreroles = []       #Initial roles in the centre
    nightactionlist = []        #List of night actions taken
    doppelrole = "Doppelganger" #What the Doppelganger becomes
    finalplayerroles = []       #Each player's final role
    finalcentreroles = []       #Final roles in the centre
    nightactionstr = ""         #String keeping track of night actions

    if gamestate == 0:          #Login phase
        gamestate,playerlist = await login(client,message)
    if gamestate == 2:          #Role choosing phase
        gamestate,roleslist = await chooseroles(client,message,playerlist)
    if gamestate == 3:
        startplayerroles,startcentreroles = giveroles(centrecards,roleslist)
        #Night phase
        nightactionlist,doppelrole = await night(client,message,playerlist,startplayerroles)
        #Resolve night actions
        finalplayerroles,finalcentreroles,nightactionstr = await resolvenight(client,message,playerlist,startplayerroles,startcentreroles,nightactionlist,doppelrole)
        #Day start
        await day(client,message,playerlist,roleslist)
        #Vote phase
        await vote(client,message,playerlist,startplayerroles,startcentreroles,nightactionlist,doppelrole,finalplayerroles,finalcentreroles,nightactionstr)

#Login phase
async def login(client,message):
    gamestate = 1
    playerlist = []
    await message.channel.send("```Login Phase Triggered```\nThe game of Werewolf is about to begin.\n*Type !join to enter the game. ({}-{} players only.)*\n".format(minplayers,maxplayers))
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

#Choosing which roles will be in play
async def chooseroles(client,message,playerlist):
    gamestate = 2
    roleslist = defaultroles[len(playerlist)-minplayers].copy()
    await message.channel.send("```Role Choosing Phase Triggered```")
    await roledisplay(client,message,roleslist,roles,0)
    while gamestate == 2:
        def player_check(m):
            return m.channel == message.channel and m.author in playerlist
        reply = await client.wait_for("message", check=player_check)
        replylist = reply.content.split()
        if replylist[0] == "!add":
            for i in range(len(replylist)):
                for j in range(len(roles)):
                    roleshortstr = "".join(roles[j].lower().split())
                    if replylist[i] == roleshortstr:
                        if roles[j] not in roleslist or roles[j] in multiroles:
                            roleslist.append(roles[j])
            await message.channel.send("Roles have been added.")
            await roledisplay(client,message,roleslist,roles,0)
        if replylist[0] == "!remove":
            for i in range(len(replylist)):
                for j in range(len(roles)):
                    roleshortstr = "".join(roles[j].lower().split())
                    if replylist[i] == roleshortstr and roles[j] in roleslist:
                        roleslist.remove(roles[j])
            await message.channel.send("Roles have been removed.")
            await roledisplay(client,message,roleslist,roles,0)
        if replylist[0] == "!stop":
            await message.channel.send("The game has been stopped.")
            gamestate = 0
        if replylist[0] == "!start":
            if len(roleslist) == len(playerlist)+centrecards:
                await roledisplay(client,message,roleslist,roles,1)
                gamestate = 3
            else:
                await message.channel.send("There are currently {} roles. {} needed to start.".format(len(roleslist),len(playerlist)+centrecards))
    return gamestate,roleslist

#Night phase
async def night(client,message,playerlist,startplayerroles):
    await message.channel.send("```Night Phase Triggered```")
    playerstr = playerstring(playerlist)
    await message.channel.send("List of players:\n{}".format(playerstr))
    acted = [False] * len(playerlist)
    nightactionlist = []
    doppelrole = "Doppelganger"
    doppelaction = []

    #Display each person's role and what they need to know
    async def roleinfo(player,role,playerstr,doppel):
        if doppel:
            passstring = ""
        else:
            passstring = "\nYou do not have any night actions so type \"pass\" to continue."
        if role == "Doppelganger":
            await player.send("You are a Doppelganger.\nYou must choose another player's card.\nYou will then become that role and perform the appropriate night action.\nYou will gain the win condition of the role you chose.\n\nThe numbering of players is as follows:")
            await player.send(playerstr)
            await player.send("To copy someone else's role, type the number of that player. (You may not pass)")
        if role == "Werewolf":
            if doppel:
                await player.send("You are a Werewolf.\nYou win with the Werewolves, if no Werewolves or Tanners are killed.\nYou will be informed of your fellow Werewolves at the end of the night.\n")
            else:
                await player.send("You are a Werewolf.\nYou win with the Werewolves, if no Werewolves or Tanners are killed.\nYou will be informed of your fellow Werewolves, if any, at the end of the night.\nYou can now choose the centre card that you will look at, in the event that you are a lone Werewolf.\nType \"1\", \"2\", or \"3\" to choose a centre card to look at, or \"pass\" to do nothing.")
        if role == "Minion":
            await player.send("You are a Minion.\nYou win with the Werewolves, if no Werewolves or Tanners are killed.\nHowever, you yourself are not a Werewolf so if only you are killed you still win.\nYou will be informed of the Werewolves, if any, at the end of the night.\nIf there are no Werewolves at the end of the night, you become a Werewolf.{}".format(passstring))
        if role == "Apprentice Tanner":
            await player.send("You are an Apprentice Tanner.\nYou win with the Tanner, if they are killed.\nHowever, you yourself are not a Tanner so if only you are killed you still lose.\nYou will be informed of the Tanner (and Doppel-Tanner), if any, at the end of the night.\nIf both the Tanner and Doppel-Tanner are in play, you win if either dies.\nIf there are no Tanners at the end of the night, you become a Tanner.{}".format(passstring))
        if role == "Mason":
            await player.send("You are a Mason.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou will be informed of your fellow Masons at the end of the night.{}".format(passstring))
        if role == "Seer":
            await player.send("You are a Seer.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou may look at another player's card, or two centre cards.\nThe numbering of players is as follows:")
            await player.send(playerstr)
            await player.send("To see someone else's card, type the number of that player. To see two centre cards, type their numbers i.e. \"1 2\", \"1 3\", or \"2 3\". Type \"pass\" to do nothing.")
        if role == "Apprentice Seer":
            await player.send("You are an Apprentice Seer.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou may look at one centre card.\nType \"1\", \"2\", or \"3\" to choose a centre card to look at, or \"pass\" to do nothing.")
        if role == "Robber":
            await player.send("You are a Robber.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou may take another player's card and look at it.\nThe numbering of players is as follows:")
            await player.send(playerstr)
            await player.send("To rob someone else's card, type the number of that player. Type \"pass\" to do nothing.")
        if role == "Troublemaker":
            await player.send("You are a Troublemaker.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou may exchange two other players' cards.\nThe numbering of players is as follows:")
            await player.send(playerstr)
            await player.send("To troublemake two other people's cards, type their numbers separated by a space e.g. \"1 2\". Type \"pass\" to do nothing.")
        if role == "Village Idiot":
            await player.send("You are a Village Idiot.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou may move all players' cards up by one or down by one.\nThe numbering of players is as follows:")
            await player.send(playerstr)
            await player.send("To move all cards up or down by one, type \"up\" or \"down\". Type \"pass\" to do nothing.")
        if role == "Drunk":
            await player.send("You are a Drunk.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou must now choose the centre card that you will exchange with your card.\nType \"1\", \"2\", or \"3\" to choose a centre card. (You may not pass)")
        if role == "Insomniac":
            await player.send("You are an Insomniac.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nYou will be informed of your final role at the end of the night.{}".format(passstring))
        if role == "Squire":
            await player.send("You are a Squire.\nYou win with the Werewolves, if no Werewolves or Tanners are killed.\nHowever, you yourself are not a Werewolf so if only you are killed you still win.\nYou will be informed of the Werewolves, if any, at the end of the night, and will see their final roles.\nIf there are no Werewolves at the end of the night, you become a Werewolf.{}".format(passstring))
        if role == "Villager":
            await player.send("You are a Villager.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.{}".format(passstring))
        if role == "Hunter":
            await player.send("You are a Hunter.\nYou win with the Villagers, if at least one Werewolf is killed and no Tanner is killed.\nIf you are killed at the end of the day, the person you voted for will also be killed.{}".format(passstring))
        if role == "Tanner":
            await player.send("You are a Tanner.\nYou win if and only if you are killed, in which case no one else wins.{}".format(passstring))

    for i in range(len(playerlist)):
        await roleinfo(playerlist[i],startplayerroles[i],playerstr,False)

    def dm_check(m):
        if m.channel == message.channel and m.content == "!shame":
            return True
        return dmCheck(m.channel) and m.author in playerlist

    #Gets each person's night action
    while False in acted:
        reply = await client.wait_for("message", check=dm_check)

        if reply.channel == message.channel:
            shamestring = "The players whose night actions have not been received are:\n"
            for i in range(len(playerlist)):
                if not acted[i]:
                    shamestring = shamestring + "{}\n".format(playerlist[i].display_name)
            await message.channel.send(shamestring)
            continue

        replycommand = reply.content
        replyauthor = reply.author
        authornum = 0
        for i in range(len(playerlist)):
            if replyauthor == playerlist[i]:
                authornum = i
        authorrole = startplayerroles[authornum]
        if authorrole == "Doppelganger":
            authorrole = doppelrole

        currentaction = []
        actiondone = False
        
        if acted[authornum]:
            await replyauthor.send("You have already performed your action.")
            continue

        if replycommand == "pass":
            if authorrole not in cannotpass:
                await replyauthor.send("You have chosen to pass.")
                if startplayerroles[authornum] == "Doppelganger":
                    nightactionlist.append(doppelaction)
                acted[authornum] = True
                continue

        if authorrole == "Doppelganger":
            try:
                doppelcard = int(replycommand)-1
                assert doppelcard >= 0 and doppelcard < len(playerlist)
                if doppelcard == authornum:
                    await replyauthor.send("You cannot choose your own card.")
                    continue
                else:
                    await replyauthor.send("You have chosen to copy {}'s card.".format(playerlist[doppelcard].display_name))
                    doppelaction = ["doppel",authornum,doppelcard]
                    doppelrole = startplayerroles[doppelcard]
                    await roleinfo(replyauthor,doppelrole,playerstr,True)
                    if doppelrole in doppelpass:
                        nightactionlist.append(doppelaction)
                        acted[authornum] = True
                    continue
            except:
                pass

        elif authorrole == "Werewolf":
            try:
                replynum = int(replycommand)
                assert replynum > 0 and replynum <= centrecards
                await replyauthor.send("You have chosen to look at centre card {} if there are no other Werewolves.".format(replynum))
                currentaction = ["werewolfsee",authornum,replynum]
                actiondone = True
            except:
                pass

        elif authorrole == "Seer":
            try:
                replylist = replycommand.split()
                if len(replylist) == 2:
                    firstcard = int(replylist[0])
                    secondcard = int(replylist[1])
                    assert firstcard > 0 and firstcard <= centrecards
                    assert secondcard > 0 and secondcard <= centrecards
                    assert firstcard != secondcard
                    await replyauthor.send("You have chosen to look at centre cards {} and {}.".format(firstcard,secondcard))
                    currentaction = ["seecentre",authornum,firstcard,secondcard]
                    actiondone = True
                else:
                    assert len(replylist) == 1
                    seecard = int(replylist[0])-1
                    assert seecard >= 0 and seecard < len(playerlist)
                    if seecard == authornum:
                        await replyauthor.send("You cannot choose your own card.")
                        continue
                    else:
                        await replyauthor.send("You have chosen to look at {}'s card.".format(playerlist[seecard].display_name))
                        currentaction = ["see",authornum,seecard]
                        actiondone = True
            except:
                pass

        elif authorrole == "Apprentice Seer":
            try:
                replynum = int(replycommand)
                assert replynum > 0 and replynum <= centrecards
                await replyauthor.send("You have chosen to look at centre card {}.".format(replynum))
                currentaction = ["appsee",authornum,replynum]
                actiondone = True
            except:
                pass

        elif authorrole == "Robber":
            try:
                robcard = int(replycommand)-1
                assert robcard >= 0 and robcard < len(playerlist)
                if robcard == authornum:
                    await replyauthor.send("You cannot choose your own card.")
                    continue
                else:
                    await replyauthor.send("You have chosen to rob {}'s card.".format(playerlist[robcard].display_name))
                    currentaction = ["rob",authornum,robcard]
                    actiondone = True
            except:
                pass

        elif authorrole == "Troublemaker":
            try:
                replylist = replycommand.split()
                assert len(replylist) == 2
                firstplayer = int(replylist[0])-1
                secondplayer = int(replylist[1])-1
                assert firstplayer >= 0 and firstplayer < len(playerlist)
                assert secondplayer >= 0 and secondplayer < len(playerlist)
                assert firstplayer != secondplayer
                if firstplayer == authornum or secondplayer == authornum:
                    await replyauthor.send("You cannot choose your own card.")
                    continue
                else:
                    await replyauthor.send("You have chosen to troublemake {}'s and {}'s cards.".format(playerlist[firstplayer].display_name,playerlist[secondplayer].display_name))
                    currentaction = ["troublemake",authornum,firstplayer,secondplayer]
                    actiondone = True
            except:
                pass

        elif authorrole == "Village Idiot":
            if replycommand == "up":
                currentaction = ["idiot",authornum,"up"]
                actiondone = True
            elif replycommand == "down":
                currentaction = ["idiot",authornum,"down"]
                actiondone = True
            if actiondone:
                await replyauthor.send("You chose to move all cards {}.".format(replycommand))

        elif authorrole == "Drunk":
            try:
                replynum = int(replycommand)
                assert replynum > 0 and replynum <= centrecards
                await replyauthor.send("You have chosen to drink centre card {}.".format(replynum))
                currentaction = ["drink",authornum,replynum]
                actiondone = True
            except:
                pass

        if actiondone:
            if startplayerroles[authornum] == "Doppelganger":
                doppelaction.append(currentaction)
                nightactionlist.append(doppelaction)
            else:
                nightactionlist.append(currentaction)
            acted[authornum] = True
            continue

        await replyauthor.send("Invalid command.")

    return nightactionlist,doppelrole

#Resolve night actions (or track night actions)
async def resolvenight(client,message,playerlist,startplayerroles,startcentreroles,nightactionlist,doppelrole):
    playerroles = startplayerroles.copy()
    centreroles = startcentreroles.copy()
    actionlist = copy.deepcopy(nightactionlist)

    nightactionstr = "_ _\nNight actions:\n"

    async def see(command,playerlist,playerroles,centreroles,nightactionstr):
        if command[0] == "appsee":
            await playerlist[command[1]].send("Centre card {} is the {}.".format(command[2],centreroles[command[2]-1]))
            nightactionstr = nightactionstr + "{} saw centre card {}, which was the {}.\n".format(playerlist[command[1]].display_name,command[2],centreroles[command[2]-1])
        elif command[0] == "seecentre":
            await playerlist[command[1]].send("Centre card {} is the {}.".format(command[2],centreroles[command[2]-1]))
            await playerlist[command[1]].send("Centre card {} is the {}.".format(command[3],centreroles[command[3]-1]))
            nightactionstr = nightactionstr + "{} saw centre cards {} and {}, which were {} and {}, respectively.\n".format(playerlist[command[1]].display_name,command[2],command[3],centreroles[command[2]-1],centreroles[command[3]-1])
        else:
            await playerlist[command[1]].send("{}'s card is the {}.".format(playerlist[command[2]].display_name,playerroles[command[2]]))
            nightactionstr = nightactionstr + "{} saw {}'s card, which was the {}.\n".format(playerlist[command[1]].display_name,playerlist[command[2]].display_name,playerroles[command[2]])
        return nightactionstr

    async def rob(command,playerlist,playerroles,nightactionstr):
        temprole = playerroles[command[2]]
        await playerlist[command[1]].send("You robbed {}'s card, which is the {}.".format(playerlist[command[2]].display_name,temprole))
        nightactionstr = nightactionstr + "{} robbed {}'s {}.\n".format(playerlist[command[1]].display_name,playerlist[command[2]].display_name,temprole)
        playerroles[command[2]] = playerroles[command[1]]
        playerroles[command[1]] = temprole
        return playerroles,nightactionstr

    def troublemake(command,playerlist,playerroles,nightactionstr):
        temprole = playerroles[command[2]]
        playerroles[command[2]] = playerroles[command[3]]
        playerroles[command[3]] = temprole
        nightactionstr = nightactionstr + "{} troublemade {} and {}.\n".format(playerlist[command[1]].display_name,playerlist[command[2]].display_name,playerlist[command[3]].display_name)
        return playerroles,nightactionstr

    def idiot(command,playerlist,playerroles,nightactionstr):
        if command[2] == "up":
            temprole = playerroles[0]
            for i in range(len(playerlist)-1):
                playerroles[i] = playerroles[i+1]
            playerroles[-1] = temprole
        else:
            temprole = playerroles[-1]
            for i in range(len(playerlist)-1):
                playerroles[-1-i] = playerroles[-2-i]
            playerroles[0] = temprole
        nightactionstr = nightactionstr + "{} moved all roles {}!\n".format(playerlist[command[1]].display_name,command[2])
        return playerroles,nightactionstr

    def drink(command,playerlist,playerroles,centreroles,nightactionstr):
        temprole = playerroles[command[1]]
        playerroles[command[1]] = centreroles[command[2]-1]
        centreroles[command[2]-1] = temprole
        nightactionstr = nightactionstr + "{} drunk centre card {}.\n".format(playerlist[command[1]].display_name,command[2])
        return playerroles,centreroles,nightactionstr

    #Doppelganger
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] == "doppel":
            nightactionstr = nightactionstr + "{} doppelganged {} and became a {}.\n".format(playerlist[command[1]].display_name,playerlist[command[2]].display_name,doppelrole)
            if len(command) == 4:
                doppelcommand = command[3]
                if doppelcommand[0] in ["seecentre","see","appsee"]:
                    nightactionstr = await see(doppelcommand,playerlist,playerroles,centreroles,nightactionstr)
                if doppelcommand[0] == "rob":
                    playerroles,nightactionstr = await rob(doppelcommand,playerlist,playerroles,nightactionstr)
                if doppelcommand[0] == "troublemake":
                    playerroles,nightactionstr = troublemake(doppelcommand,playerlist,playerroles,nightactionstr)
                if doppelcommand[0] == "idiot":
                    playerroles,nightactionstr = idiot(doppelcommand,playerlist,playerroles,nightactionstr)
                if doppelcommand[0] == "drink":
                    playerroles,centreroles,nightactionstr = drink(doppelcommand,playerlist,playerroles,centreroles,nightactionstr)
            actionlist.pop(i)
            break

    #Werewolves, Minion
    curwerewolves = []
    werewolfstr = ""
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Werewolf" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Werewolf"):
            curwerewolves.append(i)
            werewolfstr = werewolfstr + playerlist[i].display_name + ", "
    werewolfstr = werewolfstr.rstrip(", ")
    if len(curwerewolves) != 1:
        actionremove = []
        werewolfwant = ""
        for i in range(len(actionlist)):
            if actionlist[i][0] == "werewolfsee":
                werewolfwant = werewolfwant + "{} wanted to see centre card {}.\n".format(playerlist[actionlist[i][1]].display_name,actionlist[i][2])
                actionremove.append(i)
        newactionlist = []
        for i in range(len(actionlist)):
            if i not in actionremove:
                newactionlist.append(actionlist[i])
        actionlist = newactionlist
        for i in curwerewolves:
            await playerlist[i].send("The werewolves are:\n{}".format(werewolfstr))
        if len(curwerewolves) == 0:
            nightactionstr = nightactionstr + "No werewolves woke up.\n"
        else:
            nightactionstr = nightactionstr + "Werewolves {} woke up.\n".format(werewolfstr)
            nightactionstr = nightactionstr + werewolfwant
    else:
        lonewerewolf = curwerewolves[0]
        werewolfseen = False
        cardchoice = 0
        cardrole = ""
        for i in range(len(actionlist)):
            if actionlist[i][0] == "werewolfsee":
                werewolfseen = True
                cardchoice = actionlist[i][2]
                cardrole = centreroles[cardchoice-1]
                actionlist.pop(i)
                break
        await playerlist[lonewerewolf].send("You are a lone werewolf.")
        nightactionstr = nightactionstr + "Werewolf {} woke up.\n".format(playerlist[lonewerewolf].display_name)
        if werewolfseen:
            await playerlist[lonewerewolf].send("You chose to look at centre card {}, which is a {}.".format(cardchoice,cardrole))
            nightactionstr = nightactionstr + "{} saw centre card {}, which was a {}.\n".format(playerlist[lonewerewolf].display_name,cardchoice,cardrole)
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Minion" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Minion"):
            if len(curwerewolves) == 0:
                await playerlist[i].send("There are no werewolves.")
                nightactionstr = nightactionstr + "Minion {} woke up but saw no werewolves.\n".format(playerlist[i].display_name)
            else:
                await playerlist[i].send("The werewolves are:\n{}".format(werewolfstr))
                nightactionstr = nightactionstr + "Minion {} woke up and saw the werewolves.\n".format(playerlist[i].display_name)

    #Apprentice Tanner
    curtanners = []
    tannerstr = ""
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Tanner" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Tanner"):
            curtanners.append(i)
            tannerstr = tannerstr + playerlist[i].display_name + ", "
    tannerstr = tannerstr.rstrip(", ")
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Apprentice Tanner" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Apprentice Tanner"):
            if len(curtanners) == 0:
                await playerlist[i].send("There are no tanners.")
                nightactionstr = nightactionstr + "Apprentice Tanner {} woke up but saw no tanners.\n".format(playerlist[i].display_name)
            else:
                await playerlist[i].send("The tanners are:\n{}".format(tannerstr))
                nightactionstr = nightactionstr + "Apprentice Tanner {} woke up and saw the tanners.\n".format(playerlist[i].display_name)

    #Masons
    curmasons = []
    masonstr = ""
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Mason" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Mason"):
            curmasons.append(i)
            masonstr = masonstr + playerlist[i].display_name + ", "
    masonstr = masonstr.rstrip(", ")
    for i in curmasons:
        await playerlist[i].send("The masons are:\n{}".format(masonstr))
    if len(curmasons) > 1:
        nightactionstr = nightactionstr + "Masons {} woke up and saw each other.\n".format(masonstr)
    elif len(curmasons) == 1:
        nightactionstr = nightactionstr + "Mason {} woke up alone.\n".format(masonstr)

    #Seer, Apprentice Seer
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] in ["seecentre","see","appsee"]:
            nightactionstr = await see(command,playerlist,playerroles,centreroles,nightactionstr)
            actionlist.pop(i)
            break

    #Robber
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] == "rob":
            playerroles,nightactionstr = await rob(command,playerlist,playerroles,nightactionstr)
            actionlist.pop(i)
            break

    #Troublemaker
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] == "troublemake":
            playerroles,nightactionstr = troublemake(command,playerlist,playerroles,nightactionstr)
            actionlist.pop(i)
            break

    #Village idiot
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] == "idiot":
            playerroles,nightactionstr = idiot(command,playerlist,playerroles,nightactionstr)
            actionlist.pop(i)
            break

    #Drunk
    for i in range(len(actionlist)):
        command = actionlist[i]
        if command[0] == "drink":
            playerroles,centreroles,nightactionstr = drink(command,playerlist,playerroles,centreroles,nightactionstr)
            actionlist.pop(i)
            break

    #Insomniac
    for i in range(len(playerlist)):
        if startplayerroles[i] == "Insomniac" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Insomniac"):
            await playerlist[i].send("You are now the {}.".format(playerroles[i]))
            nightactionstr = nightactionstr + "{} saw that they were now the {}.\n".format(playerlist[i].display_name,playerroles[i])

    #Squire
    for i in range(len(playerroles)):
        if startplayerroles[i] == "Squire" or (startplayerroles[i] == "Doppelganger" and doppelrole == "Squire"):
            if len(curwerewolves) == 0:
                await playerlist[i].send("There are no werewolves.")
                nightactionstr = nightactionstr + "Squire {} woke up but saw no werewolves.\n".format(playerlist[i].display_name)
            else:
                nightactionstr = nightactionstr + "Squire {} woke up and saw the werewolves.\n".format(playerlist[i].display_name)
                for j in curwerewolves:
                    await playerlist[i].send("{} was a Werewolf and is now a {}.".format(playerlist[j].display_name,playerroles[j]))
                    nightactionstr = nightactionstr + "{} saw that {} was now the {}.\n".format(playerlist[i].display_name,playerlist[j].display_name,playerroles[j])
    
    return playerroles,centreroles,nightactionstr

#Day phase (just a timer, with dayskip)
async def day(client,message,playerlist,roleslist):
    minutesleft = daytimer
    secondsleft = 0
    stillinday = True
    await message.channel.send("```Day Phase Triggered```")
    daymessage = await message.channel.send("You have {} minutes and {} seconds left until the day ends.".format(minutesleft,secondsleft))
    await message.channel.send("If everyone types !dayskip, the day will end automatically.")

    roleorderstr = "Order of roles:\n"
    for i in range(len(roleorder)):
        if roleorder[i] in roleslist:
            roleorderstr = roleorderstr + roleorder[i] + ", "
    roleorderstr = roleorderstr.rstrip(", ")
    await message.channel.send(roleorderstr)

    async def daycountdown(daymessage):
        minutesleft = daytimer
        secondsleft = 0
        stillinday = True
        while stillinday:
            await daymessage.edit(content="You have {} minutes and {} seconds left until the day ends.".format(minutesleft,secondsleft))
            if secondsleft == 0:
                if minutesleft == 0:
                    stillinday = False
                    break
                else:
                    secondsleft = 50
                    minutesleft -= 1
            else:
                secondsleft -= 10
            await asyncio.sleep(10)

    async def dayskip(playerlist):
        def dayskip_check(m):
            return m.channel == message.channel and m.author in playerlist and m.content == "!dayskip"
        
        hasdayskip = [False] * len(playerlist)
        while False in hasdayskip:
            reply = await client.wait_for("message", check=dayskip_check)
            authornum = 0
            for i in range(len(playerlist)):
                if reply.author == playerlist[i]:
                    authornum = i
            if not hasdayskip[authornum]:
                await message.channel.send("{} has requested a dayskip!".format(playerlist[authornum].display_name))
                hasdayskip[authornum] = True
    
    tasks = [asyncio.create_task(daycountdown(daymessage)),asyncio.create_task(dayskip(playerlist))]
    await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
    for task in tasks:
        if not task.done():
            task.cancel()

#Vote phase and results
async def vote(client,message,playerlist,startplayerroles,startcentreroles,nightactionlist,doppelrole,finalplayerroles,finalcentreroles,nightactionstr):
    await message.channel.send("```Vote Phase Triggered```")

    hasvoted = [False] * len(playerlist)
    votetarget = [0] * len(playerlist)
    
    playerstr = playerstring(playerlist)
    for i in range(len(playerlist)):
        await playerlist[i].send("Time is up! You must vote.\nThe numbering of players is as follows:")
        await playerlist[i].send(playerstr)
        await playerlist[i].send("To vote for someone, type the number of that player.")

    def dm_check(m):
        return dmCheck(m.channel) and m.author in playerlist

    #Gets each person's vote
    while False in hasvoted:
        reply = await client.wait_for("message", check=dm_check)
        replycontent = reply.content
        authornum = 0
        for i in range(len(playerlist)):
            if reply.author == playerlist[i]:
                authornum = i
        replyauthor = playerlist[authornum]
        try:
            target = int(replycontent)-1
            assert target >= 0 and target < len(playerlist)
            if target == authornum:
                await replyauthor.send("You cannot vote for yourself.")
                continue
            else:
                await replyauthor.send("You have chosen to vote for {}.".format(playerlist[target].display_name))
                if not hasvoted[authornum]:
                    await message.channel.send("{} has voted!".format(replyauthor.display_name))
                    hasvoted[authornum] = True
                votetarget[authornum] = target
        except:
            await replyauthor.send("Invalid command.")

    #Displays votes and determines who dies
    playervotestr = ""
    numvotes = [0] * len(playerlist)
    for i in range(len(playerlist)):
        playervotestr = playervotestr + "{} voted for {}!\n".format(playerlist[i].display_name,playerlist[votetarget[i]].display_name)
        numvotes[votetarget[i]] += 1
    await message.channel.send(playervotestr)

    maxvotes = 2            #Players with the most votes only die if they have at least 2 votes
    deathlist = []

    for i in range(len(playerlist)):
        if numvotes[i] == maxvotes:
            deathlist.append(i)
        if numvotes[i] > maxvotes:
            maxvotes = numvotes[i]
            deathlist = [i]

    deathstr = ""
    for i in range(len(deathlist)):
        playername = playerlist[deathlist[i]].display_name
        playerrole = finalplayerroles[deathlist[i]]
        if playerrole == "Doppelganger" and doppelrole != "Doppelganger":
            playerrole = "Doppel-" + doppelrole
        deathstr = deathstr + "{} died and was a {}!\n".format(playername,playerrole)

    #If a Hunter dies, check to make sure their victim also dies
    hunting = True
    while hunting:
        hunting = False
        huntingvictim = 0
        for i in range(len(deathlist)):
            playernum = deathlist[i]
            if finalplayerroles[playernum] == "Hunter" or (finalplayerroles[playernum] == "Doppelganger" and doppelrole == "Hunter"):
                huntingvictim = votetarget[playernum]
                if huntingvictim not in deathlist:
                    hunting = True
                    huntername = playerlist[playernum].display_name
                    huntedname = playerlist[huntingvictim].display_name
                    huntedrole = finalplayerroles[huntingvictim]
                    if huntedrole == "Doppelganger" and doppelrole != "Doppelganger":
                        huntedrole = "Doppel-" + doppelrole
                    deathstr = deathstr + "{} hunted {}!\n".format(huntername,huntedname)
                    deathstr = deathstr + "{} died and was a {}!\n".format(huntedname,huntedrole)
                    deathlist.append(huntingvictim)
                    break

    if deathstr == "":
        deathstr = "No one died!"
    await message.channel.send(deathstr)

    #Display final roles and determine who wins
    werewolves = []
    werewolfteam = []
    tanners = []
    apptanners = []

    finalrolestr = "_ _\nFinal roles:\n"   
    playeractualroles = []      #Counting Doppelganger as whatever it doppeled into
    for i in range(len(playerlist)):
        playername = playerlist[i].display_name
        if finalplayerroles[i] == "Doppelganger":
            playeractualroles.append(doppelrole)
            if doppelrole == "Doppelganger":
                playerrole = "Doppelganger"
            else:
                playerrole = "Doppel-" + doppelrole
        else:
            playeractualroles.append(finalplayerroles[i])
            playerrole = finalplayerroles[i]
        finalrolestr = finalrolestr + "{}: {}\n".format(playername,playerrole)

    for i in range(centrecards):
        if finalcentreroles[i] == "Doppelganger" and doppelrole != "Doppelganger":
            centrerole = "Doppel-" + doppelrole
        else:
            centrerole = finalcentreroles[i]
        finalrolestr = finalrolestr + "Centre card {}: {}\n".format(i+1,centrerole)

    await message.channel.send(finalrolestr)

    for i in range(len(playerlist)):
        if playeractualroles[i] == "Werewolf":
            werewolves.append(i)
            werewolfteam.append(i)
        if playeractualroles[i] in ["Minion","Squire"]:
            werewolfteam.append(i)
        if playeractualroles[i] == "Tanner":
            tanners.append(i)
    if len(werewolves) == 0:
        for i in range(len(playerlist)):
            if playeractualroles[i] in ["Minion","Squire"]:
                werewolves.append(i)
    if len(tanners) == 0:
        for i in range(len(playerlist)):
            if playeractualroles[i] == "Apprentice Tanner":
                tanners.append(i)
    else:
        for i in range(len(playerlist)):
            if playeractualroles[i] == "Apprentice Tanner":
                apptanners.append(i)        

    winners = []
    tannerwin = False
    everyoneloss = False
    werewolfwin = True
    for i in range(len(tanners)):
        if tanners[i] in deathlist:
            tannerwin = True
            winners.append(tanners[i])
    if tannerwin:
        winners.extend(apptanners)
    else:
        if len(werewolves) == 0:
            if len(deathlist) != 0:
                everyoneloss = True
            else:
                werewolfwin = False
        if not everyoneloss:
            for i in range(len(werewolves)):
                if werewolves[i] in deathlist:
                    werewolfwin = False
            if werewolfwin:
                winners.extend(werewolfteam)
            else:
                for i in range(len(playerlist)):
                    if i not in werewolfteam and i not in tanners:
                        winners.append(i)

    #Display winners
    if tannerwin:
        await message.channel.send("Tanner win!")
    elif everyoneloss:
        await message.channel.send("Everyone loses!")
    elif werewolfwin:
        await message.channel.send("Werewolf team win!")
    else:
        await message.channel.send("Villager team win!")
    if not everyoneloss:
        winnerstr = ""
        for i in range(len(winners)):
            winnername = playerlist[winners[i]].display_name
            winnerstr = winnerstr + winnername + ", "
        winnerstr = winnerstr.rstrip(", ")
        await message.channel.send("Congratulations to {} for winning!".format(winnerstr))

    #Display starting roles
    startrolestr = "_ _\nStarting roles:\n"
    for i in range(len(playerlist)):
        playername = playerlist[i].display_name
        playerrole = startplayerroles[i]
        startrolestr = startrolestr + "{} started as the {}.\n".format(playername,playerrole)
    for i in range(centrecards):
        centrerole = startcentreroles[i]
        startrolestr = startrolestr + "Centre card {} started as the {}\n".format(i+1,centrerole)
    await message.channel.send(startrolestr)

    #Display actions
    await message.channel.send(nightactionstr)

client.run('TOKEN')

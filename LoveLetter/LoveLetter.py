import discord
import random
from helpcommands import *
from datetime import datetime
from random import shuffle, randint
from stringutils import *

client = discord.Client()
busyChannels = []
game = discord.Game(name="Love Letter")

cardnames = ["Spy:detective:","Guard:woman_police_officer:","Priest:cross:","Baron:cowboy:","Handmaid:mermaid:","Prince:prince:","Chancellor:levitate:","King:crown:","Countess:woman_vampire:","Princess:princess:"]

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Greetings {0.author.mention}'.format(message)
        await message.channel.send(msg)

    if message.content.startswith('!loveletter'):
        if message.channel in busyChannels:
            await message.channel.send("Channel busy with another activity.")
        else:
            busyChannels.append(message.channel)
            gamemode = ""
            messagelist = message.content.split()
            if len(messagelist) > 1:
                if messagelist[1] == "extended":
                    gamemode = "extended"
            await message.channel.send("Starting **Love Letter** in `#"+message.channel.name+"`...")
            await loveletter(client,message,gamemode)
            busyChannels.remove(message.channel)

    if message.content.startswith('!help'):
        await helpcommand(client, message)

    if message.content.startswith('!rules'):
        await rules(client, message)
        
@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + str(client.user.id))
    await client.change_presence(activity = game)

async def loveletter(client,message,gamemode):  #Main loop
    #Declarations
    maxplayers = 6                      #Maximum number of players
    gamestate = 0                       #State of game
    playerlist = []                     #List of players in the game
    deck = []                           #Deck of cards
    favours = []                        #Number of favour tokens each player has
    cards = []                          #Cards held by each player
    revealedcards = []                  #Cards revealed by each player
    playerin = []                       #Whether each player is still in the game
    playerprotected = []                #Whether each player has Handmaid protection
    tokenstowin = 0                     #Number of tokens to win
    firstplayer = 0                     #First player
    curplayer = 0                       #Current player
    burnt = 0                           #Burnt card

    if gamestate == 0:
        maxplayers,gamestate,playerlist,favours,tokenstowin,firstplayer = await login(client,message,gamemode)
    while gamestate == 2 or gamestate == 3  or gamestate == 4:
        if gamestate == 2:
            deck,cards,revealedcards,playerin,playerprotected,curplayer,burnt = await loadround(client,message,gamemode,playerlist,firstplayer)
            gamestate = 3
        if gamestate == 3:
            playersin = 0
            for i in range(len(playerlist)):
                playersin += playerin[i]
            if playersin > 1 and len(deck) > 0:
                gamestate,deck,cards,revealedcards,playerin,playerprotected,curplayer = await taketurn(client,message,gamestate,playerlist,deck,cards,revealedcards,playerin,playerprotected,curplayer,burnt)
            else:
                gamestate = 4
        if gamestate == 4:
            favours,firstplayer = await roundend(client,message,playerlist,favours,cards,revealedcards,playerin)
            gameended = False
            for i in range(len(playerlist)):
                if favours[i] >= tokenstowin:
                    gameended = True
            if gameended:
                await gameend(client,message,playerlist,favours,tokenstowin)
                gamestate = 0
            else:
                gamestate = 2
    await message.channel.send("```Game Ended```\nStart a new game with `!loveletter` or type `!help` for instructions on how to play.")

async def login(client,message,gamemode):
    #Login phase
    if gamemode == "extended":
        maxplayers = 9
    else:
        maxplayers = 6


    gamestate = 1
    playerlist = []
    favours = []
    tokenstowin = 0
    firstplayer = 0
    await message.channel.send("```Login Phase Triggered```\nThe game of Love Letter is about to begin.\n*Type !join to enter the game. (2-{} players only)*\n".format(maxplayers))
    while gamestate == 1:
        def channel_check(m):
            return m.channel == message.channel
        reply = await client.wait_for('message', check=channel_check)
        if reply.content == "!join" and len(playerlist) <= maxplayers:
            if reply.author not in playerlist:
                await message.channel.send("Greetings, {}. You have successfully entered the game.".format(reply.author.mention))
                playerlist.append(reply.author)
                if len(playerlist) == 2:
                    await message.channel.send("Two names are on the list. You may start the game with `!start` or allow more players to `!join`.".format(reply.author.mention))
            else:
                await message.channel.send("Rest assured {}, you already have a reserved place in the game.".format(reply.author.mention))
        if reply.content == "!join" and len(playerlist) > maxplayers:
            await message.channel.send(gameFullStr)
        if reply.content == "!quit":
            if reply.author in playerlist:
                await message.channel.send("{} has quit the game.".format(reply.author.mention))
                playerlist.remove(reply.author)
            else:
                await message.channel.send("Rest assured {}, you are not taking part in the game.".format(reply.author.mention))
        if reply.content == "!stop" and reply.author in playerlist:
            gamestate = 0
        if reply.content == "!start" and len(playerlist) < 2:
            await message.channel.send("We cannot begin with less than two players.")
        if reply.content == "!start" and len(playerlist) >= 2:
            random.seed(datetime.now())
            favours,tokenstowin,firstplayer = await loadgame(client,message,playerlist)
            gamestate = 2
    return maxplayers,gamestate,playerlist,favours,tokenstowin,firstplayer

async def loadgame(client,message,playerlist):
    favours = []
    playerstring = ""
    for i in range(len(playerlist)):
        favours.append(0)
        player = playerlist[i]
        playerstring += player.display_name
        if i < len(playerlist)-1:
            playerstring += ", "
    tokensarray = [7,5,4,3,3,3,3,3]
    tokenstowin = tokensarray[len(playerlist)-2]
    firstplayer = randint(0,len(playerlist)-1)
    await message.channel.send("This game of Love Letter has begun! The players are {}.".format(playerstring))
    return favours,tokenstowin,firstplayer

async def loadround(client,message,gamemode,playerlist,firstplayer):
    if gamemode == "extended":
        deck = [0,0,0,1,1,1,1,1,1,1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,6,6,6,7,7,8,8,9]
    else:
        deck = [0,0,1,1,1,1,1,1,2,2,3,3,4,4,5,5,6,6,7,8,9]
    shuffle(deck)
    cards = []
    revealedcards = []
    playerin = []
    playerprotected = []
    for i in range(len(playerlist)):
        cards.append(deck.pop(0))
        revealedcards.append([])
        playerin.append(1)
        playerprotected.append(0)
        await playerlist[i].send("You start with the {}.".format(cardnames[cards[i]]))
    curplayer = firstplayer
    burnt = deck.pop(0)
    messagestring = "A new round has begun. \n\nThe cards have been sent out." + "\n" + "{} will begin this round.".format(playerlist[firstplayer].display_name)
    await message.channel.send(messagestring)
    return deck,cards,revealedcards,playerin,playerprotected,curplayer,burnt

async def taketurn(client,message,gamestate,playerlist,deck,cards,revealedcards,playerin,playerprotected,curplayer,burnt):
    def player_check(m):
        if m.channel == message.channel and m.author == playerlist[curplayer]:
            return True
        return False
    def can_play(commandnum,drawncard):
        playnum = 0
        if commandnum == cards[curplayer]:
            playnum = 1
        if commandnum == drawncard:
            playnum = 2
        if commandnum == 5 or commandnum == 7:
            if cards[curplayer] == 8 or drawncard == 8:
                playnum = 0
        return playnum
    def check_mention(mention):
        mentionnum = -1
        for i in range(len(playerlist)):
            if removeExclamation(mention) == mentionlist[i]:
                mentionnum = i
        return mentionnum
    messagestring = "Cards played:"
    for i in range(len(playerlist)):
        strike = ""
        if playerin[i] == 0:
            strike = "~~"
        revealedstr = ""
        for j in range(len(revealedcards[i])):
            revealedstr += cardnames[revealedcards[i][j]]
            if j < len(revealedcards[i])-1:
                revealedstr += ", "
        if revealedstr == "":
            revealedstr = "None"
        messagestring += "\n" + "{}{}: {}{}".format(strike,playerlist[i].display_name,revealedstr,strike)
    messagestring += "\n" + "It is {}'s turn.".format(playerlist[curplayer].display_name)
    drawncard = deck.pop(0)
    await playerlist[curplayer].send("You drew the {}.".format(cardnames[drawncard]))
    await playerlist[curplayer].send("You currently have the {} and the {}.".format(cardnames[cards[curplayer]],cardnames[drawncard]))
    playerprotected[curplayer] = 0
    mustwaste = True
    for i in range(len(playerlist)):
        if playerprotected[i] == 1:
            messagestring += "\n" + "{} is currently being protected by the Handmaid.".format(playerlist[i].display_name)
        if i != curplayer and playerprotected[i] == 0 and playerin[i] == 1:
                mustwaste = False
    messagestring += "\n" + "There are {} cards remaining in the deck.".format(len(deck))
    if mustwaste:
        messagestring += "\n" + "As all other players are protected, typing !guard, !priest, !baron, or !king will waste the corresponding card."
    await message.channel.send(messagestring)
    waiting = True
    while waiting:
        command = await client.wait_for('message', check=player_check)
        if not command.content.startswith("!"):
            continue
        if command.content == "!stop":
            waiting = False
            gamestate = 0
            continue
        commandlist = command.content.split()
        if len(commandlist) == 0:
            await message.channel.send("Invalid command. (Type ! followed by the name of the card you want to play in lowercase).")
            continue
        cardcommands = ["!spy","!guard","!priest","!baron","!handmaid","!prince","!chancellor","!king","!countess","!princess"]
        commandnum = 10
        for i in range(10):
            if commandlist[0] == cardcommands[i]:
                commandnum = i
        mentionlist = []
        for i in playerlist:
            mentionlist.append(removeExclamation(i.mention))
        if commandnum == 10:
            await message.channel.send("Invalid command. (Type ! followed by the name of the card you want to play in lowercase).")
            continue
        playnum = can_play(commandnum,drawncard)
        if playnum == 0:
            await message.channel.send("You cannot play this card.")
            continue
        if commandnum == 0:
            waiting = False
            revealedcards[curplayer].append(0)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Spy.".format(playerlist[curplayer].display_name))
        if commandnum == 1:
            if mustwaste:
                waiting = False
                revealedcards[curplayer].append(1)
                if playnum == 1:
                    cards[curplayer] = drawncard
                await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
                await message.channel.send("{} wasted the {}.".format(playerlist[curplayer].display_name,"Guard"))
                continue
            invalidguard = False
            if len(commandlist) < 3:
                invalidguard = True
            else:
                try: 
                    targetnum = int(commandlist[2])
                    if targetnum < 0 or targetnum > 9:
                        invalidguard = True
                except ValueError:
                    invalidguard = True
            if invalidguard:
                await message.channel.send("Invalid command. (To play the Guard, type !guard followed by the player you wish to target and then the value of the card you are guessing, e.g. !guard @example 2).")
                continue
            mentionnum = check_mention(commandlist[1])
            if mentionnum == -1:
                await message.channel.send("{} is not in the game.".format(commandlist[1]))
                continue
            if mentionnum == curplayer:
                await message.channel.send("You cannot target yourself with this action.")
                continue
            if playerin[mentionnum] == 0:
                await message.channel.send("This player is out of the round.")
                continue
            if playerprotected[mentionnum] == 1:
                await message.channel.send("This player is currently being protected by the Handmaid.")
                continue
            if targetnum == 1:
                await message.channel.send("You cannot guess the number 1 with the Guard.")
                continue
            waiting = False
            revealedcards[curplayer].append(1)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Guard, guessing that {} has the {}.".format(playerlist[curplayer].display_name,playerlist[mentionnum].display_name,cardnames[targetnum]))
            if targetnum == cards[mentionnum]:
                playerin[mentionnum] = 0
                await message.channel.send("{} had the {} and is thus out of the game.".format(playerlist[mentionnum].display_name,cardnames[targetnum]))
                revealedcards[mentionnum].append(targetnum)
                await message.channel.send("{} has discarded the {}.".format(playerlist[mentionnum].display_name,cardnames[targetnum]))
            else:
                await message.channel.send("{} does not have the {}.".format(playerlist[mentionnum].display_name,cardnames[targetnum]))
        if commandnum == 2:
            if mustwaste:
                waiting = False
                revealedcards[curplayer].append(2)
                if playnum == 1:
                    cards[curplayer] = drawncard
                await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
                await message.channel.send("{} wasted the {}.".format(playerlist[curplayer].display_name,"Priest"))
                continue
            if len(commandlist) < 2:
                await message.channel.send("Invalid command. (To play the Priest, type !priest followed by the player you wish to target, e.g. !priest @example).")
                continue
            mentionnum = check_mention(commandlist[1])
            if mentionnum == -1:
                await message.channel.send("{} is not in the game.".format(commandlist[1]))
                continue
            if mentionnum == curplayer:
                await message.channel.send("You cannot target yourself with this action.")
                continue
            if playerin[mentionnum] == 0:
                await message.channel.send("This player is out of the round.")
                continue
            if playerprotected[mentionnum] == 1:
                await message.channel.send("This player is currently being protected by the Handmaid.")
                continue
            waiting = False
            revealedcards[curplayer].append(2)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Priest, targeting {}.".format(playerlist[curplayer].display_name,playerlist[mentionnum].display_name))
            await playerlist[curplayer].send("{} has the {}.".format(playerlist[mentionnum].display_name,cardnames[cards[mentionnum]]))
        if commandnum == 3:
            if mustwaste:
                waiting = False
                revealedcards[curplayer].append(3)
                if playnum == 1:
                    cards[curplayer] = drawncard
                await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
                await message.channel.send("{} wasted the {}.".format(playerlist[curplayer].display_name,"Baron"))
                continue
            if len(commandlist) < 2:
                await message.channel.send("Invalid command. (To play the Baron, type !baron followed by the player you wish to target, e.g. !baron @example).")
                continue
            mentionnum = check_mention(commandlist[1])
            if mentionnum == -1:
                await message.channel.send("{} is not in the game.".format(commandlist[1]))
                continue
            if mentionnum == curplayer:
                await message.channel.send("You cannot target yourself with this action.")
                continue
            if playerin[mentionnum] == 0:
                await message.channel.send("This player is out of the round.")
                continue
            if playerprotected[mentionnum] == 1:
                await message.channel.send("This player is currently being protected by the Handmaid.")
                continue
            waiting = False
            revealedcards[curplayer].append(3)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Baron, targeting {}.".format(playerlist[curplayer].display_name,playerlist[mentionnum].display_name))
            if cards[curplayer] == cards[mentionnum]:
                await message.channel.send("It's a tie!")
            else:
                if cards[curplayer] > cards[mentionnum]:
                    baronloser = mentionnum
                else:
                    baronloser = curplayer
                playerin[baronloser] = 0
                await message.channel.send("{} had the lower card and is thus out of the game.".format(playerlist[baronloser].display_name))
                revealedcards[baronloser].append(cards[baronloser])
                await message.channel.send("{} has discarded the {}.".format(playerlist[baronloser].display_name,cardnames[cards[baronloser]]))
        if commandnum == 4:
            waiting = False
            revealedcards[curplayer].append(4)
            playerprotected[curplayer] = 1
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Handmaid and is now protected until their next turn.".format(playerlist[curplayer].display_name))
        if commandnum == 5:
            if len(commandlist) < 2:
                await message.channel.send("Invalid command. (To play the Prince, type !prince followed by the player you wish to target, e.g. !prince @example).")
                continue
            mentionnum = check_mention(commandlist[1])
            if mentionnum == -1:
                await message.channel.send("{} is not in the game.".format(commandlist[1]))
                continue
            if playerin[mentionnum] == 0:
                await message.channel.send("This player is out of the round.")
                continue
            if playerprotected[mentionnum] == 1:
                await message.channel.send("This player is currently being protected by the Handmaid.")
                continue
            waiting = False
            revealedcards[curplayer].append(5)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Prince, targeting {}.".format(playerlist[curplayer].display_name,playerlist[mentionnum].display_name))
            revealedcards[mentionnum].append(cards[mentionnum])
            if cards[mentionnum] == 9:
                playerin[mentionnum] = 0
                await message.channel.send("{} has discarded the Princess and is thus out of the game.".format(playerlist[mentionnum].display_name))
            else:
                await message.channel.send("{} has discarded the {}.".format(playerlist[mentionnum].display_name,cardnames[cards[mentionnum]]))
                if len(deck) == 0:
                    newdraw = burnt
                    await message.channel.send("As there are no cards left, {} has drawn the burnt card.".format(playerlist[mentionnum].display_name))
                else:
                    newdraw = deck.pop(0)
                    await message.channel.send("{} has drawn a new card from the deck.".format(playerlist[mentionnum].display_name))
                cards[mentionnum] = newdraw
                await playerlist[mentionnum].send("You drew the {}.".format(cardnames[newdraw]))
        if commandnum == 6:
            waiting = False
            revealedcards[curplayer].append(6)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            def chancellor_check(m):
                if dmCheck(m.channel) and m.author == playerlist[curplayer]:
                    return True
                return False
            if len(deck) == 0:
                await message.channel.send("{} has played the Chancellor but there are no cards left so it was wasted.".format(playerlist[curplayer].display_name))
                continue
            elif len(deck) == 1:
                await message.channel.send("{} has played the Chancellor but can draw only one card.".format(playerlist[curplayer].display_name))
                chancellor1 = deck.pop(0)
                await playerlist[curplayer].send("You drew the {}.".format(cardnames[chancellor1]))
                await playerlist[curplayer].send("You currently have the {} and the {}.".format(cardnames[cards[curplayer]],cardnames[chancellor1]))
                await playerlist[curplayer].send("Please choose which card you want to keep by DMing the card number.")
                valid = False
                while not valid:
                    creply = await client.wait_for('message', check=chancellor_check)
                    try:
                        cnum = int(creply.content)
                    except ValueError:
                        continue
                    if cnum == cards[curplayer]:
                        chancellor3 = cnum
                        chancellor4 = chancellor1
                        valid = True
                    elif cnum == chancellor1:
                        chancellor3 = cnum
                        chancellor4 = cards[curplayer]
                        valid = True
                cards[curplayer] = chancellor3
                await playerlist[curplayer].send("You have kept the {}.".format(cardnames[cards[curplayer]]))
                deck.append(chancellor4)
            else:
                await message.channel.send("{} has played the Chancellor and has drawn two cards.".format(playerlist[curplayer].display_name))
                chancellor1 = deck.pop(0)
                chancellor2 = deck.pop(0)
                await playerlist[curplayer].send("You drew the {} and the {}.".format(cardnames[chancellor1],cardnames[chancellor2]))
                await playerlist[curplayer].send("You currently have the {}, the {}, and the {}.".format(cardnames[cards[curplayer]],cardnames[chancellor1],cardnames[chancellor2]))
                await playerlist[curplayer].send("Please choose which card you want to keep by DMing the card number.")
                valid = False
                while not valid:
                    creply = await client.wait_for('message', check=chancellor_check)
                    try:
                        cnum = int(creply.content)
                    except ValueError:
                        continue
                    if cnum == cards[curplayer]:
                        chancellor3 = cnum
                        chancellor4 = chancellor1
                        chancellor5 = chancellor2
                        valid = True
                    elif cnum == chancellor1:
                        chancellor3 = cnum
                        chancellor4 = cards[curplayer]
                        chancellor5 = chancellor2
                        valid = True
                    elif cnum == chancellor2:
                        chancellor3 = cnum
                        chancellor4 = cards[curplayer]
                        chancellor5 = chancellor1
                        valid = True
                cards[curplayer] = chancellor3
                await playerlist[curplayer].send("You have kept the {}.".format(cardnames[cards[curplayer]]))
                await playerlist[curplayer].send("Please choose which card you want to put back first by DMing the card number.")
                valid = False
                while not valid:
                    creply = await client.wait_for('message', check=chancellor_check)
                    try:
                        cnum = int(creply.content)
                    except ValueError:
                        continue
                    if cnum == chancellor4:
                        chancellor6 = cnum
                        chancellor7 = chancellor5
                        valid = True
                    elif cnum == chancellor5:
                        chancellor6 = cnum
                        chancellor7 = chancellor4
                        valid = True
                await playerlist[curplayer].send("You have returned {} first and {} second.".format(cardnames[chancellor6],cardnames[chancellor7]))
                deck.append(chancellor6)
                deck.append(chancellor7)
            await message.channel.send("{} has returned their cards.".format(playerlist[curplayer].display_name))
        if commandnum == 7:
            if mustwaste:
                waiting = False
                revealedcards[curplayer].append(7)
                if playnum == 1:
                    cards[curplayer] = drawncard
                await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
                await message.channel.send("{} wasted the {}.".format(playerlist[curplayer].display_name,"King"))
                continue
            if len(commandlist) < 2:
                await message.channel.send("Invalid command. (To play the King, type !king followed by the player you wish to target, e.g. !king @example).")
                continue
            mentionnum = check_mention(commandlist[1])
            if mentionnum == -1:
                await message.channel.send("{} is not in the game.".format(commandlist[1]))
                continue
            if mentionnum == curplayer:
                await message.channel.send("You cannot target yourself with this action.")
                continue
            if playerin[mentionnum] == 0:
                await message.channel.send("This player is out of the round.")
                continue
            if playerprotected[mentionnum] == 1:
                await message.channel.send("This player is currently being protected by the Handmaid.")
                continue
            waiting = False
            revealedcards[curplayer].append(7)
            if playnum == 1:
                cards[curplayer] = drawncard
            await message.channel.send("{} has played the King, targeting {}.".format(playerlist[curplayer].display_name,playerlist[mentionnum].display_name))
            swappedcard = cards[curplayer]
            cards[curplayer] = cards[mentionnum]
            cards[mentionnum] = swappedcard
            await playerlist[curplayer].send("After swapping hands, you received the {}.".format(cardnames[cards[curplayer]]))
            await playerlist[mentionnum].send("After swapping hands, you received the {}.".format(cardnames[cards[mentionnum]]))
        if commandnum == 8:
            waiting = False
            revealedcards[curplayer].append(8)
            if playnum == 1:
                cards[curplayer] = drawncard
            await playerlist[curplayer].send("You currently have the {}.".format(cardnames[cards[curplayer]]))
            await message.channel.send("{} has played the Countess.".format(playerlist[curplayer].display_name))
        if commandnum == 9:
            waiting = False
            revealedcards[curplayer].append(9)
            playerin[curplayer] = 0
            if playnum == 1:
                cards[curplayer] = drawncard
            await message.channel.send("{} has played the Princess and is thus out of the game.".format(playerlist[curplayer].display_name))
            revealedcards[curplayer].append(cards[curplayer])
            await message.channel.send("{} has discarded the {}.".format(playerlist[curplayer].display_name,cardnames[cards[curplayer]]))
    cantplay = True
    while cantplay:
        curplayer += 1
        if curplayer == len(playerlist):
            curplayer = 0
        if playerin[curplayer] == 1:
            cantplay = False
    return gamestate,deck,cards,revealedcards,playerin,playerprotected,curplayer

async def roundend(client,message,playerlist,favours,cards,revealedcards,playerin):
    messagestring = "The round is over and all remaining players reveal their cards."
    jointwin = False
    maxcard = -1
    winningplayer = -1
    spynum = 0
    spyplayer = -1
    for i in range(len(playerlist)):
        if playerin[i] == 1:
            messagestring += "\n" + "{} had the {}".format(playerlist[i].display_name,cardnames[cards[i]])
            if cards[i] == maxcard:
                jointwin = True
            elif cards[i] > maxcard:
                maxcard = cards[i]
                jointwin = False
                winningplayer = i
            if 0 in revealedcards[i]:
                spynum += 1
                spyplayer = i
    if jointwin == False:
        messagestring += "\n" + "{} won the round and gained one Favour Token.".format(playerlist[winningplayer].display_name)
        favours[winningplayer] += 1
        firstplayer = winningplayer
    else:
        jointwin = False
        maxtotal = -1
        jointwinners = []
        for i in range(len(playerlist)):
            if playerin[i] == 1 and cards[i] == maxcard:
                playertotal = 0
                for j in range(len(revealedcards[i])):
                    playertotal += revealedcards[i][j]
                if playertotal == maxtotal:
                    jointwin = True
                    jointwinners.append(i)
                elif playertotal > maxtotal:
                    maxtotal = playertotal
                    jointwin = False
                    winningplayer = i
                    jointwinners = [i]
        if jointwin == False:
            messagestring += "\n" + "{} won the round on a tie break and gained one Favour Token.".format(playerlist[winningplayer].display_name)
            favours[winningplayer] += 1
            firstplayer = winningplayer
        else:
            for i in range(len(jointwinners)):
                messagestring += "\n" + "{} jointly won the round and gained one Favour Token.".format(playerlist[jointwinners[i]].display_name)
                favours[jointwinners[i]] += 1
            messagestring += "\n" + "The first player for the next round will be randomly chosen from the joint winners."
            firstindex = randint(0,len(jointwinners)-1)
            firstplayer = jointwinners[firstindex]
    if spynum == 1:
        messagestring += "\n" + "{} is the only remaining player to have played the Spy and thus gains one Favour Token.".format(playerlist[spyplayer].display_name)
        favours[spyplayer] += 1
    for i in range(len(playerlist)):
        messagestring += "\n" + "{} has {} Favour Tokens.".format(playerlist[i].display_name,favours[i])
    await message.channel.send(messagestring)
    return favours,firstplayer

async def gameend(client,message,playerlist,favours,tokenstowin):
    messagestring = "A player has obtained {} Favour Tokens so the game is over.".format(tokenstowin)
    jointwin = False
    maxfavours = -1
    jointwinners = []
    for i in range(len(playerlist)):
        if favours[i] == maxfavours:
            jointwin = True
            jointwinners.append(i)
        elif favours[i] > maxfavours:
                maxfavours = favours[i]
                jointwin = False
                winningplayer = i
                jointwinners = [i]
    if jointwin == False:
        messagestring += "\n" + "{} is the winner, with {} Favour Tokens!".format(playerlist[winningplayer].display_name,maxfavours)
    else:
        for i in range(len(jointwinners)):
            messagestring += "\n" + "{} is the joint winner, with {} Favour Tokens!".format(playerlist[jointwinners[i]].display_name,maxfavours)
    await message.channel.send(messagestring)
    for i in range(len(playerlist)):
        playermention = playerlist[i].mention
        playermoney = favours[i]
        if i in jointwinners:
            playermoney = playermoney*2
        playermsg = await message.channel.send("$give {} {}".format(playermention,playermoney))
        await playermsg.delete(delay=0.5)
    await message.channel.send("Money has been given out for CasinoBot.")

client.run('TOKEN')

import discord
import os
import pickle
import PIL
from PIL import Image
import copy
import time
import SudokuMaster

client = discord.Client()
busyChannels = []
game = discord.Game(name="Sudoku")

#Size of grid
dim = 3
dimsquared = 9

teamsize = 5            #Max. size of a sudoku team

global hasStarted       #Has it started initialising everything?
hasStarted = False

global sudokuArray      #Array for the state of the sudoku
sudokuArray = []

global cursolving       #Currently solving a sudoku?
cursolving = "No"       #Can be No, Selecting, and Solving

global curchannel       #Channel where sudoku is currently being played
curchannel = ""

global sudokuTeam       #Team for solving the sudoku
sudokuTeam = []

global sudokuName       #Name of sudoku currently being solved
sudokuName = ""

global writeMode        #Mode of writing
writeMode = ""

#Graphics of digits and grid
global bigDigits,smallDigits,blueDigits,basicGrid
bigDigits,smallDigits,blueDigits,basicGrid = (None,)*4
#Pixels in graphics
global bigDigitsPixels,smallDigitsPixels,blueDigitsPixels,basicGridPixels
bigDigitsPixels,smallDigitsPixels,blueDigitsPixels,basicGridPixels = (None,)*4

#Constants to do with the display
bigSize = 19
smallSize = 5
bigGap = 3          #Actually, the big gap is bigGap+smallGap
smallGap = 3
startX = 25
startY = 9

#List of difficulties and their monetary rewards
listofdiffs = ["Easy","Medium","Hard","Diabolical","Extreme","Ultra-Extreme"]
listofmoney = [10,20,50,100,200,1000]

#How many of the difficulties can be generated
genDiffs = 4

#List of SudokuMaster difficulties at each level
masterDiffs = [[1,1],[2,2],[3,4],[5,7]]

#CasinoBot's ID (for giving money)
casinoid = 695698408186576976

#Read all data necessary to start
@client.event
async def on_ready():
    global hasStarted,sudokuArray,cursolving,curchannel,sudokuTeam,sudokuName
    #Get graphics
    await getGraphics()
    #Read cursolving
    try:
        with open("Files/CurrentlyPlaying.txt","r") as f:
            cursolving = f.read()
    except:
        print("Could not read from CurrentlyPlaying.txt")
        return
    if cursolving == "Selecting":
        cursolving = "No"
    if cursolving == "Solving":
        #Read curchannel
        try:
            with open("Files/ChannelID.txt","r") as f:
                a = f.read()
                channelid = int(a)
                curchannel = client.get_channel(channelid)
        except:
            print("Could not read from ChannelID.txt")
            return
        #Read sudokuTeam
        try:
            sudokuTeam = []
            with open("Files/TeamPlayers.txt","r") as f:
                teamlines = f.readlines()
                for i in range(len(teamlines)):
                    sudokuTeam.append(int(teamlines[i].rstrip("\n")))
        except:
            print("Could not read from TeamPlayers.txt")
            return
        #Read sudokuName
        try:
            with open("Files/SudokuName.txt","r") as f:
                sudokuName = f.read()
        except:
            print("Could not read from SudokuName.txt")
            return
        #Read sudokuArray
        try:
            with open("Files/SudokuData.txt","rb") as f:
                sudokuArray = pickle.load(f)
        except:
            print("Could not write to SudokuData.txt")
            return
        await displaySudoku()
        await displayTeam()
    print("Connected!")
    print("Username: " + client.user.name)
    print("ID: " + str(client.user.id))
    await client.change_presence(activity = game)
    hasStarted = True

@client.event
async def on_message(message):
    if not hasStarted:
        return

    global cursolving,curchannel
    if message.author == client.user:
        return

    if message.content == "!hello":
        msg = "Greetings {0.author.mention}".format(message)
        await message.channel.send(msg)

    #Help
    if message.content == "!help":
        messagestring = "Commands:\n"
        messagestring += "!sudoku - starts a game of sudoku\n"
        messagestring += "!help - gives a list of commands\n"
        messagestring += "!join - join the current sudoku-solving team\n"
        messagestring += "!quit - leave the current sudoku-solving team\n"
        messagestring += "!resign - give up on the current sudoku\n"
        messagestring += "!money - transfers all money owed to CasinoBot if it's online, and displays it if not\n"
        messagestring += "!team - displays the current team\n"
        messagestring += "!save - save current progress\n"
        messagestring += "!write - write a number to a cell e.g. \"!write a1 1\"\n"
        messagestring += "!clear - clear a cell e.g. \"!clear a1\"\n"
        messagestring += "!pencil - make pencilmarks in a cell e.g. \"!pencil a1 1 2 3\"\n"
        messagestring += "!penciladd - add pencilmarks to a cell e.g. \"!penciladd a1 1 2 3\"\n"
        messagestring += "!pencilremove - remove pencilmarks from a cell e.g. \"!pencilremove a1 1 2 3\"\n"
        messagestring += "All three pencil commands can be applied to multiple cells e.g. \"!pencil a1 a2 1 2 3\"\n"
        messagestring += "!mode write - sets mode to write so !write can be omitted\n"
        messagestring += "!mode pencil - sets mode to pencil so !pencil can be omitted\n"
        messagestring += "(In pencil mode, just type add or remove instead of !penciladd and !pencilremove)\n"
        messagestring += "!mode reset - resets mode\n"
        await message.channel.send(messagestring)

    #To start a sudoku
    if message.content == "!sudoku":
        if cursolving == "No":
            curchannel = message.channel
            try:
                with open("Files/ChannelID.txt","w") as f:
                    f.write(str(curchannel.id))
            except:
                print("Could not write to ChannelID.txt")
                return
            await message.channel.send("Starting **Sudoku** in `#"+message.channel.name+"`...")
            cursolving = "Selecting"
            await selectSudoku()
        else:
            await message.channel.send("A game of sudoku is currently in progress.")

    #To check or give money
    if message.content == "!money":
        #Get money owed
        try:
            with open("Files/MoneyOwed.txt","r") as f:
                moneylines=f.readlines()
                moneyids = []
                moneyoweds = []
                for i in range(len(moneylines)):
                    if i%2 == 0:
                        moneyids.append(int(moneylines[i].rstrip("\n")))
                    else:
                        moneyoweds.append(int(moneylines[i].rstrip("\n")))
        except:
            print("Could not read from MoneyOwed.txt")
            return
        if len(moneyids) == 0:
            await message.channel.send("No one is currently owed any credits.")
            return
        casinobot = discord.utils.get(message.guild.members, id=casinoid)
        if str(casinobot.status) == "online":
            for i in range(len(moneyids)):
                await message.channel.send("$give <@!{}> {}".format(moneyids[i],moneyoweds[i]))
                time.sleep(0.5)
            try:
                with open("Files/MoneyOwed.txt","w") as f:
                    f.write("")
            except:
                print("Could not read from MoneyOwed.txt")
                return
        else:
            moneystr = "CasinoBot is offline!\n"
            for i in range(len(moneyids)):
                moneystr = moneystr + "<@!{}> is owed {} credits!\n".format(moneyids[i],moneyoweds[i])
            await message.channel.send(moneystr)

    #To display team
    if message.content == "!team":
        await displayTeam()

    #Beyond here are commands that only work if currently solving a sudoku
    if cursolving != "Solving":
        return
    if message.channel != curchannel:
        return

    #Should it be saved?
    saving = False

    #Saves data
    if message.content == "!save":
        saving = True

    #To join the team
    if message.content == "!join":
        if message.author.id in sudokuTeam:
            await curchannel.send("You are already in the team.")
        elif len(sudokuTeam) >= teamsize:
            await curchannel.send("The team is full!")
        else:
            sudokuTeam.append(message.author.id)
            await curchannel.send("{} has joined the team!".format(message.author.mention))
            saving = True
    
    if message.author.id in sudokuTeam:
        #If a team member decides to quit
        if message.content == "!quit":
            await curchannel.send("You have chosen to quit the team.")
            sudokuTeam.remove(message.author.id)
            saving = True
        #If a team member decides to resign
        if message.content == "!resign":
            await curchannel.send("You have chosen to resign.")
            cursolving = "No"
            saving = True

    global writeMode
    replycontent = message.content
    
    #Gets mode, if it has been set
    if not replycontent.startswith("!"):
        if not (replycontent.startswith("add") or replycontent.startswith("remove")):
            replycontent = " " + replycontent
        replycontent = writeMode + replycontent

    #To write a number to the sudoku
    if replycontent.startswith("!write"):
        if message.author.id not in sudokuTeam:
            if len(sudokuTeam) >= teamsize:
                await curchannel.send("The team is full!")
                return
            else:
                sudokuTeam.append(message.author.id)
                await curchannel.send("{} has joined the team!".format(message.author.mention))
                saving = True
        try:
            commandlist = replycontent.split()
            assert len(commandlist) == 3
            gridcoords = commandlist[1]
            gridnumstr = commandlist[2]
            assert len(gridcoords) == 2
            gridxstr = gridcoords[0]
            gridystr = gridcoords[1]
            gridx = ord(gridxstr) - 97
            gridy = dimsquared - int(gridystr)
            gridnum = int(gridnumstr)
            assert 0 <= gridx < dimsquared
            assert 0 <= gridy < dimsquared
            assert 0 < gridnum <= dimsquared
        except:
            await curchannel.send("To write a number, type \"!write\" followed by the coordinates and then what you want to write e.g. \"!write a1 1\"")
            return
        if sudokuArray[gridy][gridx][0] == "Clue":
            await curchannel.send("You cannot overwrite a clue!")
            return
        sudokuArray[gridy][gridx] = ["Write",gridnum]
        await displaySudoku()
        await checkSolved()
        
    #To clear a number
    if replycontent.startswith("!clear"):
        if message.author.id not in sudokuTeam:
            if len(sudokuTeam) >= teamsize:
                await curchannel.send("The team is full!")
                return
            else:
                sudokuTeam.append(message.author.id)
                await curchannel.send("{} has joined the team!".format(message.author.mention))
                saving = True
        try:
            commandlist = replycontent.split()
            assert len(commandlist) == 2
            gridcoords = commandlist[1]
            assert len(gridcoords) == 2
            gridxstr = gridcoords[0]
            gridystr = gridcoords[1]
            gridx = ord(gridxstr) - 97
            gridy = dimsquared - int(gridystr)
            assert 0 <= gridx < dimsquared
            assert 0 <= gridy < dimsquared
        except:
            await curchannel.send("To clear a number, type \"!clear\" followed by the coordinates e.g. \"!clear a1\"")
            return
        if sudokuArray[gridy][gridx][0] == "Clue":
            await curchannel.send("You cannot overwrite a clue!")
            return
        sudokuArray[gridy][gridx] = ["Clear"]
        await displaySudoku()

    #To make pencil marks
    if replycontent.startswith("!pencil"):
        if message.author.id not in sudokuTeam:
            if len(sudokuTeam) >= teamsize:
                await curchannel.send("The team is full!")
                return
            else:
                sudokuTeam.append(message.author.id)
                await curchannel.send("{} has joined the team!".format(message.author.mention))
                saving = True
        try:
            if replycontent.startswith("!penciladd"):
                penciladd = True
            else:
                penciladd = False
            if replycontent.startswith("!pencilremove"):
                pencilremove = True
            else:
                pencilremove = False
            commandlist = replycontent.split()
            assert len(commandlist) > 2
            gridxylist = []
            i = 1
            while len(commandlist[i]) > 1:
                gridcoords = commandlist[i]
                assert len(gridcoords) == 2
                gridxstr = gridcoords[0]
                gridystr = gridcoords[1]
                gridx = ord(gridxstr) - 97
                gridy = dimsquared - int(gridystr)
                assert 0 <= gridx < dimsquared
                assert 0 <= gridy < dimsquared
                if sudokuArray[gridy][gridx][0] == "Clue":
                    await curchannel.send("You cannot overwrite a clue!")
                    return
                gridxylist.append([gridx,gridy])
                i += 1
            pencillist = commandlist[i:]
            for i in range(len(gridxylist)):
                gridx = gridxylist[i][0]
                gridy = gridxylist[i][1]
                if sudokuArray[gridy][gridx][0] == "Pencil" and (penciladd or pencilremove):
                    pencilset = sudokuArray[gridy][gridx][1]
                    pass
                else:
                    pencilset = set()
                for i in range(len(pencillist)):
                    pencilnum = int(pencillist[i])
                    assert 0 < pencilnum <= dimsquared
                    if pencilremove:
                        pencilset.discard(pencilnum)
                    else:
                        pencilset.add(pencilnum)
                sudokuArray[gridy][gridx] = ["Pencil",pencilset]
        except:
            if replycontent.startswith("!penciladd"):
                await curchannel.send("To add pencil marks, type \"!penciladd\" followed by the coordinates and then what you want to add e.g. \"!penciladd a1 1 2 3\"")
            elif replycontent.startswith("!pencilremove"):
                await curchannel.send("To remove pencil marks, type \"!pencilremove\" followed by the coordinates and then what you want to remove e.g. \"!pencilremove a1 1 2 3\"")
            else:
                await curchannel.send("To make pencil marks, type \"!pencil\" followed by the coordinates and then what you want to write e.g. \"!pencil a1 1 2 3\"")
            return
        await displaySudoku()

    #Sets mode
    if message.content.startswith("!mode"):
        if message.content == "!mode reset":
            writeMode = ""
            await curchannel.send("Mode reset.")
        elif message.content == "!mode write":
            writeMode = "!write"
            await curchannel.send("Mode set to write.")
        elif message.content == "!mode pencil":
            writeMode = "!pencil"
            await curchannel.send("Mode set to pencil.")
        else:
            await curchannel.send("To set mode to write/pencil, type \"!mode write\" or \"!mode pencil\", or type \"!mode reset\" to reset mode.")
    
    #Save data if need be
    if saving:
        if await saveData():
            await curchannel.send("Data saved successfully.")
        else:
            await curchannel.send("There was an error in saving the data.")

#Select a sudoku out of those available
async def selectSudoku():
    global sudokuArray,cursolving,sudokuTeam,sudokuName
    await curchannel.send("Please select the sudoku you wish to play out of the following list.")
    try:
        with open("Files/ListOfSudokus.txt","r") as f:
            sudokulines=f.readlines()
        sudokunames = []
        sudokudiffs = []
        #1 is easy, 2 is medium, 3/4 is hard, 5/6/7 is diabolical
        #Anything beyond 6 is extreme, except escargot etc. which are ultra-extreme
        sudokusolveds = []
        for i in range(len(sudokulines)):
            if i%3 == 0:
                sudokunames.append(sudokulines[i].rstrip("\n"))
            elif i%3 == 1:
                sudokudiffs.append(sudokulines[i].rstrip("\n"))
            else:
                sudokusolveds.append(sudokulines[i].rstrip("\n") == "True")
        messagestr = ""
        for i in range(len(sudokusolveds)):
            sudokustr = str(i+1) + ": " + sudokudiffs[i]
            if sudokusolveds[i]:
                sudokustr = sudokustr + " (Solved)\n"
            else:
                sudokustr = sudokustr + " (Unsolved)\n"
            messagestr = messagestr + sudokustr
        await curchannel.send(messagestr)
    except:
        print("Could not read from ListOfSudokus.txt")
        return
    await curchannel.send("Type \"generate\" to generate a new sudoku at a specified difficulty.")

    def channel_check(m):
        return m.channel == curchannel

    generateChosen = False

    #Get a response
    while True:
        reply = await client.wait_for("message", check=channel_check)
        if reply.content == "generate":
            generateChosen = True
            break
        try:
            replynum = int(reply.content)-1
            assert replynum >= 0 and replynum < len(sudokusolveds)
            break
        except:
            continue

    #If generating a sudoku, get a response.
    if generateChosen:
        messagestring = "Choose the difficulty of the sudoku you wish to generate.\n"
        for i in range(genDiffs):
            messagestring = messagestring + "{}: {}\n".format(i+1,listofdiffs[i])
        await curchannel.send(messagestring)
        while True:
            reply = await client.wait_for("message", check=channel_check)
            try:
                diff = int(reply.content)-1
                assert diff >= 0 and diff < genDiffs
                break
            except:
                continue
        await curchannel.send("You have chosen to generate a sudoku of {} difficulty.".format(listofdiffs[diff]))
        await curchannel.send("Generating...")
        sudokurawdata = SudokuMaster.generateDiff(masterDiffs[diff][0],masterDiffs[diff][1])

        #Add to ListOfSudokus
        sudokuNum = 0
        while os.path.isfile("Sudokus/gen{}.txt".format(sudokuNum)):
            sudokuNum += 1
        sudokuName = "gen{}.txt".format(sudokuNum)
        try:
            with open("Sudokus/"+sudokuName,"w") as f:
                f.writelines(sudokurawdata)
        except:
            print("Could not write sudoku.txt")
            return
        if not sudokulines[-1].endswith("\n"):
             sudokulines[-1] =  sudokulines[-1] + "\n"
        sudokulines.append(sudokuName+"\n")
        sudokulines.append(listofdiffs[diff]+"\n")
        sudokulines.append("False")
        try:
            with open("Files/ListOfSudokus.txt","w") as f:
                f.writelines(sudokulines)
        except:
            print("Could not write to ListOfSudokus.txt")
            return

    #If loading an existing sudoku:
    else:
        sudokuName = sudokunames[replynum]
        
        await curchannel.send("Loading sudoku...")

        #Convert text file to array to work with
        try:
            with open("Sudokus/"+sudokuName,"r") as f:
                sudokurawdata=f.readlines()
        except:
            print("Could not read from sudoku file.")
            return

    sudokuArray=[[None]*dimsquared for i in range(dimsquared)]
    for i in range(len(sudokurawdata)):
        for j in range(dimsquared):
            char = sudokurawdata[i][j]
            if char == " ":
                sudokuArray[i][j] = ["Clear"]
            else:
                sudokuArray[i][j] = ["Clue",int(char)]

    sudokuTeam = [reply.author.id]
    cursolving = "Solving"

    #Save and display sudoku
    await saveData()
    await displaySudoku()
    await displayTeam()

#Saves data to files
async def saveData():
    global cursolving,curchannel
    
    if cursolving == "Selecting":
        cursolving = "No"
    #Save cursolving
    try:
        with open("Files/CurrentlyPlaying.txt","w") as f:
            f.write(cursolving)
    except:
        print("Could not write to CurrentlyPlaying.txt")
        return False
    if cursolving == "Solving":
        #Save curchannel
        try:
            with open("Files/ChannelID.txt","w") as f:
                f.write(str(curchannel.id))
        except:
            print("Could not write to ChannelID.txt")
            return False
        #Save sudokuTeam
        try:
            teamstr = ""
            for i in range(len(sudokuTeam)):
                teamstr = teamstr + str(sudokuTeam[i]) + "\n"
            with open("Files/TeamPlayers.txt","w") as f:
                f.write(teamstr)
        except:
            print("Could not write to TeamPlayers.txt")
            return False
        #Save sudokuName
        try:
            with open("Files/SudokuName.txt","w") as f:
                f.write(sudokuName)
        except:
            print("Could not write to SudokuName.txt")
            return False
        #Save sudokuArray
        try:
            with open("Files/SudokuData.txt","wb") as f:
                pickle.dump(sudokuArray,f)
        except:
            print("Could not write to SudokuData.txt")
            return False
    return True

#Gets graphics from files
async def getGraphics():
    global bigDigits,smallDigits,blueDigits
    global bigDigitsPixels,smallDigitsPixels,blueDigitsPixels
    
    #Get big, small, and blue digits
    bigDigits = []
    bigDigitsPixels = []
    smallDigits = []
    smallDigitsPixels = []
    blueDigits = []
    blueDigitsPixels = []
    try:
        for i in range(dimsquared):
            bigDigits.append(Image.open("Files/BigDigit{}.bmp".format(i+1)))
            bigDigitsPixels.append(bigDigits[i].load())
            smallDigits.append(Image.open("Files/SmallDigit{}.bmp".format(i+1)))
            smallDigitsPixels.append(smallDigits[i].load())
    except:
        print("Could not read from a digit file.")
        return
    blueDigits = copy.deepcopy(bigDigits)
    for i in range(dimsquared):
        blueDigitsPixels.append(blueDigits[i].load())
        for j in range(bigSize):
            for k in range(bigSize):
                if blueDigitsPixels[i][j,k] == (0, 0, 0):
                    blueDigitsPixels[i][j,k] = (0, 0, 255)    

#Displays sudoku as a .bmp converted to .png file
async def displaySudoku():
    global basicGrid,basicGridPixels

    try:
        basicGrid = Image.open("Files/basicGrid.bmp")
        basicGridPixels = basicGrid.load()
    except:
        print("Could not read from basicGrid.bmp")
        return

    #Function for putting pencilmarks in a square
    def pencilmark(xpos,ypos,pencilset):
        for k in range(dim):
            yoffset = 1 + (smallSize+1)*k
            for l in range(dim):
                xoffset = 1 + (smallSize+1)*l
                klnum = k*dim + l + 1
                if klnum in pencilset:
                    basicGrid.paste(smallDigits[klnum-1],(xpos+xoffset,ypos+yoffset,xpos+xoffset+smallSize,ypos+yoffset+smallSize))

    for i in range(dimsquared):
        ypos = startY + i*(bigSize+smallGap) + (i//dim)*bigGap
        for j in range(dimsquared):
            xpos = startX + j*(bigSize+smallGap) + (j//dim)*bigGap
            
            if sudokuArray[i][j][0] == "Clue":
                cluenum = sudokuArray[i][j][1]-1
                basicGrid.paste(bigDigits[cluenum],(xpos,ypos,xpos+bigSize,ypos+bigSize))
            if sudokuArray[i][j][0] == "Write":
                cluenum = sudokuArray[i][j][1]-1
                basicGrid.paste(blueDigits[cluenum],(xpos,ypos,xpos+bigSize,ypos+bigSize))
            if sudokuArray[i][j][0] == "Pencil":
                pencilset = sudokuArray[i][j][1]
                pencilmark(xpos,ypos,pencilset)

    basicGrid.save("Files/curGrid.png","png")
    await curchannel.send(file=discord.File('Files/curGrid.png'))

#Lists current team
async def displayTeam():
    messagestring = "The current team is "
    for i in range(len(sudokuTeam)):
        messagestring = messagestring + "<@!" + str(sudokuTeam[i]) + ">, "
    messagestring = messagestring.rstrip(", ")
    await curchannel.send(messagestring)

#Checks whether a sudoku has been solved
async def checkSolved():
    global cursolving
    
    #Check to see if every square is written in and, if so, get its digit
    griddigits=[[None]*dimsquared for i in range(dimsquared)]
    for i in range(dimsquared):
        for j in range(dimsquared):
            if sudokuArray[i][j][0] not in ["Clue","Write"]:
                return
            griddigits[i][j] = sudokuArray[i][j][1]

    #Check rows
    for i in range(dimsquared):
        digitset = set()
        for j in range(dimsquared):
            digitset.add(griddigits[i][j])
        if digitset != set(range(1,dimsquared+1)):
            return

    #Check columns
    for j in range(dimsquared):
        digitset = set()
        for i in range(dimsquared):
            digitset.add(griddigits[i][j])
        if digitset != set(range(1,dimsquared+1)):
            return

    #Check boxes
    for k in range(dim):
        for l in range(dim):
            digitset = set()
            for i in range(dim):
                for j in range(dim):
                    digitset.add(griddigits[i+dim*k][j+dim*l])
            if digitset != set(range(1,dimsquared+1)):
                return

    #It should be solved now!

    await curchannel.send("The sudoku has been solved! Kudos to you!")
    await displayTeam()

    #Get sudoku information from list
    try:
        with open("Files/ListOfSudokus.txt","r") as f:
            sudokulines=f.readlines()
        sudokunames = []
        sudokudiffs = []
        sudokusolveds = []
        for i in range(len(sudokulines)):
            if i%3 == 0:
                sudokunames.append(sudokulines[i].rstrip("\n"))
            elif i%3 == 1:
                sudokudiffs.append(sudokulines[i].rstrip("\n"))
            else:
                sudokusolveds.append(sudokulines[i].rstrip("\n") == "True")
    except:
        print("Could not read from ListOfSudokus.txt")
        return

    for i in range(len(sudokunames)):
        if sudokunames[i] == sudokuName:
            sudokuNumber = i
            curDifficulty = sudokudiffs[i]
            curSolved = sudokusolveds[i]

    #Give money if it is unsolved
    if not curSolved:
        sudokulines[sudokuNumber*3+2] = "True\n"
        try:
            with open("Files/ListOfSudokus.txt","w") as f:
                f.writelines(sudokulines)
        except:
            print("Could not write to ListOfSudokus.txt")
            return
        for i in range(len(listofdiffs)):
            if listofdiffs[i] == curDifficulty:
                curMoney = listofmoney[i]
                
        #Get list of current money owed
        try:
            with open("Files/MoneyOwed.txt","r") as f:
                moneylines=f.readlines()
                moneyids = []
                moneyoweds = []
                for i in range(len(moneylines)):
                    if i%2 == 0:
                        moneyids.append(int(moneylines[i].rstrip("\n")))
                    else:
                        moneyoweds.append(int(moneylines[i].rstrip("\n")))
        except:
            print("Could not read from MoneyOwed.txt")
            return
        for i in sudokuTeam:
            if i in moneyids:
                for j in range(len(moneyids)):
                    if i == moneyids[j]:
                        moneyoweds[j] += curMoney
            else:
                moneyids.append(i)
                moneyoweds.append(curMoney)
        moneyowedstr = ""
        for i in range(len(moneyids)):
            moneyowedstr = moneyowedstr + str(moneyids[i]) + "\n" + str(moneyoweds[i]) + "\n"
        with open("Files/MoneyOwed.txt","w") as f:
            f.write(moneyowedstr)
        await curchannel.send("Everyone on the team got {} credits for CasinoBot. To transfer these, type \"!money\" when CasinoBot is online.".format(curMoney))

    cursolving = "No"

    if await saveData():
        await curchannel.send("Data saved successfully.")
    else:
        await curchannel.send("There was an error in saving the data.")

client.run('TOKEN')

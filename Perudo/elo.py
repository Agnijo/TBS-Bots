#Removes exclamaion mark from mention in order to standardise it
def removeExclamation(mention):
    if len(mention) > 2:
        if mention[2]=="!":
            mention="<@"+mention[3:]
    return str(mention)

#Gets elos from file
def getelos():
    elofile = open("elo.txt","r")
    elolines = elofile.readlines()
    elofile.close()
    playermentions = []
    playerelos = []
    for i in range(len(elolines)):
        if i%2 == 0:
            playermentions.append(elolines[i].rstrip("\n"))
        else:
            playerelos.append(int(elolines[i].rstrip("\n")))
    return playermentions,playerelos

#Saves elos to file
def saveelos(playermentions,playerelos):
    elostr = ""
    for i in range(len(playermentions)):
        elostr = elostr+playermentions[i]+"\n"+str(playerelos[i])+"\n"
    elostr.rstrip("\n")
    elofile = open("elo.txt","w")
    elofile.write(elostr)
    elofile.close()

#Calculate elo change in one pair
def elotransfer(elo1,elo2,result):

    elopower = 1.005773     #Roughly 10^(1/400)
    kfactor = 32            #Maximum change in elo for one pair
    elocutoff = 720         #Cutoff where change in elo is less than half a point
    
    elodiff = elo2-elo1

    #Make absolute value of elodiff at most elocutoff
    if elodiff > elocutoff:
        elodiff = elocutoff
    if elodiff < -elocutoff:
        elodiff = -elocutoff

    #Expected result for player 1
    expectedresult = 1/(1+elopower**elodiff)

    #Change in elo for player 1
    elochange = round(kfactor*(result - expectedresult))
    return elochange

#Updates elos based on player results
def updateelos(playerlist,playerpoints):

    elocutoff = 100         #Elo at which you can start to lose elo
    
    #Get all stored elos
    allplayermentions,allplayerelos = getelos()

    #If a player is not in the elo file, add it with 0 elo
    for i in playerlist:
        imention = removeExclamation(i.mention)
        if imention not in allplayermentions:
            allplayermentions.append(imention)
            allplayerelos.append(0)

    #Index of each player in file
    playerfileindices = []
    for i in range(len(playerlist)):
        fileindex = 0
        for j in range(len(allplayermentions)):
            if removeExclamation(playerlist[i].mention) == allplayermentions[j]:
                fileindex = j
        playerfileindices.append(fileindex)

    #Each player's current elo
    playerelo = []
    playerelochange = []
    newplayerelo = []
    for i in range(len(playerlist)):
        playerelo.append(allplayerelos[playerfileindices[i]])
        playerelochange.append(0)
        newplayerelo.append(0)

    #Update elos for each pair
    for i in range(len(playerlist)):
        for j in range(i):
            elo1 = playerelo[i]
            elo2 = playerelo[j]
            result = 0
            if playerpoints[i] > playerpoints[j]:
                result = 1
            if playerpoints[i] == playerpoints[j]:
                result = 0.5
            elochange = elotransfer(elo1,elo2,result)
            playerelochange[i] += elochange
            playerelochange[j] -= elochange

    #Stops elo from being reduced if it is too low
    #(and makes players with 0 elo gain at least 1)
    for i in range(len(playerlist)):
        elofloor = max(1,playerelo[i])
        elofloor = min(elofloor,elocutoff)
        if playerelochange[i] < elofloor - playerelo[i]:
            playerelochange[i] = elofloor - playerelo[i]

    #Finds new elos of current players
    for i in range(len(playerlist)):
        newplayerelo[i] = playerelo[i] + playerelochange[i]

    #Updates elos in file
    for i in range(len(playerlist)):
        allplayerelos[playerfileindices[i]] = newplayerelo[i]
    saveelos(allplayermentions,allplayerelos)

    return playerelochange,newplayerelo

#Reports a player's elo (returning False if player lacks elo)
def fetchelo(messagemention):
    playermentions,playerelos = getelos()    
    elovalue = 0
    for i in range(len(playermentions)):
        if messagemention == playermentions[i]:
            elovalue = playerelos[i]
    return elovalue

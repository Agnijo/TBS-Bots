from utils import *
from random import shuffle,randint
import copy

#Chooses card from hand, given seen cards and table
def botchoosecard(bothand,unseencards,rowlength,rows,roweffects,numhumans):

    numtrials = 10      #Number of random trials done for mean points taken
    specialval = 3.685  #Point offset for playing special card
                        #Ideally roughly equal to mean points taken in later rounds

    #Exclude the actual bot hand from unseencards
    unseencards = copy.deepcopy(unseencards)
    unseencards.difference_update(bothand)
    
    #Check whether any cards are safe (barring deliberate spite)
    minrowbeef = 0
    unsaferows = []
    for i in range(len(rows)):
        rowbeef = rowbeefcalc(rows[i],roweffects[i])
        if i == 0:
            minrowbeef = rowbeef
        if rowbeef == minrowbeef:
            unsaferows.append(i)
        elif rowbeef < minrowbeef:
            minrowbeef = rowbeef
            unsaferows = [i]
    saferows = []
    for i in range(len(rows)):
        if i not in unsaferows:
            saferows.append(i)

    #Once safe rows to put cards in have been found, see which cards are safe
    potentialsafecards = []
    maxbothand = 0
    for i in bothand:
        if type(i) == int:
            if i > maxbothand:
                maxbothand = i
    for i in range(len(saferows)):
        rowspace = rowlength - len(rows[saferows[i]])
        rowright = rows[saferows[i]][-1]
        count = 0
        j = rowright+1
        while count < rowspace and j <= maxbothand:
            potentialsafecards.append(j)
            if j in unseencards:
                count += 1
            j += 1

    #See which potentially safe cards are actually in the bot's hand
    safecards = []
    for i in potentialsafecards:
        if i in bothand:
            safecards.append(i)

    #If any cards are safe, pick the most useful one to get rid of
    if len(safecards) > 0:
        maxvalue = 0
        chosencard = safecards[0]
        for i in safecards:
            cardval = cardvalue(i,bothand,specialval)
            if cardval > maxvalue:
                maxvalue = cardval
                chosencard = i
        return chosencard
    
    #If no cards are safe, simulate playing random cards numtrials times with each card
    cardvals = []
    for i in range(len(bothand)):
        meancost = 0
        botcard = bothand[i]
        for j in range(numtrials):
            fakeplayed = [botcard]
            shuffledunseens = unseencards.copy()
            shuffledlist = []
            while len(shuffledunseens) > 0:
                shuffledlist.append(shuffledunseens.pop())
            shuffle(shuffledlist)
            fakeplayed.extend(shuffledlist[:numhumans])
            fakesortedcards = sorthand(fakeplayed)
            fakerows = copy.deepcopy(rows)
            fakeroweffects = copy.deepcopy(roweffects)
            botcost,humancost,rowpicked = simulateround(botcard,fakesortedcards,rowlength,fakerows,fakeroweffects)
            meancost += botcost
        meancost = meancost/numtrials
        meancost -= cardvalue(bothand[i],bothand,specialval)
        cardvals.append(meancost)

    #Now that the cards have been simulated, choose the one with the lowest cost
    mincost = 0
    chosencard = bothand[0]
    for i in range(len(bothand)):
        cardcost = cardvals[i]
        if i == 0:
            mincost = cardcost
        if cardcost < mincost:
            mincost = cardcost
            chosencard = bothand[i]
    return chosencard

#An estimate of the value of playing a card (offset for losses incurred)
def cardvalue(card,bothand,specialval):
    if type(card) != int:
        #Return something roughly equal to the loss for a random card in the latter half
        return -specialval
    cardval = 1/card
    for i in bothand:
        if type(i) == int:
            if i > card:
                cardval += 0.5/(i-card)
    return cardval

#Simulates a round, calculating bot losses and combined human losses
def simulateround(botcard,fakesortedcards,rowlength,rows,roweffects):

    if len(fakesortedcards) == 0:
        return 0,0,0

    #This is only used if the bot is actually picking a row
    rowpicked = 0
    
    botcost = 0
    humancost = 0

    rightcards = []
    for i in range(len(rows)):
        rightcards.append(rows[i][-1])

    firstcard = fakesortedcards[0]
    remainingcards = fakesortedcards[1:]

    botplayingnow = False
    if botcard == firstcard:
        botplayingnow = True

    #Cards that have an effect on a row
    rowcards = ["Barricade","Beef Up","First Choice","Ranch Salad"]

    cardinrow = False
    for i in range(len(rowcards)):
        if firstcard.startswith(rowcards[i]):
            cardinrow = True
            cardeffect = rowcards[i]

    #If the card to be played has a row effect
    if cardinrow:
        if botplayingnow:
            #Choose a row maximising human cost
            maxhumancost = 0
            maxhumancostrow = []
            firstrow = True     #Just in case the human cost is always negative, make it match the first row
            for j in range(len(rows)):
                if "Barricade" not in roweffects[j]:
                    newroweffects = copy.deepcopy(roweffects)
                    newroweffects[j].append(cardeffect)
                    newroweffects[j] = sorthand(newroweffects[j])
                    botcostnew,humancostnew,rowpickednew = simulateround(botcard,remainingcards,rowlength,rows,newroweffects)
                    if firstrow:
                        maxhumancost = humancostnew
                        firstrow = False
                    if humancostnew == maxhumancost:
                        maxhumancostrow.append(j)
                    elif humancostnew > maxhumancost:
                        maxhumancost = humancostnew
                        maxhumancostrow = [j]
            humancost = maxhumancost
            randrow = randint(0,len(maxhumancostrow)-1)
            rowpicked = maxhumancostrow[randrow]
        else:
            #Take the mean value based on which row is chosen
            rownum = 0
            for j in range(len(rows)):
                if "Barricade" not in roweffects[j]:
                    newroweffects = copy.deepcopy(roweffects)
                    newroweffects[j].append(cardeffect)
                    newroweffects[j] = sorthand(newroweffects[j])
                    botcostnew,humancostnew,rowpickednew = simulateround(botcard,remainingcards,rowlength,rows,newroweffects)
                    botcost += botcostnew
                    humancost += humancostnew
                    rownum += 1
            botcost = botcost/rownum
            humancost = humancost/rownum

    #If the card to be played is numerical
    elif type(firstcard) == int:
        maxright = 0
        cardrow = -1
        for j in range(len(rows)):
            if rightcards[j] < firstcard and rightcards[j] > maxright and "Barricade" not in roweffects[j]:
                maxright = rightcards[j]
                cardrow = j
        if cardrow == -1:
            for j in range(len(rows)):
                if "First Choice" in roweffects[j] and "Barricade" not in roweffects[j]:
                    cardrow = j

        #If there is a choice as to which row to pick
        if cardrow == -1:
            minbeef = 0
            viablerows = []
            firstrow = True
            for j in range(len(rows)):
                if "Barricade" not in roweffects[j]:
                    rowbeef = rowbeefcalc(rows[j],roweffects[j])
                    if firstrow:
                        minbeef = rowbeef
                        firstrow = False
                    if rowbeef == minbeef:
                        viablerows.append(j)
                    elif rowbeef < minbeef:
                        minbeef = rowbeef
                        viablerows = [j]
            beeftaken = minbeef
            #If this is the bot's card, maximise human cost
            if botplayingnow:
                botcost = beeftaken
                maxhumancost = 0
                maxhumancostrow = []
                for j in range(len(viablerows)):
                    newrows = copy.deepcopy(rows)
                    newroweffects = copy.deepcopy(roweffects)
                    newrows[viablerows[j]] = [firstcard]
                    newroweffects[viablerows[j]] = []
                    botcostnew,humancostnew,rowpickednew = simulateround(botcard,remainingcards,rowlength,newrows,newroweffects)
                    if j == 0:
                        maxhumancost = humancostnew
                    if humancostnew == maxhumancost:
                        maxhumancostrow.append(j)
                    elif humancostnew > maxhumancost:
                        maxhumancost = humancostnew
                        maxhumancostrow = [j]
                humancost = maxhumancost
                randrow = randint(0,len(maxhumancostrow)-1)
                rowpicked = viablerows[maxhumancostrow[randrow]]
            else:
                #Take the mean value based on which viable row is chosen

                for j in range(len(viablerows)):
                    newrows = copy.deepcopy(rows)
                    newroweffects = copy.deepcopy(roweffects)
                    newrows[viablerows[j]] = [firstcard]
                    newroweffects[viablerows[j]] = []
                    botcostnew,humancostnew,rowpickednew = simulateround(botcard,remainingcards,rowlength,newrows,newroweffects)
                    botcost += botcostnew
                    humancost += humancostnew
                botcost = botcost/len(viablerows)
                humancost = humancost/len(viablerows)
                humancost += beeftaken
        #If there is no choice in which row to pick
        else:
            newrows = copy.deepcopy(rows)
            newroweffects = copy.deepcopy(roweffects)
            if len(newrows[cardrow]) == rowlength:
                beeftaken = rowbeefcalc(rows[cardrow],roweffects[cardrow])
                newroweffects[cardrow] = []
                newrows[cardrow] = [firstcard]
                if botplayingnow:
                    botcost = beeftaken
                else:
                    humancost = beeftaken
            else:
                newrows[cardrow].append(firstcard)
            botcostnew,humancostnew,rowpickednew = simulateround(botcard,remainingcards,rowlength,newrows,newroweffects)
            botcost += botcostnew
            humancost += humancostnew
    return botcost,humancost,rowpicked

#When the bot has to pick a row
def botchooserow(sortedplayedcards,botorder,rowlength,rows,roweffects):
    fakesortedcards = sortedplayedcards[botorder:]
    botcard = fakesortedcards[0]
    botcost,humancost,rowpicked = simulateround(botcard,fakesortedcards,rowlength,rows,roweffects)
    return rowpicked

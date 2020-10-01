#Sorts hand (or any set of cards)
def sorthand(hand):
    newhand = hand.copy()
    inthand = []
    strhand = []
    for i in range(len(newhand)):
        if type(newhand[i]) == int:
            inthand.append(newhand[i])
        else:
            strhand.append(newhand[i])
    strhand.sort()
    inthand.sort()
    strhand.extend(inthand)
    return strhand

#Gives number of beef heads of card
def beefhead(card):
    if type(card) != int:
        return 0
    if card % 55 == 0:
        return 7
    if card % 11 == 0:
        return 5
    if card % 10 == 0:
        return 3
    if card % 5 == 0:
        return 2
    return 1

#Turns rows and row effects into a table string
def tablestring(rowlength,rows,roweffects):
    messagestring = "The following cards are on the table:\n"
    for i in range(len(rows)):
        rowstring = ""
        for j in range(len(rows[i])):
            rowstring = rowstring + str(rows[i][j])+", "
        for j in range(rowlength-len(rows[i])):
            rowstring = rowstring + "\_\_, "
        rowstring = rowstring.rstrip(", ")
        rowbeef = rowbeefcalc(rows[i],roweffects[i])
        rowstring = rowstring + " - {} beef heads".format(rowbeef)
        effectstring = ""
        for j in range(len(roweffects[i])):
            effectstring = effectstring + roweffects[i][j]+", "
        effectstring = effectstring.rstrip(", ")
        if effectstring != "":
            effectstring = " ({})".format(effectstring)
        rowstring = rowstring + effectstring
        if "Barricade" in roweffects[i]:
            rowstring = "~~{}~~".format(rowstring)
        messagestring = messagestring + rowstring + "\n"
    return messagestring

#Calculates number of beef heads in row
def rowbeefcalc(row,roweffect):
    rowbeef = 0
    for j in range(len(row)):
        rowbeef += beefhead(row[j])
    if "Beef Up" in roweffect:
        rowbeef = rowbeef*2
    if "Ranch Salad" in roweffect:
        rowbeef = -rowbeef
    return rowbeef

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

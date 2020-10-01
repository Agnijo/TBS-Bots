import discord
from random import shuffle

#Displays roles as a string
async def roledisplay(client,message,roleslist,roles,initstr):
    #Determine initial string for role message
    if initstr == 0:
        rolestr = "Current roles:\n"
    if initstr == 1:
        rolestr = "Game started with roles:\n"

    for i in range(len(roles)):
        for j in range(len(roleslist)):
            if roleslist[j] == roles[i]:
                rolestr = rolestr+roles[i]+", "
    rolestr = rolestr.rstrip(", ")
    await message.channel.send(rolestr)

#Assigns cards
def giveroles(centrecards,roleslist):
    startplayerroles = roleslist.copy()
    shuffle(startplayerroles)
    startcentreroles = startplayerroles[:centrecards]
    startplayerroles = startplayerroles[centrecards:]
    return startplayerroles,startcentreroles

#Gets playerstring
def playerstring(playerlist):
    playerstr = ""
    for i in range(len(playerlist)):
        playerstr = playerstr + "{}: {}\n".format(i+1,playerlist[i].display_name)
    return playerstr

#Checks whether channel is DM
def dmCheck(channel):
    if str(channel).startswith("Direct Message with"):
        return True
    return False

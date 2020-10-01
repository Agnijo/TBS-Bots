import discord

async def helpcommand(client,message):
    messagestring = "Commands:\n"
    messagestring += "!perudo - starts the game\n"
    messagestring += "!help - gives a list of commands\n"
    messagestring += "!rules - gives a list of rules\n"
    messagestring += "!help abilities - gives details of the one-time abilities\n"
    messagestring += "!join - join the game during login phase\n"
    messagestring += "!quit - quit the game during login phase\n"
    messagestring += "!start - start playing with the current playerlist\n"
    messagestring += "!start freebidding - start with free bidding instead of BGA restrictions\n"
    messagestring += "!start calza - start with calza enabled\n"
    messagestring += "!start abilities - start with one-time abilities enabled\n"
    messagestring += "To make a bid, type \"x y\" with x being the number of dice you want to bid and y being the value\n"
    messagestring += "(For example, type \"5 6\" to bid 5 sixes)\n"
    messagestring += "To call dudo on the previous bid, type dudo\n"
    messagestring += "To call calza on the previous bid, type calza\n"
    await message.channel.send(messagestring)

async def helpabilities(client,message):
    messagestring = "Abilities are unlocked as you lose dice and can each be used once in the entire game.\n"
    messagestring += "They can only be used on your own turn.\n"
    messagestring += "At three dice left, you can match the previous bid instead of increasing it.\n"
    messagestring += "Type \"match\" to do this.\n"
    messagestring += "At two dice left, you can reroll your own dice.\n"
    messagestring += "Type \"reroll\" to do this.\n"
    messagestring += "At one die left, you can see another player's dice.\n"
    messagestring += "Type \"see @playername\" to do this.\n"
    await message.channel.send(messagestring)

async def rules(client,message):
    messagestring = "Rules:\n"
    messagestring += "Each player initially has five dice.\n"
    messagestring += "At the start of each round, players roll their dice in secret.\n"
    messagestring += "On each turn, a player either makes a bid or calls dudo.\n"
    messagestring += "(On the first turn of a round, a bid must be made)\n"
    messagestring += "When bidding, a player states the number of dice and then the value.\n"
    messagestring += "The first bid of a round must not be a bid of ones, but any subsequent bid can be.\n"
    messagestring += "After the first bid, a player can either bid ones, increase the number of dice and keep the same value, or increase the value and keep the same number of dice.\n"
    messagestring += "If a player is bidding ones and the previous bidder did not, the number of dice bid must be at least half the previous bid.\n"
    messagestring += "If a player is not bidding ones when the previous bidder did, the number of dice bid must be strictly greater than twice the previous bid.\n"
    messagestring += "(If playing with free bidding, a player can either increase the number of dice and choose any value, or keep the same number of dice and increase the value.\n"
    messagestring += "Ones count for double the number of dice, are the highest value, and may be bid on the first turn.)\n"
    await message.channel.send(messagestring)
    messagestring = "If a player calls dudo, all dice are revealed.\n"
    messagestring += "The total number of dice showing the previous bid's value is counted up, with ones being wild.\n"
    messagestring += "If this number is greater than or equal to the previous bid, the player who calls dudo loses a die.\n"
    messagestring += "Otherwise, if this number is less than the previous bid, the previous bidder loses a die.\n"
    messagestring += "The player who lost a die begins the next round.\n"
    messagestring += "Once a player has lost all of their dice, they are out. The next player after them begins the next round.\n"
    messagestring += "If, after losing a die, a player has only one die left, the next round is a palifico round.\n"
    messagestring += "In a palifico round, ones are not wild.\n"
    messagestring += "Ones may be bid on the first bid like any other number, but the value on the first bid cannot be changed.\n"
    messagestring += "If playing with calza, any player may call calza on any bid (except the person who made the bid).\n"
    messagestring += "If the bid is exactly correct, the player who called calza gains a die.\n"
    messagestring += "(You cannot go above the initial number of dice by using calza)\n"
    messagestring += "Otherwise, the player who called calza loses a die.\n"
    messagestring += "The player who called calza begins the next round, regardless of whether they won or lost.\n"
    await message.channel.send(messagestring)

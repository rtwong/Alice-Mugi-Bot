import discord
from discord.ext import commands
import random

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='`', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='Why'))

bot.remove_command('help')

#MUGI GIFS
#
#pillow throw 
#
#
#
#
#


@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

@bot.command()
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))

@bot.command()
async def repeat(times : int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await bot.say(content)

@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))

@bot.group(pass_context=True)
async def cool(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await bot.say('No, {0.subcommand_passed} is not cool'.format(ctx))

@bot.command(name='mugiwhy')
async def _bot():
    """Is the bot cool?"""
    await bot.say('You better back the fuck up before you get smacked the fuck up')

@bot.command(name='fish')
async def fish():
	""" posts the mugi fish gif """
	await bot.say('http://pa1.narvii.com/5795/1fc45ddac9245f5a3beff456383787db9138b336_hq.gif')

@bot.command(name='fight')
async def fight():
	""" posts the mugi pillow gif """
	await bot.say('https://media.tenor.com/images/396f1f445a1befa7b6e7b082a2fcbac8/tenor.gif')
	await bot.say('ill fk u up bich')

@bot.command(name='jam')
async def jam():
	""" posts the mugi jammin gif """
	await bot.say('http://imgur.com/eR56w')

@bot.command(name='amaze')
async def amaze():
	""" posts the mugi jammin gif """
	await bot.say('https://media.tenor.com/images/571aa142a20ea4886ddf9b187094ea3c/tenor.gif')


@bot.command(name='help')
async def help():
	await bot.say('if u need help u dumb as fk')

@bot.event
async def on_message(message):
	"""parse test"""
	print('dum')
	if 'dum' in message.content and (message.author) != (bot.user): #str(message.author).startswith("Mugi"):
		user = str(message.author)
		name,id = user.split('#')
		print(id)
		phrase = message.author.mention + " you\'re dumb as hell tbh"
		await bot.send_message(message.channel, phrase)

	if message.tts:
		await bot.send_message(message.channel, 'stfu dumb bitch')

	if 'yosh' in message.content and (message.author) != (bot.user):
		await bot.send_message(message.channel, 'http://i.imgur.com/oiZxHlZ.gif')

	if 'fk u' in message.content and (message.author) != (bot.user):
		await bot.send_message(message.channel, 'http://i.imgur.com/x0rE1OW.gif')
		await bot.send_message(message.channel, 'O SHIT')

	await bot.process_commands(message)

bot.run('MzE5NzU0NTM5MjE1NDg2OTc3.DBFiNQ.O3nTIBSEIo6xS5riwmBNquvHxaQ')

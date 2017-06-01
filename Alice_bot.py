import discord
from discord.ext import commands
import random
import asyncio

description = '''Alice Nakiri on duty!'''

bot = commands.Bot(command_prefix='?', description=description, pm_help=True)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='Coding Manager 2017'))

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	if "alice" in message.content.lower() :
		await bot.send_message(message.channel, "https://s-media-cache-ak0.pinimg.com/originals/0a/92/d7/0a92d7d7f15ba1e4e14449ec29271cb7.gif")
		await bot.send_message(message.channel, "Stop talking about me!")

	await bot.process_commands(message)


@bot.command()
async def wobwob():
	"""Shows an enjoyable gif. """
	await bot.say('http://imgur.com/QSoL1ge')


recipe_categories = ["chicken", "pizza", "cocktails", "pasta", "burgers", "sandwiches", "desserts", "salad"]
@bot.command()
async def recipe(request_category : str):
	"""Links a recipe from SeriousEats of the specified type. """
	request_category = request_category.lower()
	if request_category == "random":
		recipe_category = random.choice(recipe_categories)
	elif request_category in recipe_categories:
		recipe_category = request_category
	else:
		await bot.say("Incorrect category, choose one of [chicken, pizza, cocktails, pasta, burgers, sandwiches, desserts, salad, random]")
		return
	print(recipe_category) 




bot.run('MzE5NzM5ODYxOTc4MzE2ODEw.DBFcug.6H82mGImZexQHyuujZyJKqI9TpQ')

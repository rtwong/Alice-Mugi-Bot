import discord
from discord.ext import commands
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlite3
import os


description = '''Alice Nakiri on duty!'''

bot = commands.Bot(command_prefix='?', description=description, pm_help=True)


recipe_categories = ["chicken", "pizza", "cocktails", "pasta", "burgers", "sandwiches", "desserts", "salad"]
recipe_urls = {
	"chicken"    : "http://www.seriouseats.com/tags/recipes/chicken",
	"pizza"      : "http://www.seriouseats.com/tags/recipes/pizza",
	"cocktails"  : "http://www.seriouseats.com/recipes/topics/meal/drinks/cocktails",
	"pasta"      : "http://www.seriouseats.com/tags/recipes/pasta",
	"burgers"    : "http://www.seriouseats.com/tags/recipes/burger",
	"sandwiches" : "http://www.seriouseats.com/sandwiches",
	"desserts"   : "http://www.seriouseats.com/desserts",
	"salad"      : "http://www.seriouseats.com/tags/recipes/salad"
}

alice_gifs = [
"https://s-media-cache-ak0.pinimg.com/originals/78/f5/8e/78f58e593a193d470add8983973ee8c4.gif",
"https://68.media.tumblr.com/de6d2ca14fc64f3b4bc73e3651bf5ab3/tumblr_nt5tg2WBcS1r60zuio1_500.gif",
"https://s-media-cache-ak0.pinimg.com/originals/de/83/2d/de832de0340706a16d1b64321850f95e.gif",
"http://pa1.narvii.com/5939/4d3eeb22212ff56d5e30b9b7596fa29d8dbad042_hq.gif",
"https://media.giphy.com/media/13ZoPdc5aFQM5q/giphy.gif",
"https://media.tenor.com/images/7735c516c3c0c5896f4c2cbd969c187e/tenor.gif",
"http://pa1.narvii.com/6163/74711fb8f84cb1b93e04ef6c9d27995a72dc93cd_hq.gif",
"http://pa1.narvii.com/6024/ee7acf9fccff51e7b8e05b9133e9ba9976053458_hq.gif",
"http://i.imgur.com/iyARgYd.gif",
"http://i.imgur.com/H0l6Mlb.gifv",
"http://i43.photobucket.com/albums/e374/NeoRyo/JapaneseAnime/Shokugeki%20no%20Soma/Shokugeki%20no%20Soma%20-%20Episode%2013%20-%20Nakiri%20Alice%20teaches%20Ryou%20how%20to%20intimidate%20people.gif"
]

# tuples are (opponent name, win chance, payout, win gif, lose gif, win quote, lose quote)
shokugeki_opponents = {
	'joichiro_yukihira' : ("Joichiro Yukihira", 1, 100.0,"http://pa1.narvii.com/6021/915dc3a471a6966bd466ec002b4f79606f40f76c_hq.gif", "https://68.media.tumblr.com/527b2586255523f4f9221f97dfa794f3/tumblr_nuvpy2QwW61siue1no1_500.gif", "Glad you liked it!", "Isn't this nasty?"),
	'alice_nakiri'      : ("Alice Nakiri", 10, 10.0, "http://68.media.tumblr.com/23ce70b3550a0301506c6e430b293600/tumblr_of78s8NjPf1v89ei5o1_500.gif", "https://media.tenor.com/images/f518febf0964959af19720ba1e759041/tenor.gif", "Winner!", "Wahhhh"),
	'soma_yukihira'     : ("Soma Yukihira", 33, 3.0,"http://pa1.narvii.com/5764/1d00f4332957996f6d21be3b8eaae0416a081501_hq.gif","https://media.giphy.com/media/dYegLwRzhiY2Q/giphy.gif", "Glad you liked it!", "Try THIS!"),
	'takumi_aldini'     : ("Takumi Aldini", 50, 2.0,"https://s-media-cache-ak0.pinimg.com/originals/96/a9/7c/96a97ce95e406147453bd77724445d14.gif","https://media.tenor.co/images/b116de827c21558bb2d4f67f85567f15/tenor.gif","ALDINIIIIIII", "I don't want to talk about it."),
	'megumi_tadokoro'   : ("Megumi Tadokoro", 66, 1.5,"https://68.media.tumblr.com/0d1a2186d7f99e3646d8676418fae8b8/tumblr_of75ht79nB1v89ei5o1_500.gif","https://s-media-cache-ak0.pinimg.com/originals/c5/d2/50/c5d25025fd2de0ae4cfa359b0a7927d8.gif", "Thanks!", "Oh god oh god oh god."),
	'kanichi_konishi'   : ("Kanichi Konishi", 90, 1.1, "https://68.media.tumblr.com/a1f57ba41ef084d3f4b64f18a380edbd/tumblr_nujeh76lqz1qj4q1zo1_500.gif", "https://cdn.discordapp.com/attachments/238032111125266432/321416685762510858/ezgif-3-b68ebfd882.gif", "I'M SO PROUD OF ME", "o")
}

member_points = {}
db_filename = "AliceBotPoints.sqlite"



async def point_counter():
	currently_online = set()
	members_list = bot.get_all_members()
	for member in members_list:
		if member.bot:
			continue
		if member.voice.voice_channel is not None and not member.voice.is_afk:
			currently_online.add(member)

	conn = sqlite3.connect(db_filename)
	c = conn.cursor()
	for member in currently_online:
		member_points[member.id] = member_points.get(member.id, 0) + 10
		c.execute("INSERT or REPLACE into points_table (id, points) VALUES (%s, %s)" % (member.id, member_points[member.id]))
	conn.commit()
	conn.close()


async def db_init():
	conn = sqlite3.connect(db_filename)
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS points_table (id INTEGER PRIMARY KEY, points INTEGER)')
	users = c.execute('SELECT id, points from points_table').fetchall()
	for user in users:
		member_points[str(user[0])] = user[1]
	conn.commit()
	conn.close()


@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	await bot.change_presence(game=discord.Game(name='?help for commands'))
	await db_init()

	while True:
		await point_counter()
		await asyncio.sleep(300)


@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	if "alice" in message.content.lower() :
		await bot.send_message(message.channel, "https://s-media-cache-ak0.pinimg.com/originals/0a/92/d7/0a92d7d7f15ba1e4e14449ec29271cb7.gif")
		await bot.send_message(message.channel, "Stop talking about me!")

	await bot.process_commands(message)


@bot.command()
async def gifme():
	"""Shows a random enjoyable gif. """
	await bot.say(random.choice(alice_gifs))


@bot.command()
async def recipe(request_category : str):
	"""Links a random recipe from SeriousEats. Recipe options are: chicken, pizza, cocktails, pasta, burgers, sandwiches, desserts, salad, or random
	"""
	request_category = request_category.lower()
	if request_category == "random":
		recipe_category = random.choice(recipe_categories)
	elif request_category in recipe_categories:
		recipe_category = request_category
	else:
		await bot.say("Incorrect category, choose one of [chicken, pizza, cocktails, pasta, burgers, sandwiches, desserts, salad, random]")
		return

	async with aiohttp.get(recipe_urls[recipe_category]) as resp:
		if resp.status == 200:
			webpage = await resp.text()
		else:
			bot.say("File not found")


	recipe_recommendations = []
	soup = BeautifulSoup(webpage, "html.parser")
	for link in soup.find_all('a', {"class" : "module__image-container module__link"}):
		recipe_link = link.get('href')
		if recipe_link != recipe_urls[recipe_category]:
			recipe_recommendations.append(recipe_link)
	await bot.say(random.choice(recipe_recommendations))


@bot.command(pass_context=True)
async def bentos(ctx):
	""" Shows how many Bentos you have! """
	sender_id = ctx.message.author.id
	if sender_id in member_points:
		await bot.say("You currently have " + str(member_points[sender_id]) + " Bentos.")
	else:
		await bot.say("You currently have no Bentos, get cooking!")


@bot.command(pass_context=True)
async def shokugeki(ctx, points_bet : int):
	""" Bento Gambling, random opponent, higher payout if given harder opponent"""
	betting_id = ctx.message.author.id
	member_points[betting_id] = member_points.get(betting_id,0)

	if points_bet < 10:
		await bot.say("You must stake 10 or more Bentos!")
		return
	if points_bet > member_points[betting_id]:
		await bot.say("You do not have that many Bentos!")
		return

	member_points[betting_id] = member_points[betting_id] - points_bet
	opponent = random.choice(list(shokugeki_opponents.items()))[1]
	roll = random.randrange(1,100)
	payout = int(points_bet*opponent[2])

	if roll <= opponent[1]:
		member_points[betting_id] = member_points[betting_id] + payout
		await bot.say("You beat %s, winning %d Bentos!" % (opponent[0], payout - points_bet) + "\n" + "You currently have %d Bentos." % member_points[betting_id] + "\n" + opponent[4])
		await bot.say(opponent[6])
	else:
		await bot.say("You lose to %s, winning %d Bentos!" % (opponent[0], points_bet) + "\n" + "You currently have %d Bentos." % member_points[betting_id] + "\n" + opponent[3])
		await bot.say(opponent[5])

	conn = sqlite3.connect(db_filename)
	c = conn.cursor()
	c.execute("INSERT or REPLACE into points_table (id, points) VALUES (%s, %s)" % (betting_id, member_points[betting_id]))
	conn.commit()
	conn.close()



bot.run('MzE5NzM5ODYxOTc4MzE2ODEw.DBFcug.6H82mGImZexQHyuujZyJKqI9TpQ')

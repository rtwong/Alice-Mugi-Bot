import discord
from discord.ext import commands
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlite3
import os
import youtube_dl
import secrets
import static
import cards
import re


description = '''Alice Nakiri on duty!'''
recipe_categories = static.recipe_categories
recipe_urls = static.recipe_urls
alice_gifs = static.alice_gifs
shokugeki_opponents = static.shokugeki_opponents
member_points = {}
db_filename = "AliceBotPoints.sqlite"
rep_points = 0

bot = commands.Bot(command_prefix='?', description=description, pm_help=True)
#bot.add_cog(Music(bot))

async def db_init():
    global rep_points
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS points_table (id INTEGER PRIMARY KEY, points INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS variables_table (variables STRING PRIMARY KEY, var_points INTEGER)')
    users = c.execute('SELECT id, points from points_table').fetchall()
    for user in users:
        member_points[str(user[0])] = user[1]
    variables = c.execute('SELECT variables, var_points from variables_table').fetchall()
    # currently only 1 variable, rep
    for variable in variables:
        rep_points = variable[1]
    conn.commit()
    conn.close()

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
    global rep_points
    if message.author == bot.user:
        return
    c = re.compile(r"\balice\b",re.I)
    if len(c.findall(message.content.lower())) > 0:
        await bot.send_message(message.channel, "https://s-media-cache-ak0.pinimg.com/originals/0a/92/d7/0a92d7d7f15ba1e4e14449ec29271cb7.gif")
        await bot.send_message(message.channel, "Stop talking about me!")

    if ("+rep" in message.content.lower()) and (message.channel.name == "repchannel"):
        rep_points = rep_points + 1
        conn = sqlite3.connect(db_filename)
        c = conn.cursor()
        c.execute("INSERT or REPLACE into variables_table (variables, var_points) VALUES ('rep', %s)" % (str(rep_points)))
        conn.commit()
        conn.close()
        await bot.send_message(message.channel, "+rep! We have " + str(rep_points) + " rep!")

    if ("-rep" in message.content.lower()) and (message.channel.name == "repchannel"):
        rep_points = rep_points - 1
        conn = sqlite3.connect(db_filename)
        c = conn.cursor()
        c.execute("INSERT or REPLACE into variables_table (variables, var_points) VALUES ('rep', %s)" % (str(rep_points)))
        conn.commit()
        conn.close()
        await bot.send_message(message.channel, "-rep! We have " + str(rep_points) + " rep!")

    #if "feeling" in message.content.lower():
        #await bot.send_message(message.channel, "http://68.media.tumblr.com/7ecff5cbddd9ea983d0aae3a1a266f9b/tumblr_ofztu8uWSJ1u0bi6jo1_r1_500.gif")
    #Dan if you're reading this you suck

    await bot.process_commands(message)

@bot.command()
async def rep():
    """ +1 to rep"""
    await bot.say("We have " + str(rep_points) + " rep!")

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
        await bot.say("You lose to %s, losing %d Bentos!" % (opponent[0], points_bet) + "\n" + "You currently have %d Bentos." % member_points[betting_id] + "\n" + opponent[3])
        await bot.say(opponent[5])

    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute("INSERT or REPLACE into points_table (id, points) VALUES (%s, %s)" % (betting_id, member_points[betting_id]))
    conn.commit()
    conn.close()

@bot.command(pass_context=True)
async def addition(ctx):
    """test"""
    summ = 0
    flag = True
    while flag:
        msg = await bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
        if msg.content.lower() == "end":
            flag = False
        try:
            num = int(msg.content)
            summ = summ + num
        except:
            print("blarg")

    await bot.say(summ)

@bot.command(pass_context=True)
async def blackjack(ctx, points_bet : int):
    """Bento gambling in a game of Blackjack against Alice, 1.5x when winning with Blackjack, dealer must stand on a soft 17."""

    betting_id = ctx.message.author.id
    member_points[betting_id] = member_points.get(betting_id,0)

    if points_bet < 500:
        await bot.say("You must stake 500 or more Bentos!")
        return
    if points_bet > member_points[betting_id]:
        await bot.say("You do not have that many Bentos!")
        return

    #member_points[betting_id] = member_points[betting_id] - points_bet

    deck = cards.Deck(2)

    shown_card = deck.draw()
    hole_card = deck.draw()
    dealer_hand = [hole_card, shown_card]

    player_hand = []
    player_hand.append(deck.draw())
    player_hand.append(deck.draw())

    player_playing = True
    if check_blackjack(player_hand):
        # already hit blackjack, don't need to play
        player_playing = False
        await bot.say("Alice's Cards :     :grey_question::question:     " + emotify_card(shown_card) + "\n"
                    + "Your Cards    :" + emotify_hand(player_hand) +"\n"
                    + "Blackjack, my turn!")

    while player_playing:
        await bot.say("Alice's Cards :     :grey_question::question:     " + emotify_card(shown_card) + "\n"
                    + "Your Cards    :" + emotify_hand(player_hand) +"\n"
                    + "Hit or Stand?")

        msg = await bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
        if (msg.content.lower() != "hit") and (msg.content.lower() != "stand"):
            await bot.say("Please type 'Hit' or 'Stand' to make your move.")
            continue
        elif msg.content.lower() == "stand":
            player_playing = False
            await bot.say("Alrighty, my turn")
        else:
            new_card = deck.draw()
            player_hand.append(new_card)
            if check_blackjack(player_hand):
                await bot.say("Alice's Cards :     :grey_question::question:     " + emotify_card(shown_card) + "\n"
                            + "Your Cards    :" + emotify_hand(player_hand) +"\n"
                            + "Blackjack, my turn!")
                break
            elif check_hand(player_hand) > 21:
                await bot.say("Alice's Cards :     :grey_question::question:     " + emotify_card(shown_card) + "\n"
                            + "Your Cards    :" + emotify_hand(player_hand) +"\n"
                            + "Bust, loser!")
                member_points[betting_id] = member_points[betting_id] - points_bet
                await bot.say("You lose %d Bentos!" % (points_bet) + "\n" + "You currently have %d Bentos." % member_points[betting_id])
                conn = sqlite3.connect(db_filename)
                c = conn.cursor()
                c.execute("INSERT or REPLACE into points_table (id, points) VALUES (%s, %s)" % (betting_id, member_points[betting_id]))
                conn.commit()
                conn.close()
                return

    await asyncio.sleep(3)
    await bot.say("Alice's Cards :" + emotify_hand(dealer_hand) + "\n"
                + "Your Cards    :" + emotify_hand(player_hand) +"\n")

    while check_hand(dealer_hand) < 17:
        new_card = deck.draw() 
        dealer_hand.append(new_card)
        await bot.say("Alice's Cards :" + emotify_hand(dealer_hand) + "\n"
                    + "Your Cards    :" + emotify_hand(player_hand) +"\n")
        await asyncio.sleep(3)

    if (check_hand(dealer_hand) > 21) or (check_hand(dealer_hand) < check_hand(player_hand)):
        if check_hand(player_hand) == 21:
            member_points[betting_id] = member_points[betting_id] + int(points_bet*1.5)
            await bot.say("1.5x for having Blackjack!" + "\n"
                         +"You win %d Bentos!" % (int(points_bet*1.5)) + "\n"
                         +"You currently have %d Bentos." % member_points[betting_id])
        else:
            member_points[betting_id] = member_points[betting_id] + points_bet
            await bot.say("Ugh, you win." + "\n"
                         +"You win %d Bentos!" % (points_bet) + "\n"
                         +"You currently have %d Bentos." % member_points[betting_id])
    elif check_hand(dealer_hand) == check_hand(player_hand):
        # tie
        await bot.say("Guess no one wins this round!" + "\n" + "You currently have %d Bentos." % member_points[betting_id])
    elif check_hand(dealer_hand) > check_hand(player_hand):
        # player loss, loses initial bet
        member_points[betting_id] = member_points[betting_id] - points_bet
        await bot.say("Hahaha, you're a loser!" + "\n"
                     +"You lose %d Bentos!" % (points_bet) + "\n" + "You currently have %d Bentos." % member_points[betting_id])

    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute("INSERT or REPLACE into points_table (id, points) VALUES (%s, %s)" % (betting_id, member_points[betting_id]))
    conn.commit()
    conn.close()

def check_blackjack(hand):
    return check_hand(hand) == 21

def check_hand(hand):
    # returns value of the hand, accounting for Aces being 11 if possible, and 1 otherwise
    hand_value = 0
    aces = 0
    for card in hand:
        if card.value == "Ace":
            aces += 1
        else:
            if card.value in ["Jack", "Queen", "King"]:
                hand_value += 10
            else:
                hand_value += int(card.value)
    for i in range(aces):
        if hand_value+11 <= 21:
            hand_value += 11
        else:
            hand_value += 1
    return hand_value

def emotify_card(card):
    output_dict = {"Ace"      :":regional_indicator_a:",
                   "King"     :":regional_indicator_k:",
                   "Queen"    :":regional_indicator_q:",
                   "Jack"     :":regional_indicator_j:",
                   "10"       :":one::zero:",
                   "9"        :":nine:",
                   "8"        :":eight:",
                   "7"        :":seven:",
                   "6"        :":six:",
                   "5"        :":five:",
                   "4"        :":four:",
                   "3"        :":three:",
                   "2"        :":two:",
                   "Diamonds" :":diamonds:",
                   "Clubs"    :":clubs:",
                   "Hearts"   :":hearts:",
                   "Spades"   :":spades:"}
    return output_dict[card.value] + output_dict[card.suit]

def emotify_hand(hand):
    return_string = ""
    for card in hand:
        return_string = return_string + "     " + emotify_card(card)
    return return_string

bot.run(secrets.alice_token)

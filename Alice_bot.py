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


description = '''Alice Nakiri on duty!'''
recipe_categories = static.recipe_categories
recipe_urls = static.recipe_urls
alice_gifs = static.alice_gifs
shokugeki_opponents = static.shokugeki_opponents
member_points = {}
db_filename = "AliceBotPoints.sqlite"
rep_points = 0



if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Music:
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song.
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))






bot = commands.Bot(command_prefix='?', description=description, pm_help=True)
bot.add_cog(Music(bot))

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
    if "alice" in message.content.lower():
        await bot.send_message(message.channel, "https://s-media-cache-ak0.pinimg.com/originals/0a/92/d7/0a92d7d7f15ba1e4e14449ec29271cb7.gif")
        await bot.send_message(message.channel, "Stop talking about me!")

    if "+rep" in message.content.lower():
        rep_points = rep_points + 1
        conn = sqlite3.connect(db_filename)
        c = conn.cursor()
        c.execute("INSERT or REPLACE into variables_table (variables, var_points) VALUES ('rep', %s)" % (str(rep_points)))
        conn.commit()
        conn.close()
        await bot.send_message(message.channel, "+rep! We have " + str(rep_points) + " rep!")

    if "-rep" in message.content.lower():
        rep_points = rep_points - 1
        conn = sqlite3.connect(db_filename)
        c = conn.cursor()
        c.execute("INSERT or REPLACE into variables_table (variables, var_points) VALUES ('rep', %s)" % (str(rep_points)))
        conn.commit()
        conn.close()
        await bot.send_message(message.channel, "-rep! We have " + str(rep_points) + " rep!")



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



bot.run(secrets.alice_token)

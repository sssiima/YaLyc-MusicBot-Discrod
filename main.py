import discord
from discord.ext import commands
import logging
import datetime
import requests
import random
from sqlalchemy.orm import Session
from data.names import Names
from data.history import History
from sqlalchemy import create_engine
from youtube_dl import YoutubeDL
import aiohttp
import io
import vk_api
from discord.ui import Button, View


YDL_OPTIONS = {'format': 'worstaudio/best', 'noplaylist': 'False', 'simulate': 'True', 'key': 'FFmpegExtractAudio'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 - reconnect_streamed 1 - reconnect_delay_max 5', 'options': '-vn'}

db_sess = create_engine("sqlite:///db/music.db")

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

TOKEN = "BOTTOKEN"
VK_TOKEN = 'VKTOKEN'

bot = commands.Bot(command_prefix='!#', intents=intents)

global tracks, current_track
tracks = []

dashes = ['\u2680', '\u2681', '\u2682', '\u2683', '\u2684', '\u2685']


@bot.event
async def on_ready():
    ch = await bot.fetch_channel("1093543144060096543")
    await ch.send(content="""Hello, I'm a music bot YaLCat. I download music from SoundCloud and play it.
But not only this :)
For example, I can send you YouTube videos and some info from VK.
To know what I also do, type command !#helpme""")


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Nice to meet you, {member.name}!'
    )


@bot.command(name='set_timer')
async def set_timer(ctx, hours, minutes):
    async def button_callback(interaction):
        await interaction.response.edit_message(content='Understood. Send me the name of the track', view=None)
        ans = await bot.wait_for('message', check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
        name = ans.content
        for elem in tracks:
            if name.lower() in elem[1].lower():
                with Session(db_sess) as session:
                    result = session.query(Names).filter_by(link=elem[0]).first()
        if not result:
            await ctx.send(f"Track wasn't found, but the timer is set on {hours} hours and {minutes} minutes.")
        else:
            await ctx.send(f'the timer is set on {hours} hours and {minutes} minutes.')
        now = datetime.datetime.now()
        new_time = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
        print(new_time)
        while datetime.datetime.now() != new_time:
            pass
        if not result:
            pass
        else:
            await ctx.send(result.link)
        await ctx.send(f'\u23f0 Time X has come!')

    async def button_call(interaction):
        await interaction.response.edit_message(content='Okay, no music', view=None)
        await ctx.send(f'the timer is set on {hours} hours and {minutes} minutes.')
        now = datetime.datetime.now()
        new_time = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
        print(new_time)
        while datetime.datetime.now() != new_time:
            pass
        await ctx.send(f'\u23f0 Time X has come!')

    button1 = Button(custom_id='button1', label='Yes!', style=discord.ButtonStyle.red)
    button2 = Button(custom_id='button2', label='No', style=discord.ButtonStyle.grey)
    button1.callback = button_callback
    button2.callback = button_call
    view = View()
    view.add_item(item=button1)
    view.add_item(item=button2)
    await ctx.send('Do you want to choose a ringtone?', view=view)


@bot.command(name='add_track')
async def add_track(ctx, *name):
    url = "https://soundcloud-scraper.p.rapidapi.com/v1/search/tracks"
    name = ' '.join(name)
    querystring = {"term": name}
    headers = {
        "X-RapidAPI-Key": "API",
        "X-RapidAPI-Host": "soundcloud-scraper.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring).json()
    link = response["tracks"]["items"][0]["permalink"]
    title = response["tracks"]["items"][0]["title"]
    id = response["tracks"]["items"][0]["id"]
    for elem in tracks:
        if id == elem[2]:
            await ctx.send(content="This track is already in your album")
    else:
        tracks.append((link, title, id))
        with Session(db_sess) as session:
            session.add(Names(track_name=f'{title}', link=f'{link}'))
            session.add(History(user_name=f'{ctx.message.author}', link=f'{link}'))
            session.commit()
        await ctx.send(content=f'Track {title} was added')


@bot.command(name='play_track')
async def play_track(ctx, name):
    voice_channel = ctx.message.author.voice.channel
    for elem in tracks:
        if name.lower() in elem[1].lower():
            with Session(db_sess) as session:
                result = session.query(Names).filter_by(link=elem[0]).first()
                await ctx.send(result.link)


@bot.command(name='track_list')
async def track_list(ctx, *args):
    if args:
        flag = False
        for elem in tracks:
            if ' '.join(args).lower() in elem[1].lower():
                await ctx.send(f'{elem[1]}')
                flag = True
        if not flag:
            await ctx.send("I can't find any tracks by your request")
    else:
        emb = discord.Embed(title="Your playlist", color=random.randint(1, 16777216))
        for elem in tracks:
            emb.add_field(name=f"{elem[1]}", value='', inline=False)
        await ctx.send(embed=emb)


@bot.command(name='random_play')
async def random_play(ctx):
    num = random.randint(0, len(tracks) - 1)
    voice_channel = ctx.message.author.voice.channel
    await ctx.send(f'{tracks[num][0]}')


@bot.command(name='delete_track')
async def delete_track(ctx, name):
    flag = False
    for elem in tracks:
        if name.lower() in elem[1].lower():
            tracks.remove(elem)
            with Session(db_sess) as session:
                result = session.query(Names).filter_by(link=elem[0]).first()
                session.delete(result)
                session.commit()
            flag = True
            await ctx.send(f'Track {elem[1]} is removed')
    if not flag:
        await ctx.send(f'No tracks to delete found')


@bot.command(name='play_video')
async def play_video(ctx, *args):
    if not args:
        await ctx.send(f'No parameters, try again')
    else:
        args = ''.join(args)
        vc = await ctx.message.author.voice.channel.connect()

        with YoutubeDL(YDL_OPTIONS) as ydl:
            if 'https://' in args:
                info = ydl.extract_info(args, download=False)
            else:
                info = ydl.extract_info(f'ytsearch:{args}', download=False)['entries'][0]
        link = info['formats'][0]['url']

        vc.play(discord.FFmpegPCMAudio(executable='ffmpeg\\ffmpeg.exe', source=link, **FFMPEG_OPTIONS))


@bot.command(name='cat')
async def cat(ctx):
    response = requests.get('https://api.thecatapi.com/v1/images/search').json()
    link = response[0]['url']
    await ctx.send(link)


@bot.command(name='dog')
async def dog(ctx):
    response = requests.get('https://dog.ceo/api/breeds/image/random').json()
    link = response['message']
    await ctx.send(link)


@bot.command(name='to_file')
async def to_file(ctx, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img = await resp.read()
            with io.BytesIO(img) as file:
                await ctx.send(file=discord.File(file, f"{url[10:25]}.png"))


@bot.command(name='game')
async def game(ctx):
    await ctx.send("""Game starts!
To stop type 'stop'""")
    flag = True
    while flag:
        ans = await bot.wait_for('message', check = lambda m: m.channel == ctx.channel and m.author == ctx.author)
        if ans.content.lower() == 'stop':
            await ctx.send('Game is over')
            flag = False
            break
        await ctx.send(f'{ans.content}')


@bot.command(name='roll_dice')
async def roll_dice(ctx, count):
    for i in range(int(count)):
        dash = random.choice(dashes)
        await ctx.send(dash)


@bot.command(name='get_album')
async def get_album(ctx, num, user_id):
    token = VK_TOKEN
    tok = vk_api.VkApi(token=token)
    vkapi = tok.get_api()
#    my_id = '497351082'
    try:
        photos = vkapi.photos.getUserPhotos(user_id=user_id, count=num)
        await ctx.send("Sending photos...")
        for elem in photos['items']:
            url = elem['sizes'][0]['url']
            await ctx.send(f"{url}")
    except:
        await ctx.send(f"User {user_id} has denied access to his photos")


@bot.command(name='get_groups')
async def get_posts(ctx, user_id):
    token = VK_TOKEN
    tok = vk_api.VkApi(token=token)
    vkapi = tok.get_api()
#    my_id = '497351082'
    try:
        groups = vkapi.groups.get(user_id=user_id)
        await ctx.send("Searching groups...")
        number = groups['count']
        await ctx.send(f"User {user_id} is in {number} groups")
    except:
        await ctx.send(f"User {user_id} has denied access to his groups")


@bot.command(name='get_friends')
async def get_friends(ctx, user_id):
    token = VK_TOKEN
    tok = vk_api.VkApi(token=token)
    vkapi = tok.get_api()
#    my_id = '497351082'
    try:
        friends = vkapi.friends.get(user_id=user_id)
        await ctx.send("Searching groups...")
        number = friends['count']
        await ctx.send(f"User {user_id} has {number} friends")
    except:
        await ctx.send(f"User {user_id} has denied access to his friends")


@bot.command(name='get_info')
async def get_album(ctx):
    token = VK_TOKEN
    tok = vk_api.VkApi(token=token)
    vkapi = tok.get_api()
#    my_id = '497351082'
    try:
        info = vkapi.account.getProfileInfo()
        await ctx.send("Searching info...")
        print(info)
        emb = discord.Embed(title="Your VK info", color=random.randint(1, 16777216))
        status = info['status']
        first_name = info['first_name']
        last_name = info['last_name']
        bdate = info['bdate']
        photo = info['photo_200']
        emb.add_field(name=f"status : ", value=status, inline=False)
        emb.add_field(name=f"first_name : ", value=first_name, inline=False)
        emb.add_field(name=f"last_name : ", value=last_name, inline=False)
        emb.add_field(name=f"bdate : ", value=bdate, inline=False)
        emb.add_field(name=f"photo : ", value='', inline=False)
        await ctx.send(embed=emb)
        await ctx.send(f'{photo}')
    except:
        await ctx.send("You have denied access to account")


@bot.command(name='get_videos')
async def get_videos(ctx, num, user_id):
    token = VK_TOKEN
    tok = vk_api.VkApi(token=token)
    vkapi = tok.get_api()
#    my_id = '497351082'
    try:
        videos = vkapi.video.get(owner_id=user_id, count=num)
        await ctx.send("Searching playlists...")
        for elem in videos['items']:
            player = elem['player']
            title = elem['title']
            await ctx.send(f'{title}')
            await ctx.send(f'{player}')
    except:
        await ctx.send(f"User {user_id} has denied access to his videos")


@bot.command(name='helpme')
async def helpme(ctx):
    emb = discord.Embed(title="Info about commands", color=random.randint(1, 16777216))
    emb.add_field(name=f"`helpme` : ", value="Opens this menu", inline=False)
    emb.add_field(name=f"`set_timer(h, m)` : ", value="Sets timer on h hours and m minutes. You may choose a ringtone",
                  inline=False)
    emb.add_field(name=f"`add_track(name)` : ", value="Adds the track to the album by its name",
                  inline=False)
    emb.add_field(name=f"`play_track(name)` : ", value="Plays the track from your album by its name",
                  inline=False)
    emb.add_field(name=f"`random_play` : ", value="Plays a random track from your album",
                  inline=False)
    emb.add_field(name=f"`delete_track(name)` : ", value="Deletes track from your album by the name",
                  inline=False)
    emb.add_field(name=f"`track_list(*author)` : ", value="Prints your album (*current author's tracks)",
                  inline=False)
    emb.add_field(name=f"`play_video(url)` : ", value="Plays video from YouTube by url",
                  inline=False)
    emb.add_field(name=f"cat  : ", value="Sends a random cat pic", inline=False)
    emb.add_field(name=f"dog  : ", value="Sends a random dog pic", inline=False)
    emb.add_field(name=f"to_file(url)  : ", value="Converts a link on the pic to a png-file",
                  inline=False)
    emb.add_field(name=f"game  : ", value="Starts repeating your messages", inline=False)
    emb.add_field(name=f"roll_dice(count)  : ", value="Imitates dice rolling for count times",
                  inline=False)
    emb.add_field(name=f"get_album(num, user_id)  : ", value="Sends num photos from VK where user_id is tagged",
                  inline=False)
    emb.add_field(name=f"get_videos(num, user_id)  : ", value="Sends num links on videos from user_id's videos",
                  inline=False)
    emb.add_field(name=f"get_friends(user_id)  : ", value="Sends number of the user_id's friends",
                  inline=False)
    emb.add_field(name=f"get_groups(user_id)  : ", value="Sends number of groups of the user_id",
                  inline=False)
    emb.add_field(name=f"get_info()  : ", value="Sends your account information",
                  inline=False)
    await ctx.send(embed=emb)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            embed=discord.Embed(description=f"** {ctx.author.name}, this command doesn't exist.**", color=0x8c0c0c))


bot.run(TOKEN)

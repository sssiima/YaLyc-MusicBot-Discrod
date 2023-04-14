import discord
import logging
from discord.ext import commands
import random, logging
import datetime
import sqlite3

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

TOKEN = "BOT_TOKEN"
bot = commands.Bot(command_prefix='!#', intents=intents)

global con
con = sqlite3.connect('music-for-bot.db')
global cur
cur = con.cursor()


@bot.event
async def on_ready():
    ch = await bot.fetch_channel("1093543144060096543")
    await ch.send(content="Hello, I'm a music bot YaLCat. To know what I can do, type command !#helpme")


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Nice to meet you, {member.name}!'
    )


@bot.command(name='set_timer')
async def set_timer(ctx, hours, minutes):
    #добавить выбор рингтона
    await ctx.send(f'the timer is set on {hours} hours and {minutes} minutes.')
    now = datetime.datetime.now()
    new_time = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
    print(new_time)
    while datetime.datetime.now() != new_time:
        pass
    await ctx.send(f'\u23f0 Time X has come!')


@bot.command(name='add_track')
async def add_track(ctx):
    await ctx.send('track is added')


@bot.command(name='play')
async def play(ctx):
    await ctx.send('track is playing')


@bot.command(name='next')
async def next(ctx):
    await ctx.send('next track is playing')


@bot.command(name='stop')
async def stop(ctx):
    await ctx.send('track is stopped')


@bot.command(name='resume')
async def resume(ctx):
    await ctx.send('track is resumed')


@bot.command(name='delete_track')
async def delete_track(ctx):
    await ctx.send('track is deleted')


@bot.command(name='track_list')
async def add_track(ctx, *args): #все или если аргс то по исполнителю
    await ctx.send('track list')


@bot.command(name='random_play')
async def random_play(ctx):
    await ctx.send('random playing')


@bot.command(name='helpme')
async def helpme(ctx):
    emb = discord.Embed(title="Info about commands", color=random.randint(1, 16777216))
    emb.add_field(name=f"`helpme` : ", value="Opens this menu", inline=False)
    emb.add_field(name=f"`set_timer(h, m)` : ", value="Starts a timer on h hours and m minutes", inline=False)
    emb.add_field(name=f"`add_track(link)` : ", value="Adds the track to the album by the link", inline=False)
    emb.add_field(name=f"`play(name)` : ", value="Plays the track from your album by its name", inline=False)
    emb.add_field(name=f"`random_play` : ", value="Plays tracks from your album in random order", inline=False)
    emb.add_field(name=f"`next` : ", value="Plays next random track", inline=False)
    emb.add_field(name=f"`stop` : ", value="Stops playing music", inline=False)
    emb.add_field(name=f"`resume` : ", value="Resumes playing music from the stop point", inline=False)
    emb.add_field(name=f"`delete_track(name)` : ", value="Deletes track from your album by the name", inline=False)
    emb.add_field(name=f"`track_list(*author)` : ", value="Prints your album (*current author's tracks)", inline=False)
    message = await ctx.send(embed=emb)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            embed=discord.Embed(description=f"** {ctx.author.name}, this command doesn't exist.**", color=0x0c0c0c))


bot.run(TOKEN)
# альбом - это бд с номером-названием-исполнителем-ссылкой на трек
# добавить музыку. на таймер!! выбор рингтона из бд с музыкой из альбома
# команды: добавить в альбом, воспроизвести, переключить на следующую, остановить, запустить, ускорить (?),
# удалить из альбома, вывести все треки исполнителя в альбоме

#import random
import asyncio
#import aiohttp
import json

import re

import discord
from discord import Game
#from discord.ext.commands import Bot

import os
is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    data = {
        'TOKEN': os.environ.get('DISCORD_TOKEN', None)
    }
else:
    with open('settings.json') as f:
        data = json.loads(f.read())


DATABASE = {}

BOT_PREFIX = ('.')
TOKEN = data['TOKEN']  # Get at discordapp.com/developers/applications/me

client = discord.Client()

async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

@client.event
async def on_ready():
    await client.change_presence(game=Game(name="with humans"))
    print("Logged in as " + client.user.name)

def add_results(server_id, results):
    if server_id in DATABASE:
        db = DATABASE[server_id]
    else:
        DATABASE[server_id] = {}

    db = DATABASE[server_id]
    
    for r in results:
        if r in db:
            db[r] = db[r] + 1
        else:
            db[r] = 1

    print(db)

def get_top(server_id):
    if server_id in DATABASE:
        db = DATABASE[server_id]
        newA = {key: db[key] for key in sorted(db, key=db.get, reverse=True)[:5]}
        return newA

def get_count(server_id, emote):
    if server_id in DATABASE:
        db = DATABASE[server_id]
        if emote in db:
            return db[emote]

# @client.command()
# async def top():
#     print(client.server_id)
#     top_emotes = get_top(client.server_id)
#     string = ''
#     for key, value in top_emotes:
#         string = string + key + ' [' + value + '] ;; '
#     await client.say(string)
    


@client.event
async def on_message(message):
    regex = re.compile(r':[A-Za-z0-9]+:')
    result = regex.findall(message.content)
    result = [r.replace(':', '') for r in result]
    add_results(message.server.id, result)

    if message.author == client.user:
        return

    if message.content.startswith('.'):
        spl = message.content[1:].split(' ', 1)
        cmd = spl[0]
        content = None
        if len(spl) > 1:
            content = spl[1]

        if cmd == 'top':
            top_emotes = get_top(message.server.id)
            print(top_emotes)
            #string = ''
            em = discord.Embed(title='Top 5 most used Emotes'.upper(), color=0x50bdfe)
            for key, value in top_emotes.items():
                #string = string + str(key) + ' [' + str(value) + '] ;; '
                em.add_field(name=str(key), value=value, inline=False)
                #em.add_field(name='', value='', inline=False)
            await client.send_message(message.channel, embed=em)

        if cmd == 'count':
            if len(result) == 1:
                cnt = get_count(message.server.id, result[0])
                string = ":" + result[0] + ": was used `" + str(cnt) + "` times."
                await client.send_message(message.channel, string)


client.loop.create_task(list_servers())
client.run(TOKEN)
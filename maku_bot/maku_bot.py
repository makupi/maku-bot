import asyncio
import json

import re

import discord
from discord import Game
from discord.ext.commands import Bot


import os
is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    data = {
        'TOKEN': os.environ.get('DISCORD_TOKEN', None),
        'MONGODB': os.environ.get('MONGODB', None)
    }
else:
    with open('settings.json') as f:
        data = json.loads(f.read())


from pymongo import MongoClient
mdb_client = MongoClient(data['MONGODB'])
db = mdb_client.servers


#DATABASE = {}

BOT_PREFIX = ('.')
TOKEN = data['TOKEN']  # Get at discordapp.com/developers/applications/me

client = Bot(command_prefix=BOT_PREFIX)


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
    server = db[server_id]
    for result in results:
        server.update({'emote': result}, {'$inc': {'count': 1}}, True)


def get_top(server_id):
    server = db[server_id]
    top = server.aggregate([{'$sort': {'count': -1}}, {'$limit': 5}])
    string = dict()
    for doc in top:
        string.update({doc['emote']: doc['count']})

    return string


def get_count(server_id, emote):
    server = db[server_id]
    val = server.find_one({'emote': emote})
    if val:
        return val['count']
    else: 
        return None

@client.command(name='toc',
                description='Converts temperature from F to C',
                brief=': Converts F to C')
async def to_c(number :int):
    content = int(number)
    ce = (((content - 32) * 5) / 9)
    string = str(content) + "F is equal to " + str(round(ce, 2)) + "C."
    await client.say(string)

@client.command(name='tof',
                description='Converts temperature from C to F',
                brief=': Converts C to F')
async def to_f(number :int):
    content = int(number)
    fh = (((content * 9) / 5) + 32)
    string = str(content) + "C is equal to " + str(round(fh, 2)) + "F."
    await client.say(string)


@client.command(name='top',
                description='Lists the top 5 used emotes.',
                brief=': List top used emotes.',
                pass_context=True)
async def top(context):
    top_emotes = get_top(context.message.server.id)
    if top_emotes is None:
        # figure something out
        return
    string = "```"
    string += "Top 5 most used Emotes: \n\n"
    # em = discord.Embed(
    #     title='Top 5 most used Emotes'.upper(), color=0x50bdfe)
    for key, value in top_emotes.items():
        #string = string + str(key) + ' [' + str(value) + '] ;; '
        string += ":"+str(key) + ": \n\t" + str(value) + "\n"
        #em.add_field(name='', value='', inline=False)
    string += "```"
    await client.say(string)


@client.event
async def on_message(message):
    regex = re.compile(r':[A-Za-z0-9]+:')
    result = regex.findall(message.content)
    result = [r.replace(':', '') for r in result]
    add_results(message.server.id, result)

    await client.process_commands(message)
    return

    if message.author == client.user:
        return

    if message.content.startswith('.'):
        spl = message.content[1:].split(' ', 1)
        cmd = spl[0].lower()
        content = None
        if len(spl) > 1:
            content = spl[1]

        if cmd == 'top':
            top_emotes = get_top(message.server.id)
            if top_emotes is None:
                # figure something out
                return
            #string = ''
            em = discord.Embed(
                title='Top 5 most used Emotes'.upper(), color=0x50bdfe)
            for key, value in top_emotes.items():
                #string = string + str(key) + ' [' + str(value) + '] ;; '
                em.add_field(name=str(key), value=value, inline=False)
                #em.add_field(name='', value='', inline=False)
            await client.send_message(message.channel, embed=em)

        if cmd == 'count':
            if len(result) == 1:
                cnt = get_count(message.server.id, result[0])
                string = ":" + result[0] + \
                    ": was used `" + str(cnt) + "` times."
                await client.send_message(message.channel, string)

        if cmd == 'toc':
            if content:
                content = int(content)
                ce = (((content - 32) * 5) / 9)
                string = str(content) + "F is equal to " + str(round(ce, 2)) + "C."
                await client.send_message(message.channel, string)
                
        if cmd == 'tof':
            if content:
                content = int(content)
                fh = (((content * 9) / 5) + 32)
                string = str(content) + "C is equal to " + str(round(fh, 2)) + "F."
                await client.send_message(message.channel, string)


client.loop.create_task(list_servers())
client.run(TOKEN)

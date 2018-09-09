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
    await client.change_presence(game=Game(name=".help | with maku <3"))
    print("Logged in as " + client.user.name)


def add_results(server_id, results):
    server = db[server_id]
    for result in results:
        server.update({'emote': result}, {'$inc': {'count': 1}}, True)


def get_top(server_id, num, emote=None):
    server = db[server_id]
    if emote:
        rgx = '.*'+emote+'.*'
        top = server.aggregate([{'$match': {'emote': {'$regex': rgx}}}, {'$sort': {'count': -1}}, {'$limit': num}])
    else:
        top = server.aggregate([{'$sort': {'count': -1}}, {'$limit': num}])
    string = dict()
    for doc in top:
        string.update({doc['emote']: doc['count']})
    if string:    
        return string
    return None


def get_count(server_id, emote):
    server = db[server_id]
    val = server.find_one({'emote': emote})
    if val:
        return val['count']
    else: 
        return None

@client.command(name='toc',
                aliases=['toC'],
                description='Converts temperature from F to C',
                brief=': Converts F to C')
async def to_c(number :int):
    content = int(number)
    ce = (((content - 32) * 5) / 9)
    string = str(content) + "F is equal to " + str(round(ce, 2)) + "C."
    await client.say(string)

@client.command(name='tof',
                aliases=['toF'],
                description='Converts temperature from C to F',
                brief=': Converts C to F')
async def to_f(number :int):
    content = int(number)
    fh = (((content * 9) / 5) + 32)
    string = str(content) + "C is equal to " + str(round(fh, 2)) + "F."
    await client.say(string)


@client.command(name='top',
                description='Lists the top N used emotes.\nOptional <str> and <count> parameter.\n\t<count> = N\n\t<str> = filter emotes\nCan use both together.',
                brief=': List top used emotes.',
                pass_context=True)
async def top(context):
    spl = context.message.content.split(' ')
    num = 5
    emote = None
    if len(spl) > 2:  # .top <count> <str>
        try:
            num = int(spl[1])
        except ValueError:
            pass
        emote = spl[2]
    elif len(spl) == 2: #either <str> or <count>
        try:
            num = int(spl[1])
        except ValueError:
            emote = spl[1]

    top_emotes = get_top(context.message.server.id, num, emote)
    if top_emotes is None:
        # figure something out
        return
    index = 1
    mes = ""
    mes += "\n\t**Top " + str(num) + " most used Emotes**"
    if emote:
        mes += " **with** \t *" + emote + "* "
    mes += " \n```"
    for key, value in top_emotes.items():
        mes += '#{:02d}\tCount: {: <5d}\t{}'.format(index, value, ':'+str(key)+':')
        mes += '\n'
        index += 1
    mes += "```"
    #await client.say(string)
    await client.say(mes)

@client.command(name='count',
                description='List the count of specified emote.',
                brief=': List the count of specified emote.',
                pass_context=True)
async def count(context):
    regex = re.compile(r':[A-Za-z0-9]+:')
    result = regex.findall(context.message.content)
    result = [r.replace(':', '') for r in result]
    cnt = get_count(context.message.server.id, result[0])
    string = ":" + result[0] + \
        ": was used `" + str(cnt) + "` times."
    await client.say(string)

@client.event
async def on_message(message):
    if message.author != client.user:
        regex = re.compile(r':[A-Za-z0-9]+:')
        result = regex.findall(message.content)
        result = [r.replace(':', '') for r in result]
        add_results(message.server.id, result)

    if client.user.mentioned_in(message) and message.mention_everyone is False:
        # special reply to me
        if message.author.id == '309232625892065282':
            if any(c in message.content for c in ('ily', 'i love you')):
                await client.send_message(message.channel, 'i love you too ' + message.author.mention + ' ♥')
            else:
                await client.send_message(message.channel, 'i love you ' + message.author.mention + ' ♥')
    
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

startup_extensions = ["movienight"]
for extension in startup_extensions:
    try:
        client.load_extension("cogs."+extension)
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension {}\n{}'.format(extension, exc))

client.loop.create_task(list_servers())
client.run(TOKEN)

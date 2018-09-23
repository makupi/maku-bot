import discord
from discord.ext import commands
import time
import re
import numpy as np
#import threading
import datetime
import asyncio

from influxdb import InfluxDBClient
import os

infdb = {
    'USER': os.environ.get('INFLUX_USER', None),
    'KEY': os.environ.get('INFLUX_KEY', None),
    'URL': os.environ.get('INFLUX_URL', None),
    'PORT': int(os.environ.get('INFLUX_PORT', None))
}
try:
    inf_client = InfluxDBClient(infdb['URL'], infdb['PORT'], infdb['USER'], infdb['KEY'], 'message_stats')
except:
    inf_client = None
#inf_client.create_database('message_stats')

class ServerStats:
    def __init__(self, server_id):
        self.server_id = server_id
        self.last_hour = list()
        self.data = dict()

    def update(self, channel_id, content):
        regex = re.compile(r":[A-Za-z0-9]+:")
        result = regex.findall(content)
        words = content.split()
        words = [word for word in words if not word.startswith('<:')]
        if channel_id in self.data:
            channel = self.data[channel_id]
            try:
                channel["messages"] += 1
            except:
                channel["messages"] = 0
            try:
                channel["emotes"] += len(result)
            except:
                channel["emotes"] = 0
            try:
                channel["words"] += len(words)
            except:
                channel["words"] = 0
        else:
            self.data[channel_id] = {
                "messages": 1,
                "emotes": len(result),
                "words": len(words),
            }
        #print(self.data)

    def new_min(self):
        print("{} = {}".format(str(self.server_id), str(datetime.datetime.now())))
        self.store()
        self.reset()

    def reset(self):
        minute = {
            'timestamp': time.time(),
            'stats': self.data
        }
        self.last_hour.append(self.data)
        for index, minute in enumerate(self.last_hour):
            try:
                if (minute['timestamp'] - time.time()) > 3600:
                    last_hour.pop(index)
            except:
                pass
        self.data = dict()

    def store(self):
        pass

    def matches(self, server_id):
        if self.server_id == server_id:
            return True
        return False

    def get_stats(self, channel_id):
        if channel_id in self.data:
            ch = self.data[channel_id]
            return ch.get("messages", 0), ch.get("emotes", 0), ch.get("words", 0)
        else:
            return 0, 0, 0

    def get_average(self, channel_id):
        avg = list()
        if not self.last_hour:
            return 0, 0, 0
        for minute in self.last_hour:
            if channel_id in minute:
                ch = minute[channel_id]
                avg.append(
                    [ch.get("messages", 0), ch.get("emotes", 0), ch.get("words", 0)]
                )
            else:
                avg.append([0, 0, 0])
        arr = np.array(avg)
        avg = arr.mean(axis=0)
        return avg[0], avg[1], avg[2]


class Stats:
    def __init__(self, bot):
        self.bot = bot
        self.servers = list()
        self.last_min = time.localtime().tm_min
        self.bot.loop.create_task(self.thread_minute())
        # self.tTimer = threading.Thread(target=self.thread_minute)
        # self.tTimer.daemon = True
        # self.tTimer.start()

    @commands.command(pass_context=True, hidden=True)
    async def stats(self, ctx):
        """ get current stats from current channel """
        for server in self.servers:
            if server.matches(int(ctx.message.server.id)):
                messages, emotes, words = server.get_stats(int(ctx.message.channel.id))
                print((messages, emotes, words))

    @commands.command(pass_context=True)
    async def avg(self, ctx):
        """ get current stats from current channel """
        for server in self.servers:
            if server.matches(int(ctx.message.server.id)):
                messages, emotes, words = server.get_average(
                    int(ctx.message.channel.id)
                )
                string = "```\t{:.2f} messages/min \n\t{:.2f} emotes/min \n\t{:.2f} words/min```".format(
                    messages, emotes, words
                )
                await self.bot.say(string)
                break
        else:
            await self.bot.say("Currently no data available.")

    async def on_message(self, message):
        server_id = int(message.server.id)
        channel_id = int(message.channel.id)

        if message.author == self.bot.user:
            return

        influxdb_message(message)

        for server in self.servers:
            if server.matches(server_id):
                server.update(channel_id, message.content)
                break  # found the right one, break
        else:
            server = ServerStats(server_id)
            server.update(channel_id, message.content)
            self.servers.append(server)

    async def thread_minute(self):
        next_call = int(time.time()) + (60 - time.localtime().tm_sec)  # call on the next full minute
        delay = max(0, (next_call - time.time()))
        await asyncio.sleep(delay)
        while True:
            self.minute_tick()
            next_call += (60 - time.localtime().tm_sec)
            delay = max(0, (next_call - time.time()))
            await asyncio.sleep(delay)

    def minute_tick(self):
        cur_min = time.localtime().tm_min
        if cur_min > self.last_min:
            new_min = True
        elif self.last_min > 0 and cur_min == 0:
            new_min = True
        else:
            new_min = False
        if new_min:
            self.last_min = time.localtime().tm_min
            for server in self.servers:
                server.new_min()

def influxdb_message(message):
    messagedata = {}
    regex = re.compile(r":[A-Za-z0-9]+:")
    result = regex.findall(message.content)
    messagedata['server']  = int(message.server.id)
    messagedata['channel'] = int(message.channel.id)
    messagedata['author']  = int(message.author.id)
    words = message.content.split()
    words = [word for word in words if not word.startswith('<:')]
    messagedata['content'] = float(len(words))
    messagedata['emotes'] = int(len(result))
    cur_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    stats_collector(messagedata, cur_time)

def stats_collector(message, timestamp):
    ''' takes discord message object and sends data to influxdb '''
    stats = []

    # Count messages
    stats.append({
        'measurement': 'message_count',
        'fields': {
            'value': 1.0
        },
        'time': timestamp,
        'tags': {
            'channel': message['channel'],
            'server' : message['server'],
            'author' : message['author']
        }
    })

    # Count words per message
    stats.append({
        'measurement': 'word_count',
        'fields': {
            'value': message['content']
        },
        'time': timestamp,
        'tags': {
            'channel': message['channel'],
            'server' : message['server'],
            'author' : message['author']
        }
    })

    # emote count per message
    stats.append({
        'measurement': 'emotes_count',
        'fields': {
            'value': message['emotes']
        },
        'time': timestamp,
        'tags': {
            'channel': message['channel'],
            'server' : message['server'],
            'author' : message['author']
        }
    })

    send_to_influxdb(stats, timestamp)

    return True

def send_to_influxdb(data, timestamp):
    """ send results to kairosdb """
    try:
        inf_client.write_points(data)
    except Exception as ex:
        if "database not found" in str(ex):
            inf_client.create_database('message_stats')
            try:
                inf_client.write_points(data)
            except:
                pass
    #kairosdb_server = '<redacted>'
    #headers = {'Content-Type': 'application/json'}
    #response = requests.post(kairosdb_server, json.dumps([data]), headers=headers)

    #return response.status_code

def setup(bot):
    bot.add_cog(Stats(bot))

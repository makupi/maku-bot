import discord
from discord.ext import commands
import time
import re
import numpy as np

class ServerStats:
    def __init__(self, server_id):
        self.server_id = server_id
        self.last_hour = list()
        self.data = dict()

    def update(self, channel_id, content):
        regex = re.compile(r':[A-Za-z0-9]+:')
        result = regex.findall(content)
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
                channel["words"] += len(content.split())
            except:
                channel["words"] = 0
        else:
            self.data[channel_id] = {
                'messages': 1,
                'emotes': len(result),
                'words': len(content.split())
            }
        print(self.data)
            
    def new_min(self):
        self.store()
        self.reset()

    def reset(self):
        self.last_hour.append(self.data)
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
            return 0,0,0
        for minute in self.last_hour:
            if channel_id in minute:
                ch = minute[channel_id]
                avg.append([ch.get("messages", 0), ch.get("emotes", 0), ch.get("words", 0)])
            else:
                avg.append([0,0,0])
        arr = np.array(avg)
        avg = arr.mean(axis=0)
        return avg[0], avg[1], avg[2]


class Stats:
    def __init__(self, bot):
        self.bot = bot
        self.servers = list()
        self.last_min = time.localtime().tm_min

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
                messages, emotes, words = server.get_average(int(ctx.message.channel.id))
                string = "```\t{:.2f} messages/min \n\t{:.2f} emotes/min \n\t{:.2f} words/min```".format(messages, emotes, words)
                await self.bot.say(string)
                break
        else:
            await self.bot.say("Currently no data available.")

    async def on_message(self, message):
        server_id = int(message.server.id)
        channel_id = int(message.channel.id)

        if self.is_new_min():
            self.last_min = time.localtime().tm_min
            for server in self.servers:
                server.new_min()
        if message.author == self.bot.user:
            return

        for server in self.servers:
            if server.matches(server_id):
                server.update(channel_id, message.content)
                break  # found the right one, break 
        else:
            server = ServerStats(server_id)
            server.update(channel_id, message.content)
            self.servers.append(server)
        
        




    def is_new_min(self):
        cur_min = time.localtime().tm_min
        if cur_min > self.last_min:
            return True
        if self.last_min > 0 and cur_min == 0:
            return True
        return False



def setup(bot):
    bot.add_cog(Stats(bot))

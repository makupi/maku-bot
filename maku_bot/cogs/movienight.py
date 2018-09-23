import discord
from discord.ext import commands
from pymongo import MongoClient
import os
import time
import random

import pprint
pp = pprint.PrettyPrinter(indent=4)

reactions = ['\N{DIGIT ONE}' + u"\u20E3", '\N{DIGIT TWO}' + u"\u20E3", '\N{DIGIT THREE}' + u"\u20E3", '\N{DIGIT FOUR}' + u"\u20E3", '\N{DIGIT FIVE}' + u"\u20E3"]

class MovieNight:
    def __init__(self, bot):
        self.bot = bot
        mongodb = os.environ.get('MONGODB', None)
        mdb_client = MongoClient(mongodb)
        self.db = mdb_client.movienight
    
    @commands.command(name='movie',
                      description='Suggest a movie for MovieNight',
                      brief='Suggest a movie for MovieNight',
                      pass_context=True)
    async def movie(self, ctx):
        server = self.db[ctx.message.server.id]
        movie = ctx.message.content.split('.movie ', 1)[1]
        new_movie = {
            'movie': movie,
            'user': ctx.message.author.display_name,
            'user_id': ctx.message.author.id,
            'time': time.time()
        }
        #add movie to suggestions, if there is currently open suggestions
        self.check_db_init(ctx.message.server.id)
        is_open = server.find_one({'open': {'$exists': 1}})
        try:
            is_open = is_open.get('open', None)
        except:
            is_open = None
        string = ""
        if is_open:
            exists = server.find_one({"movies.user_id": new_movie['user_id']})
            if exists is None:
                server.update_one({}, {'$push': {'movies': new_movie}})
                string = '"{}" was added to the list.'.format(new_movie['movie'])
            else:
                # finds the exact movie object from that user to $pull it
                try:
                    for _movie in exists['movies']:
                        if _movie['user_id'] == new_movie['user_id']:
                            movie = _movie
                            break
                    else:
                        movie = None
                except:
                    movie = None
                if movie is not None:
                    server.update_one({}, {'$pull': {'movies': movie}})
                server.update_one({}, {'$push': {'movies': new_movie}})
                string = 'Suggestion was updated to "{}".'.format(new_movie['movie'])
        else:
            string = "Suggestions are currently closed."
        await self.bot.say(string)

    @commands.command(name='movie-list', 
                      description='Currently suggested movies',
                      brief='Currently suggested movies',
                      pass_context=True)
    async def movie_list(self, ctx):
        #print the current suggestions 
        server = self.db[ctx.message.server.id]
        movies = server.find_one({})
        try:
            movies = movies.get('movies', list())
        except:
            movies = list()
        if len(movies) == 0: 
            await self.bot.say("Currently no movies suggested.")
            return
        string = "```bash\n"
        for movie in movies:
            string += '"{}" suggested by {}\n'.format(movie['movie'], movie['user'])
        string += "```"
        await self.bot.say(string)
            
    
    @commands.command(name='movie-open', 
                      description='Open up suggestions',
                      brief='Open up suggestions',
                      pass_context=True)
    @commands.has_permissions(administrator=True)
    async def movie_open(self, ctx):
        server = self.db[ctx.message.server.id]
        self.check_db_init(ctx.message.server.id)
        server.update_one({'open': {'$exists': 1}}, {'$set': {'open': True}})
        string = "Suggestions for next Movienight are open! Use `.movie name` to suggest a movie."
        await self.bot.say(string)
    
    @commands.command(name='movie-close', 
                      description='close up suggestions',
                      brief='close up suggestions',
                      pass_context=True)
    @commands.has_permissions(administrator=True)
    async def movie_close(self, ctx):
        server = self.db[ctx.message.server.id]
        self.check_db_init(ctx.message.server.id)
        server.update_one({'open': {'$exists': 1}}, {'$set': {'open': False}})

    
    @commands.command(name='movie-clear', 
                      description='clear suggestions',
                      brief='clear suggestions',
                      pass_context=True)
    @commands.has_permissions(administrator=True)
    async def movie_clear(self, ctx):
        server = self.db[ctx.message.server.id]
        is_open = server.find_one({'open': {'$exists': 1}})
        try:
            is_open = is_open.get('open', None)
        except:
            is_open = None
        server.delete_one({'open': {'$exists': 1}})
        server.insert({'open': is_open, 'movies': []})
    
    @commands.command(name='movie-poll',
                      description='start a poll with 5 from the suggested movie, randomized before selecting',
                      brief='start movie poll',
                      pass_context=True)
    @commands.has_permissions(administrator=True)
    async def movie_poll(self, ctx):
        server = self.db[ctx.message.server.id]
        try:
            movies = server.find_one({})['movies']            
        except Exception as ex:
            print("exception occured {}".format(ex))
            movies = list()
        
        number_movies = len(movies)
        picked_movies = list()
        if number_movies == 0:
            await self.bot.say("No movies suggested. No poll possible.")
            return
        elif number_movies <= 5:  # no shuffle needed 
            picked_movies = movies
        else:
            picked_movies = random.shuffle(movies)[:5]
        string = ""
        
        _reactions = list()
        for index, movie in enumerate(movies):
            temp = '{} \t\t {}\n'.format(reactions[index], movie['movie'])
            string += temp
            _reactions.append(reactions[index])
        #string += "```"
        embed = discord.Embed(description=string)
        message = await self.bot.say('**MOVIE NIGHT POLL**', embed=embed)
        for react in _reactions:
            await self.bot.add_reaction(message, react)
        
    
    def check_db_init(self, server_id):
        server = self.db[server_id]
        is_open = server.find_one({'open': {'$exists': 1}})
        try:
            is_open = is_open.get('open', None)
        except:
            is_open = None
        if is_open is None:
            server.insert({'open': False, 'movies': []})

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case MembersCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(MovieNight(bot))

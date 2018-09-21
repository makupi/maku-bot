import discord
from discord.ext import commands
from pymongo import MongoClient
import os
import time

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
            'time': time.time()
        }
        print(new_movie)
        #add movie to suggestions, if there is currently open suggestions
        self.check_db_init(ctx.message.server.id)
        is_open = server.find_one({'open': {'$exists': 1}})
        try:
            is_open = is_open.get('open', None)
        except:
            is_open = None
        string = ""
        if is_open:
            exists = server.find_one({"movies.user": new_movie['user']})
            if exists is None:
                ret = server.update_one({'movies': {'$exists': 1}}, {'$push': {'movies': new_movie}})
                string = '"{}" was added to the list.'.format(new_movie['movie'])
            else:
                #TODO: doesn't work yet. pop the previous suggestion and push new one
                server.update_one({'movies': {'$exists': 1}}, {'$pull': {'movies.user': exists['user']}})
                server.update_one({'movies': {'$exists': 1}}, {'$push': {'movies': new_movie}})
                string = 'Suggestion was updated to "{}".'.format(new_movie['movie'])
        else:
            string = "Suggestions are currently closed."
        await self.bot.say(string)

    @commands.command(name='movie-list', 
                      description='Currently suggested movies',
                      brief='Currently suggested movies',
                      pass_context=True)
    async def movie_list(self, ctx):
        print("suggestions")
        #print the current suggestions 
        server = self.db[ctx.message.server.id]
        movies = server.find_one({'movies': {'$exists': 1}})
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
        print(string)
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
    async def movie_clear(self,ctx):
        server = self.db[ctx.message.server.id]
        is_open = server.find_one({'open': {'$exists': 1}})
        try:
            is_open = is_open.get('open', None)
        except:
            is_open = None
        server.delete_one({'open': {'$exists': 1}})
        server.insert({'open': is_open, 'movies': []})
    
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

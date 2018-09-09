import discord
from discord.ext import commands

class MovieNight:
    def __init__(self, bot):
        self.bot = bot
        self.db = {'suggestions': [], 'open':False}
    
    @commands.command(name='suggest',
                      description='Suggest a movie for MovieNight',
                      brief='Suggest a movie for MovieNight')
    async def suggest(self, movie : str):
        print(movie)
        #add movie to suggestions, if there is currently open suggestions
        if self.db.get("open"):
            self.db["suggestions"].append(movie)

    @commands.command(name='suggestions', 
                      description='Currently suggested movies',
                      brief='Currently suggested movies')
    async def suggestions(self):
        print("suggestions")
        #print the current suggestions 
        print(self.db.get("suggestions"))
    
    @commands.command(name='openS', 
                      description='Open up suggestions',
                      brief='Open up suggestions')
    @commands.has_permissions(administrator=True)
    async def openS(self):
        print("open-suggestions")
        self.db.update({"open": True})
    
    @commands.command(name='closeS', 
                      description='close up suggestions',
                      brief='close up suggestions')
    @commands.has_permissions(administrator=True)
    async def closeS(self):
        print("close-suggestions")
        self.db.update({"open": False})
    
    @commands.command(name='clearS', 
                      description='clear suggestions',
                      brief='clear suggestions')
    @commands.has_permissions(administrator=True)
    async def clearS(self):
        print("clear-suggestions")
        self.db["suggestions"] = []
    

# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case MembersCog.
# When we load the cog, we use the name of the file.
def setup(bot):
    bot.add_cog(MovieNight(bot))

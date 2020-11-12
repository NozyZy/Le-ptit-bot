import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = '--')

class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addYoutube(self, ctx, *, title):
        with open("txt/youtube.txt", "a") as file:
            file.write('\n' + title)
        print(title)
        ctx.send(title + " a été ajouté dans la fichier ``txt/youtube.txt``")

    @commands.command()
    async def searchYoutube(self, ctx, *, query):
        with open("txt/youtube.txt", "a") as file:
            youtubes_lines = file.readlines()
        queries = query.split()
        for line in youtubes_lines:
            for word in queries:
                if word in line.split():
                    await ctx.send(line)

def setup(bot):
    bot.add_cog(Youtube(bot))

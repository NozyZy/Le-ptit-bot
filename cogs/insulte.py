import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = '--')

class Insulte(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addInsult(self, ctx, *, nouvelle_insulte):
        if len(nouvelle_insulte) <= 2:
            await ctx.send("Sympa l'insulte...")
            return
        with open("txt/insultes.txt", "a") as file:
            file.write('\n' + nouvelle_insulte)
        await ctx.send(nouvelle_insulte + " a été ajouté au fichier txt/insultes.txt")

def setup(bot):
    bot.add_cog(Insulte(bot))

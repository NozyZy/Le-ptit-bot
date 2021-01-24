import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Help cog has been loaded sucessfully (pls translate to french)")

    # teh help command, add commands call, but not reactions
    @commands.command(aliases=["Help"])
    async def help(self, ctx, arg=None):
        if arg is None:
            help_embed = discord.Embed(
                title="Le-ptit-bot",
                color=0xD6C18A)  # vous pouvez changer le colour
            help_embed.add_field(name="```--```",
                                 value="le préfixe",
                                 inline=False)
            help_embed.add_field(
                name="Commandes",
                value=
                "`F`: to pay respect\n`--serverInfo`: pour connaître les infos du server\n`--addInsult`: pour ajouter des insultes et **tg** pour te faire insulter\n`--addWord`: pour ajouter un mot au jeu\n`--game`: pour jouer au jeu du **clap**\n`--repeat`: pour que je répète ce qui vient après l'espace\n`--appel`: puis le pseudo de ton pote pour l'appeler\n`--crypt`:pour chiffrer/déchiffrer un message César (décalage)\n`--random`: pour écrire 5 mots aléatoires\n`--randint <nb1>, <nb2>`: pour avoir un nombre aléatoire entre `nb1` et `nb2`\n`--calcul <nb1> <les operations: +, -, /, *, ^, !)> <nb2>`: pour avoir un calcul adéquat \n",
            )
            help_embed2 = discord.Embed(title="Le-ptit-bot", color=0xD6C18A)
            help_embed2.add_field(
                name="Commandes Pt.2",
                value=
                "`-isPrime <nb>`: pour tester si `nb` est premier\n`--prime <nb>`: pour avoir la liste de tous les nombres premiers jusqu'a <nb> au minimum\n`--poll <le question> <prop1> <prop2>...<prop10>`: pour avoir un sondage de max 10 propositions\n",
            )
            await ctx.send(embed=help_embed2)
            help_embed3 = discord.Embed(title="Le-ptit-bot", color=0xD6C18A)
            help_embed3.add_field(
                name="Commandes Pt.3",
                value=
                "`--song <argument>`: puis\n`add`: ajoute un morceau à la liste ([URL youtube] - [titre] - [artiste])\n`random`: choisit un morceau dans la liste\n`all`: affiche toute la liste\n",
            )
            help_embed3.set_footer(
                text=
                "Et je risque de réagir à tes messages, parfois de manière... **Inattendue** 😈"
            )
            await ctx.send(embed=help_embed3)


def setup(bot):
    bot.add_cog(Help(bot))

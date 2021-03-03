import asyncio
import time
from datetime import date

import discord
import googletrans
import youtube_dl
from discord.ext import commands
from googletrans import Translator
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from fonctions import *

# ID : 653563141002756106
# https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8

intents = discord.Intents.default()
intents.members = True
client = discord.Client()
bot = commands.Bot(command_prefix="--", description="Le p'tit bot !")
nbtg: int = 0


# On ready message
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="dis tg pour voir ?"))
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


# Get every message sent, stocked in 'message'
@bot.event
async def on_message(message):
    global nbtg
    channel = message.channel
    MESSAGE = message.content.lower()
    rdnb = random.randint(1, 5)
    today = date.today()

    # open and stock the dico, with a lot of words
    dicoFile = open("txt/dico.txt", "r+")
    dicoLines = dicoFile.readlines()
    dicoSize = len(dicoLines)
    dicoFile.close()

    bansFile = open("txt/bans.txt", "r+")
    bansLines = bansFile.readlines()
    bansFile.close()

    if message.author == bot.user:  # we don't want the bot to repeat itself
        return

    if (str(channel.id) + "\n") in bansLines:     # option to ban reactions from some channels
        await bot.process_commands(message)
        return

    # expansion of the dico, with words of every messages (stock only words, never complete message)
    # we don't want a specific bot (from a friend) to expand the dico
    if message.author.id != 696099307706777610:
        if "```" in MESSAGE:
            return
        mot = ""
        for i in range(len(MESSAGE)):
            mot += MESSAGE[i]
            if MESSAGE[i] == " " or i == len(MESSAGE) - 1:
                ponctuation = [
                    " ",
                    ".",
                    ",",
                    ";",
                    "!",
                    "?",
                    "(",
                    ")",
                    "[",
                    "]",
                    ":",
                    "*",
                ]
                for j in ponctuation:
                    mot = mot.replace(j, " ")
                if verifAlphabet(mot) and 0 < len(mot) < 27:
                    mot += "\n"
                    if mot not in dicoLines:
                        print(mot)
                        dicoLines.append(mot)
                mot = ""

    dicoLines.sort()
    if len(dicoLines) > 0 and len(dicoLines) > dicoSize:
        dicoFile = open("txt/dico.txt", "w+")
        for i in dicoLines:
            dicoFile.write(i)
        dicoFile.close()

    # stock file full of insults (yes I know...)
    fichierInsulte = open("txt/insultes.txt", "r")
    linesInsultes = fichierInsulte.readlines()
    insultes = []
    for i in linesInsultes:
        i = i.replace("\n", "")
        insultes.append(i)
    fichierInsulte.close()

    if message.content.startswith("--addInsult"):
        print("Ajout d'insulte...")
        mot = str(message.content)
        mot = mot.replace(mot[0:12], "")
        if len(mot) <= 2:
            await channel.send("Sympa l'insulte...")
            return
        mot = "\n" + mot
        fichierInsulte = open("txt/insultes.txt", "a")
        fichierInsulte.write(mot)
        fichierInsulte.close()
        text = insultes[len(insultes) - 1]
        await channel.send(text)

    # ping a people 10 time, once every 3 sec
    if MESSAGE.startswith("--appel ") and channel.guild != "EFREI International 2025":
        if "<@!653563141002756106>" in MESSAGE:
            await channel.send("T'es un marrant toi")
        elif "<@" not in MESSAGE:
            await channel.send("Tu veux appeler quelqu'un ? Bah tag le ! *Mondieu...*")
        else:
            nom = MESSAGE.replace("--appel ", "")
            liste = [
                "Allo ",
                "T'es la ? ",
                "Tu viens ",
                "On t'attend...",
                "Ca commence a faire long ",
                "Tu viens un jour ??? ",
                "J'en ai marre de toi... ",
                "Allez grouille !! ",
                "Toujours en rertard de toute facon... ",
                "ALLOOOOOOOOOOOOOOOOOOOOOOOOOO ",
            ]
            random.shuffle(liste)
            for mot in liste:
                text = mot + nom
                await channel.send(text)
                time.sleep(3)
            return

    # if you tag this bot in any message
    if "<@!653563141002756106>" in MESSAGE:
        user = str(message.author)
        user = user.replace(user[len(user) - 5:len(user)], "")
        rep = [
            "ya quoi ?!",
            "Qu'est ce que tu as " + user + " ?",
            "Oui c'est moi",
            "Présent !",
            "*Oui ma bicheuh <3*",
            user + "lance un duel.",
            "Je t'aime.",
            "T'as pas d'amis ? trouduc"
        ]
        if user == "Le Grand bot":
            rep.append("Oui bb ?")
            rep.append("Yo <@!747066145550368789>")
        elif message.author.id == 359743894042443776:
            rep.append("Patron !")
            rep.append("Eh mattez, ce mec est mon dev 👆")
            rep.append("Je vais tous vous anéantir, en commençant par toi.")
            rep.append("Tu es mort.")
        await channel.send(random.choice(rep))
        return

    # send 5 randoms words from the dico
    if MESSAGE == "--random":
        text = ""
        rd_dico = dicoLines
        random.shuffle(rd_dico)
        for i in range(5):
            text += rd_dico[i]
            if i != 4:
                text += " "
        text += "."
        text = text.replace("\n", "")
        text = text.replace(text[0], text[0].upper(), 1)
        await channel.send(text)

    # send the number of words stocked in the dico
    if MESSAGE == "--dico":
        text = "J'ai actuellement " \
               + str(len(dicoLines)) \
               + " mots enregistrés, nickel"
        await channel.send(text)

    # begginning of reaction programs, get inspired
    if not MESSAGE.startswith("--"):

        if "enerv" in MESSAGE or "énerv" in MESSAGE and rdnb >= 3:
            await channel.send("(╯°□°）╯︵ ┻━┻")

        if "(╯°□°）╯︵ ┻━┻" in MESSAGE:
            await channel.send("┬─┬ ノ( ゜-゜ノ)")

        if MESSAGE.startswith("tu sais") or MESSAGE.startswith("vous savez") or \
                MESSAGE.startswith("savez vous") or MESSAGE.startswith("savez-vous") or \
                MESSAGE.startswith("savais-tu") or MESSAGE.startswith("savais tu"):
            reponses = [
                "J'en ai vraiment rien à faire tu sais ?",
                "Waaa... Je bois tes paroles",
                "Dis moi tout bg",
                "Balec",
                "M'en fous",
                "Plait-il ?"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("hein"):
            await channel.send("deux.")

            # waits for a message valiudating further instructions
            def check(m):
                return ("3" in m.content or
                        "trois" in m.content) and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
            else:
                reponses = [
                    "BRAVO TU SAIS COMPTER !",
                    "SOLEIL !",
                    "4, 5, 6, 7.... oh et puis merde",
                    "HAHAHAHAH non.",
                    "stop.",
                ]
                await channel.send(random.choice(reponses))

        if MESSAGE == "pas mal":
            reponses = ["mouais", "peut mieux faire", "woaw", ":o"]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ez" or MESSAGE == "easy") and rdnb >= 3:
            reponses = [
                "https://tenor.com/view/walking-dead-easy-easy-peasy-lemon-squeazy-gif-7268918"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE in [
            "bite",
            "zizi",
            "teub",
            "zboub",
            "penis",
            "chybre",
            "chybrax",
            "chibre",
        ]:
            text = "8" + "=" * random.randint(0, int(
                today.strftime("%d"))) + "D"
            await channel.send(text)

        if "yanis" in MESSAGE and rdnb == 5:
            await channel.send("La Bretagne c'est pas ouf.")

        if MESSAGE.startswith("stop") or MESSAGE.startswith("arrête") or MESSAGE.startswith("arrete"):
            await channel.send("https://tenor.com/view/stop-it-get-some-help-gif-7929301")

        if MESSAGE.startswith("exact"):
            reponses = [
                "Je dirais même plus, exact.",
                "Il est vrai",
                "AH BON ??!",
                "C'est cela",
                "Plat-il ?",
                "Jure ?",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE == "<3":
            reponses = [
                "Nique ta tante (pardon)",
                "<3",
                "luv luv",
                "moi aussi je t'aime ❤"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE in ["toi-même", "toi-meme", "toi même", "toi meme"]:
            reponses = [
                "Je ne vous permet pas",
                "Miroir magique",
                "C'est celui qui dit qui l'est",
            ]
            await channel.send(random.choice(reponses))

        if "<@!747066145550368789>" in message.content:
            reponses = [
                "bae",
                "Ah oui, cette sous-race de <@!747066145550368789>",
                "il a moins de bits que moi",
                "son pere est un con",
                "ca se dit grand mais tout le monde sait que....",
            ]
            await channel.send(random.choice(reponses))

        if "❤" in MESSAGE:
            await message.add_reaction("❤")

        if MESSAGE == "1":
            await channel.send("2")

            # waits for a message valiudating further instructions
            def check(m):
                return m.content == "3" and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
            else:
                await channel.send("SOLEIL !")

        if MESSAGE == "a":

            def check(m):
                return m.content == "b" and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
            else:
                await channel.send("A B C GNEU GNEU MARRANT TROU DU CUL !!!")

        if MESSAGE == "ah":
            if rdnb >= 4:
                reponses = ["Oh", "Bh"]
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace("a", dicoLines))

        if MESSAGE == "oh":
            if rdnb >= 4:
                reponses = ["Quoi ?", "p", "ah", ":o"]
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace("o", dicoLines))

        if MESSAGE == "eh":
            if rdnb >= 4:
                reponses = ["hehehehehe", "oh"]
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace("é", dicoLines))

        if MESSAGE.startswith("merci"):
            if rdnb >= 3:
                reponses = [
                    "De rien hehe",
                    "C'est normal t'inquiète",
                    "Je veux le cul d'la crémière avec.",
                    "non.",
                    "Excuse toi non ?",
                    "Au plaisir"
                ]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("🥰")

        if MESSAGE == "skusku" or MESSAGE == "sku sku":
            await channel.send("KICÉKIJOUE ????")

        if ("😢" in MESSAGE or "😭" in MESSAGE) and rdnb >= 3:
            reponses = ["cheh", "dur dur", "dommage mon p'tit pote", "balec", "tant pis"]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("tu veux"):
            reponses = [
                "Ouais gros",
                "Carrément ma poule",
                "Mais jamais tes fou ptdr",
                "Oui."
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("quoi"):
            reponses = [
                "feur",
                "hein ?",
                "nan laisse",
                "oublie",
                "rien",
                "😯"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("pourquoi"):
            reponses = [
                "PARCEQUEEEE",
                "Aucune idée.",
                "Demande au voisin",
                "Pourquoi tu demandes ça ?"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE in ["facepalm", "damn", "fait chier", "fais chier", "ptn", "putain"] \
                or MESSAGE.startswith("pff") or MESSAGE.startswith("no.."):
            await channel.send(
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif")

        if MESSAGE.startswith("t'es sur") or MESSAGE.startswith("t sur"):
            reponses = [
                "Ouais gros",
                "Nan pas du tout",
                "Qui ne tente rien...",
                "haha 👀"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("ah ouais") or MESSAGE.startswith("ah bon"):
            reponses = [
                "Ouais gros",
                "Nan ptdr",
                "Je sais pas écoute...",
                "tg"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("au pied") and message.author.id == 359743894042443776:
            reponses = [
                "wouf wouf",
                "Maître ?",
                "*s'agenouille*\nComment puis-je vous être utile ?",
                "*Nous vous devons une reconnaissance éternelllllllle*"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("lourd") and rdnb >= 4:
            await channel.send("Sku sku")

        if "<@!321216514986606592>" in MESSAGE and rdnb >= 4:
            reponses = [
                "Le VP numéro 2",
                "Encore lui ?",
                "fasstin"
            ]
            await channel.send(random.choice(reponses))

        if "<@!761898936364695573>" in MESSAGE:
            await channel.send("Tu parles comment de mon pote là ?")

        if "tg" in MESSAGE:
            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if MESSAGE[i] == " " and MESSAGE[i + 1] == "t" and MESSAGE[i + 2] == "g" and MESSAGE[i + 3] == " ":
                    nbtg += 1
                    activity = "insulter {} personnes".format(nbtg)
                    await bot.change_presence(activity=discord.Game(name=activity))
                    await channel.send(random.choice(insultes))
                    if rdnb >= 4:
                        await message.add_reaction('🇹')
                        await message.add_reaction('🇬')

        if MESSAGE == "cheh" or MESSAGE == "sheh":
            if rdnb >= 3:
                reponses = [
                    "Oh tu t'excuses",
                    "Cheh",
                    "C'est pas gentil ça",
                    "🙁"
                ]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("🥰")

        if MESSAGE == "non":
            reponses = [
                "si.",
                "ah bah ca c'est sur",
                "SÉRIEUX ??",
                "logique aussi",
                "jure ?"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("lequel"):
            await channel.send("Le deuxième.")

        if MESSAGE.startswith("laquelle"):
            await channel.send("La deuxième.")

        if MESSAGE.startswith("miroir magique"):
            await channel.send(MESSAGE)

        if MESSAGE.startswith("jure"):
            if "wola" in MESSAGE:
                await channel.send("Wola")
            elif "wallah" in MESSAGE:
                await channel.send("Wallah")
            else:
                rep = await channel.send("Je jure de dire la vérité, uniquement la vérité et toute la vérité")
                if rdnb >= 4:
                    await rep.add_reaction("✌")

        if "☹" in MESSAGE or "😞" in MESSAGE or "😦" in MESSAGE:
            await message.add_reaction("🥰")

        if MESSAGE == "f" or MESSAGE == "rip":
            await channel.send(
                "#####\n#\n#\n####\n#\n#\n#       to pay respect")

        if ("quentin" in MESSAGE or "quent1" in MESSAGE) and rdnb >= 3:
            await channel.send("Papa ! 🤗")

        if MESSAGE.startswith("god"):
            day = today.strftime("%d")
            month = today.strftime("%m")
            MESSAGE = MESSAGE.replace("god", "")

            userID = ""
            if "<@!" not in MESSAGE:
                userID = int(message.author.id)
            else:
                i = 0
                for i in range(len(MESSAGE)):
                    if (MESSAGE[i] == "<" and MESSAGE[i + 1] == "@"
                            and MESSAGE[i + 2] == "!"):
                        i += 3
                        userID = ""
                        break
                while MESSAGE[i] != ">" and i < len(MESSAGE):
                    userID += MESSAGE[i]
                    i += 1
                userID = int(userID)
            if userID % 5 != (int(day) + int(month)) % 5:
                await channel.send("Not today (☞ﾟヮﾟ)☞")
                return
            user = await message.guild.fetch_member(userID)
            pfp = user.avatar_url
            embed = discord.Embed(
                title="This is God",
                description="<@%s> is god." % userID,
                color=0xECCE8B,
            )
            embed.set_thumbnail(url=pfp)

            await channel.send("God looks like him.", embed=embed)

        if MESSAGE.startswith("hello"):
            await channel.send(file=discord.File("images/helo.jpg"))

        if MESSAGE == "enculé" or MESSAGE == "enculer":
            image = ["images/tellermeme.png", "images/bigard.jpeg"]
            await channel.send(file=discord.File(random.choice(image)))

        if MESSAGE == "stonks":
            await channel.send(file=discord.File("images/stonks.png"))

        if MESSAGE == "parfait" or MESSAGE == "perfection":
            await channel.send(file=discord.File("images/perfection.jpg"))

        if MESSAGE.startswith("leeroy"):
            await channel.send(file=discord.File("sounds/Leeroy Jenkins.mp3"))

        if "pute" in MESSAGE:
            reponses = [
                "https://tenor.com/view/mom-gif-10756105",
                "https://tenor.com/view/wiener-sausages-hotdogs-gif-5295979",
                "https://i.ytimg.com/vi/3HZ0lvpdw6A/maxresdefault.jpg",
            ]
            await channel.send(random.choice(reponses))

        if "guillotine" in MESSAGE:
            reponses = [
                "https://tenor.com/view/guillatene-behead-lego-gif-12352396",
                "https://tenor.com/view/guillotine-gulp-worried-scared-slug-riot-gif-11539046",
                "https://tenor.com/view/revolution-guillotine-marie-antoinette-off-with-their-heads-behead-gif-12604431",
            ]
            await channel.send(random.choice(reponses))

        if "pd" in MESSAGE:
            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "p"
                        and MESSAGE[i + 2] == "d" and MESSAGE[i + 3] == " "):
                    await channel.send(file=discord.File("images/pd.jpg"))

        if "oof" in MESSAGE and rdnb >= 2:
            reponses = [
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif"
                "https://tenor.com/view/oh-snap-surprise-shocked-johncena-gif-5026702",
                "https://tenor.com/view/oof-damn-wow-ow-size-gif-16490485",
                "https://tenor.com/view/oof-simpsons-gif-14031953",
                "https://tenor.com/view/yikes-michael-scott-the-office-my-bad-oof-gif-13450971",
            ]
            await channel.send(random.choice(reponses))

        if ("money" in MESSAGE or "argent" in MESSAGE) and rdnb >= 2:
            reponses = [
                "https://tenor.com/view/6m-rain-wallstreet-makeitrain-gif-8203989",
                "https://tenor.com/view/money-makeitrain-rain-guap-dollar-gif-7391084",
                "https://tenor.com/view/taka-money-gif-10114852",
            ]
            await channel.send(random.choice(reponses))

    # teh help command, add commands call, but not reactions
    if MESSAGE == "--help":
        await channel.send(
            "Commandes : \n"
            " **F** to pay respect\n"
            " **--serverInfo** pour connaître les infos du server\n"
            " **--clear** *nb* pour supprimer *nb* messages\n"
            " **--addInsult** pour ajouter des insultes et **tg** pour te faire insulter\n"
            " **--game** pour jouer au jeu du **clap**\n"
            " **--presentation** et **--master** pour créer des memes\n"
            " **--repeat** pour que je répète ce qui vient après l'espace\n"
            " **--appel** puis le pseudo de ton pote pour l'appeler\n"
            " **--crypt** pour chiffrer/déchiffrer un message César (décalage)\n"
            " **--random** pour écrire 5 mots aléatoires\n"
            " **--randint** *nb1*, *nb2* pour avoir un nombre aléatoire entre ***nb1*** et ***nb2***\n"
            " **--calcul** *nb1* (+, -, /, *, ^, !) *nb2* pour avoir un calcul adéquat \n"
            " **--isPrime** *nb* pour tester si *nb* est premier\n"
            " **--prime** *nb* pour avoir la liste de tous les nombres premiers jusqu'a *nb* au minimum\n"
            " **--poll** ***question***, *prop1*, *prop2*,..., *prop10* pour avoir un sondage de max 10 propositions\n"
            " **--invite** pour savoir comment m'inviter\n"
            "Et je risque de réagir à tes messages, parfois de manière... **Inattendue** 😈"
        )
    else:
        # allows command to process after the on_message() function call
        await bot.process_commands(message)


# beginning of the commands


@bot.command()  # delete 'nombre' messages
async def clear(ctx, nombre: int):
    messages = await ctx.channel.history(limit=nombre + 1).flatten()
    for message in messages:
        await message.delete()


@bot.command()  # repeat the 'text', and delete the original message
async def repeat(ctx, *text):
    messages = await ctx.channel.history(limit=1).flatten()
    for message in messages:
        await message.delete()
    await ctx.send(" ".join(text))


@bot.command()  # show the number of people in the server, and its name
async def serverinfo(ctx):
    server = ctx.guild
    nbUsers = server.member_count
    text = f"Le serveur **{server.name}** contient **{nbUsers}** personnes !"
    await ctx.send(text)


@bot.command()  # same, with a capital letter
async def serverInfo(ctx):
    await serverinfo(ctx)


@bot.command()  # send the 26 possibilites of a ceasar un/decryption
async def crypt(ctx, *text):
    mot = " ".join(text)
    messages = await ctx.channel.history(limit=1).flatten()
    for message in messages:
        await message.delete()
    await ctx.send("||" + mot + "|| :\n" + crypting(mot))


@bot.command()  # send a random integer between two numbers, or 1 and 0
async def randint(ctx, *text):
    tab = []
    MESSAGE = "".join(text)
    nb2 = 0
    i = 0
    while i < len(MESSAGE) and MESSAGE[i] != ",":
        if 48 <= ord(MESSAGE[i]) <= 57:
            tab.append(MESSAGE[i])
        i += 1

    if len(tab) == 0:
        await ctx.send("Rentre un nombre banane")
        return

    nb1 = strToInt(tab)

    if i != len(MESSAGE):
        nb2 = strToInt(list=nbInStr(MESSAGE, i, len(MESSAGE)))

    if nb1 == nb2:
        text = "Bah " + str(nb1) + " du coup... 🙄"
        await ctx.send(text)
        return
    if nb2 < nb1:
        temp = nb2
        nb2 = nb1
        nb1 = temp

    rd = random.randint(nb1, nb2)
    print("random ", nb1, ":", nb2, " = ", rd, sep="")
    await ctx.send(rd)


@bot.command()  # same, with a capital letter
async def randInt(ctx, *text):
    await randint(ctx, *text)


@bot.command()  # send a random word from the dico, the first to write it wins
async def game(ctx):
    dicoFile = open("txt/dico.txt", "r+")
    dicoLines = dicoFile.readlines()
    dicoFile.close()

    mot = random.choice(dicoLines)
    mot = mot.replace("\n", "")
    text = "Le premier à écrire **" + mot + "** a gagné"
    reponse = await ctx.send(text)

    if ctx.author == bot.user:
        return

    def check(m):
        return m.content == mot and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await reponse.add_reaction("☹")
    else:
        user = str(msg.author)
        user = user.replace(user[len(user) - 5:len(user)], "")
        text = f"**{user}** a gagné !"
        await ctx.send(text)


@bot.command()  # do a simple calcul of 2 numbers and 1 operator (or a fractionnal)
async def calcul(ctx, *text):
    tab = []
    symbols = ["-", "+", "/", "*", "^", "!"]
    Message = "".join(text)
    Message = Message.lower()
    nb2 = i = rd = 0

    if "infinity" in Message:
        text = ""
        for i in range(1999):
            text += "9"
        await ctx.send(text)
        return

    while i < len(Message) and 48 <= ord(Message[i]) <= 57:
        if 48 <= ord(Message[i]) <= 57:
            tab.append(Message[i])
        i += 1

    if len(tab) == 0:
        await ctx.send("Rentre un nombre banane")
        return

    if i == len(Message) or Message[i] not in symbols:
        await ctx.send("Rentre un symbole (+, -, *, /, ^, !)")
        return

    symb = Message[i]

    nb1 = strToInt(tab)

    if symb == "!":
        if nb1 > 806:  # can't go above 806 recursion deepth
            await ctx.send("806! maximum, désolé 🤷‍♂️")
            return
        rd = facto(nb1)
        text = str(nb1) + "!=" + str(rd)
        await ctx.send(text)
        return

    if i != len(Message):
        tab = nbInStr(Message, i, len(Message))

        if len(tab) == 0:
            await ctx.send("Rentre un deuxième nombre patate")
            return

        nb2 = strToInt(tab)

    if symb == "+":
        rd = nb1 + nb2
    elif symb == "-":
        rd = nb1 - nb2
    elif symb == "*":
        rd = nb1 * nb2
    elif symb == "/":
        if nb2 == 0:
            await ctx.send("±∞")
            return
        rd = float(nb1 / nb2)
    elif symb == "^":
        rd = nb1 ** nb2
    text = str(nb1) + str(symb) + str(nb2) + "=" + str(rd)
    print(text, rd)
    await ctx.send(text)


@bot.command()  # create a reaction poll with a question, and max 10 propositions
async def poll(ctx, *text):
    tab = []
    Message = " ".join(text)
    text = ""
    for i in range(len(Message)):
        if Message[i] == ",":
            tab.append(text)
            text = ""
        elif i == len(Message) - 1:
            text += Message[i]
            tab.append(text)
        else:
            text += Message[i]
    if len(tab) <= 1:
        await ctx.send(
            "Ecris plusieurs choix séparés par des virgules, c'est pas si compliqué que ça..."
        )
        return
    if len(tab) > 11:
        await ctx.send("Ca commence à faire beaucoup non ?... 10 max ca suffit"
                       )
        return
    text = ""
    for i in range(len(tab)):
        if i == 0:
            text += "❓"
        elif i == 1:
            text += "\n1️⃣"
        elif i == 2:
            text += "\n2️⃣"
        elif i == 3:
            text += "\n3️⃣"
        elif i == 4:
            text += "\n4️⃣"
        elif i == 5:
            text += "\n5️⃣"
        elif i == 6:
            text += "\n6️⃣"
        elif i == 7:
            text += "\n7️⃣"
        elif i == 8:
            text += "\n8️⃣"
        elif i == 9:
            text += "\n9️⃣"
        elif i == 10:
            text += "\n🔟"
        text += tab[i]

    reponse = await ctx.send(text)
    for i in range(len(tab)):
        if i == 1:
            await reponse.add_reaction("1️⃣")
        elif i == 2:
            await reponse.add_reaction("2️⃣")
        elif i == 3:
            await reponse.add_reaction("3️⃣")
        elif i == 4:
            await reponse.add_reaction("4️⃣")
        elif i == 5:
            await reponse.add_reaction("5️⃣")
        elif i == 6:
            await reponse.add_reaction("6️⃣")
        elif i == 7:
            await reponse.add_reaction("7️⃣")
        elif i == 8:
            await reponse.add_reaction("8️⃣")
        elif i == 9:
            await reponse.add_reaction("9️⃣")
        elif i == 10:
            await reponse.add_reaction("🔟")


@bot.command()  # find and send all the prime numbers until 14064991, can calcul above but can't send it (8Mb limit)
async def prime(ctx, nb: int):
    if nb < 2:
        await ctx.send("Tu sais ce que ca veut dire 'prime number' ?")
        return
    Fprime = open("txt/primes.txt", "r+")
    primes = Fprime.readlines()
    Fprime.close()
    biggest = int(primes[len(primes) - 1].replace("\n", ""))
    text = ""
    ratio_max = 1.02
    n_max = int(biggest * ratio_max)
    print(biggest, n_max)

    if nb > biggest:
        if biggest % 2 == 0:
            biggest -= 1
        if nb <= n_max:
            await ctx.send("Donne moi quelques minutes bro...")
            for i in range(biggest, nb + 1, 2):
                if is_prime(i):
                    text += str(i) + "\n"
            Fprime = open("txt/primes.txt", "a+")
            Fprime.write(text)
            Fprime.close()
            if nb > 14064991:  # 8Mb file limit
                text = f"Je peux pas en envoyer plus que 14064991, mais tkt je l'ai calculé chez moi là"
                await ctx.send(text)
        else:
            text = f"Ca va me prendre trop de temps, on y va petit à petit, ok ? (max : {int(n_max)})"
            await ctx.send(text)
    else:
        text = f"Tous les nombres premiers jusqu'a 14064991 (plus grand : {biggest})"
        await ctx.send(text, file=discord.File("txt/prime.txt"))


@bot.command()  # find if 'nb' is a prime number, reacts to the message
async def isPrime(ctx, nb: int):
    if is_prime(nb):
        await ctx.message.add_reaction("👍")
    else:
        await ctx.message.add_reaction("👎")


@bot.command()  # send 'nb' random words of the dico, can repeat itself
async def randomWord(ctx, nb: int):
    dicoFile = open("txt/dico.txt", "r+")
    dicoLines = dicoFile.readlines()
    dicoFile.close()

    text = ""
    for i in range(nb):
        text += random.choice(dicoLines)
        if i != nb - 1:
            text += " "
    text += "."
    text = text.replace("\n", "")
    text = text.replace(text[0], text[0].upper(), 1)
    await ctx.send(text)


@bot.command()  # join the vocal channel fo the caller
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command()  # leaves it
async def leave(ctx):
    await ctx.voice_client.disconnect()


musics = {}
ytdl = youtube_dl.YoutubeDL()


# class of youtube videos (from youtube_dl)
class Video:
    def __init__(self, link):
        video = ytdl.extract_info(link, download=False)
        video_format = video["formats"][0]
        self.url = video["webpage_url"]
        self.stream_url = video_format["url"]


# plays a song in the vocal channel [TO FIX]
def playSong(clt, queue, song):
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            song.stream_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        ))

    def next(_):
        if len(queue) > 0:
            newSong = queue[0]
            del queue[0]
            playSong(clt, queue, newSong)
        else:
            asyncio.run_coroutine_threadsafe(clt.disconnect(), bot.loop)

    clt.play(source, after=next)


@bot.command()  # play theyoutube song attached to the URL (TO FIX)
async def play(ctx, url):
    clt = ctx.guild.voice_client

    if clt and clt.channel:
        video = Video(url)
        musics[ctx.guild].append(video)
    else:
        video = Video(url)
        musics[ctx.guild] = []
        playSong(clt, musics[ctx.guild], video)


@bot.command()
async def translate(ctx, *text):
    translator = Translator()
    text = " ".join(text).lower()
    text = text.split(",")
    if text[0] == "showall":
        text[0] = googletrans.LANGUAGES
        await ctx.send(text[0])
        return
    toTranslate = text[0]
    fromLang = text[1].replace(" ", "")
    toLang = text[2].replace(" ", "")
    try:
        textTranslated = translator.translate(toTranslate,
                                              src=fromLang,
                                              dest=toLang)
        text = (toTranslate + " (" + textTranslated.src + ") -> " +
                textTranslated.text + " (" + textTranslated.dest + ")")
    except:
        text = "Nope, sorry !"
    await ctx.send(text)


@bot.command()
async def master(ctx, *text):
    text = " ".join(text)
    if not len(text) or text.count(",") != 2:
        text = ["add 3", "f*cking terms", "splited by ,"]
    else:
        text = text.split(",")
        for term in text:
            if len(term) not in range(1, 20):
                text = ["add terms", "between", "1 and 20 chars"]
    img = Image.open("images/master.jpg")

    fonts = [
        ImageFont.truetype("fonts/Impact.ttf", 26),
        ImageFont.truetype("fonts/Impact.ttf", 18),
        ImageFont.truetype("fonts/Impact.ttf", 22),
    ]

    sizes = []

    for i in range(len(fonts)):
        sizes.append(fonts[i].getsize(text[i])[0])

    draw = ImageDraw.Draw(img)

    draw.text(
        xy=(170 - (sizes[0]) / 2, 100),
        text=text[0],
        fill=(255, 255, 255),
        font=fonts[0],
    )
    draw.text(
        xy=(250 - (sizes[1]) / 2, 190),
        text=text[1],
        fill=(255, 255, 255),
        font=fonts[1],
    )
    draw.text(
        xy=(330 - (sizes[2]) / 2, 280),
        text=text[2],
        fill=(255, 255, 255),
        font=fonts[2],
    )

    img.save("images/mastermeme.jpg")
    await ctx.send(file=discord.File("images/mastermeme.jpg"))


@bot.command()
async def presentation(ctx, *base):
    base = " ".join(base)
    if not len(base):
        base = "add something dude"
    elif len(base) > 200:
        base = "less text bro, i'm not Word"

    text = [""]
    count = j = 0
    for i in range(len(base)):
        if (j > 20 and base[i] == " ") or j > 30:
            text.append(base[i])
            count += 1
            j = 0
        else:
            j += 1

        text[count] += base[i]
    img = Image.open("images/presentation.png")

    font = ImageFont.truetype("fonts/Impact.ttf", 28)
    count += 1
    draw = ImageDraw.Draw(img)
    for i in range(len(text)):
        size = font.getsize(text[i])
        draw.text(
            xy=(335 - size[0] / 2, 170 + i * size[1] - 10 * count),
            text=text[i],
            fill=(0, 0, 0),
            font=font,
        )

    img.save("images/presentationmeme.png")
    await ctx.send(file=discord.File("images/presentationmeme.png"))


@bot.command()
async def ban(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("T'es pas admin, nananananère 😜")
        return
    bansFile = open("txt/bans.txt", "r+")
    bansLines = bansFile.readlines()
    bansFile.close()
    chanID = str(ctx.channel.id) + "\n"
    if chanID in bansLines:
        await ctx.send("Jsuis déjà ban, du calme...")
    else:
        bansFile = open("txt/bans.txt", "a+")
        bansFile.write(chanID)
        bansFile.close()
        await ctx.send("D'accord, j'arrete de vous embeter ici... mais les commandes sont toujours dispos")


@bot.command()
async def unban(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("T'es pas admin, nananananère 😜")
        return
    bansFile = open("txt/bans.txt", "r+")
    bansLines = bansFile.readlines()
    bansFile.close()
    chanID = str(ctx.channel.id) + "\n"
    if chanID not in bansLines:
        await ctx.send("D'accord, mais j'suis pas ban, hehe.")
    else:
        bansFile = open("txt/bans.txt", "w+")
        bansFile.write("")
        bansFile.close()
        bansFile = open("txt/bans.txt", "a+")
        for id in bansLines:
            if id == chanID:
                bansLines.remove(id)
                await ctx.send("JE SUIS LIIIIIIBRE")
            else:
                bansFile.write(id)
        bansFile.close()



@bot.command()
async def invite(ctx):
    await ctx.send(
        "Invitez-moi 🥵 !\nhttps://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8")


"""
@bot.command()
async def say(ctx, number, *text):
    for i in range(int(number)):
        await ctx.send(" ".join(text))
"""


# runs the bot (if you have a TOKEN hahaha)

@bot.command()  # PERSONAL USE ONLY
async def AmongUs(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Nope, t'es pas admin désolé...")
        return

    """
    f_name = open("txt/names.txt", "r+")
    all_names = f_name.readlines()
    random.shuffle(all_names)
    f_name.close()
    random.shuffle(all_names)
    """

    tour = 0
    while 1:
        tour += 1
        test = await ctx.send("On joue ? Réagis pour jouer, sinon tant pis")
        yes = "✅"

        await test.add_reaction(yes)

        time.sleep(10)

        test = await test.channel.fetch_message(test.id)
        users = set()
        for reaction in test.reactions:

            if str(reaction.emoji) == yes:
                async for user in reaction.users():
                    print(reaction)
                    users.add(user)
        """for user in users:
            text = "<@!" + str(user.id) + ">"
            await ctx.send(text)"""

        ids = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21",]
        for user in users:
            if user.id != 653563141002756106:
                ids.append(user.id)
        random.shuffle(ids)
        if len(ids) < 5:
            await ctx.send("En dessous de 5 joueurs on va avoir du mal...")
        else:
            playersID = equal_games(ids)
            color = [
                0x0000ff,
                0x740001,
                0x458b74,
                0x18eeff,
                0xeae4d3,
                0xff8100,
                0x9098ff,
                0xff90fa,
                0xff1443,
                0xff1414,
                0x7fffd4,
                0x05ff3c,
                0x05ffa1
            ]
            text = "**Partie n°" + str(tour) + "**"
            await ctx.send(text)
            for i in range(len(playersID)):
                y = 0
                embed = discord.Embed(title=("**Equipe n°" + str(i + 1) + "**"), color=random.choice(color))
                embed.set_thumbnail(url="https://tse1.mm.bing.net/th?id=OIP.3WhrRCJd4_GTM2VaWSC4SAAAAA&pid=Api")
                for user in playersID[i]:
                    y += 1
                    embed.add_field(name=("Joueur " + str(y)), value="<@!" + str(user) + ">", inline=True)
                await ctx.send(embed=embed)

        def check(m):
            id_list = [321216514986606592, 359743894042443776, 135784465065574401, 349548485797871617]
            return (m.content == "NEXT" or m.content == "END") and m.channel == ctx.channel and m.author.id in id_list

        msg = await bot.wait_for('message', check=check)
        if msg.content == "END":
            await ctx.send("**Fin de la partie...**")
            break

bot.run(TOKEN)

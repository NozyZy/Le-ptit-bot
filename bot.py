import asyncio
import time
import secret
import discord
import googletrans
import youtube_dl

from datetime import date
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
bot = commands.Bot(command_prefix="--",
                   description="Le p'tit bot !",
                   case_insensitive=True)
tgFile = open("txt/tg.txt", "r+")
nbtg: int = int(tgFile.readlines()[0])
tgFile.close()


# On ready message
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"insulter {nbtg} personnes"))
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
    user = message.author

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

    if (str(channel.id) +
            "\n") in bansLines:  # option to ban reactions from some channels
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
                        print(f">>({user.name} {time.asctime()}) - nouveau mot : {mot}")
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
    for line in linesInsultes:
        line = line.replace("\n", "")
        insultes.append(line)
    fichierInsulte.close()

    if message.content.startswith("--addInsult"):
        print(f">>({user.name} {time.asctime()})", end=" - ")
        mot = str(message.content)
        mot = mot.replace(mot[0:12], "")
        if len(mot) <= 2:
            await channel.send("Sympa l'insulte...")
            return
        mot = "\n" + mot
        fichierInsulte = open("txt/insultes.txt", "a")
        fichierInsulte.write(mot)
        fichierInsulte.close()
        print("Nouvelle insulte :", mot)
        await channel.send("Je retiens...")

    # ping a people 10 time, once every 3 sec
    if MESSAGE.startswith("--appel"):
        print(f">>({user.name} {time.asctime()})", end=" - ")
        if "<@!653563141002756106>" in MESSAGE:
            await channel.send("T'es un marrant toi")
            print("A tenté d'appeler le bot")
        elif "<@" not in MESSAGE:

            await channel.send("Tu veux appeler quelqu'un ? Bah tag le ! *Mondieu...*")
            print("A tenté d'appeler sans taguer")
        elif not message.author.guild_permissions.administrator:
            await channel.send("Dommage, tu n'as pas le droit ¯\_(ツ)_/¯")
            print("A tenté d'appeler sans les droits")
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
            print("A appelé", nom)
            return

    # if you tag this bot in any message
    if "<@!653563141002756106>" in MESSAGE:
        print(f">>({user.name} {time.asctime()}) - A ping le bot")
        user = str(message.author.nick)
        rep = [
            "ya quoi ?!",
            "Qu'est ce que tu as " + user + " ?",
            "Oui c'est moi",
            "Présent !",
            "*Oui ma bicheuh <3*",
            user + " lance un duel.",
            "Je t'aime.",
            "T'as pas d'amis ? trouduc",
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
        print(f">>({user.name} {time.asctime()}) - A généré une phrase aléatoire")
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
        print(f">>({user.name} {time.asctime()}) - A compter le nombe de mots du dico")
        text = f"J'ai actuellement {str(len(dicoLines))} mots enregistrés, nickel"
        await channel.send(text)

    # begginning of reaction programs, get inspired
    if not MESSAGE.startswith("--"):

        if "enerv" in MESSAGE or "énerv" in MESSAGE and rdnb >= 2:
            print(f">>({user.name} {time.asctime()}) - S'est enervé")
            await channel.send("(╯°□°）╯︵ ┻━┻")

        if "(╯°□°）╯︵ ┻━┻" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A balancé la table")
            await channel.send("┬─┬ ノ( ゜-゜ノ)")


        if (MESSAGE.startswith("tu sais") or MESSAGE.startswith("vous savez") or MESSAGE.startswith("savez vous")
            or MESSAGE.startswith("savez-vous") or MESSAGE.startswith("savais-tu") or MESSAGE.startswith("savais tu")) \
                and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé si on savait")
            reponses = [
                "J'en ai vraiment rien à faire tu sais ?",
                "Waaa... Je bois tes paroles",
                "Dis moi tout bg",
                "Balec",
                "M'en fous",
                "Plait-il ?",
            ]
            await channel.send(random.choice(reponses))


        if MESSAGE == "pas mal" and rdnb > 2:
            print(f">>({user.name} {time.asctime()}) - A trouvé ca pas mal")
            reponses = [
                "mouais",
                "peut mieux faire",
                "woaw",
                ":o"
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ez" or MESSAGE == "easy") and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - A trouvé ça facile")
            reponses = [
                "https://tenor.com/view/walking-dead-easy-easy-peasy-lemon-squeazy-gif-7268918",
                "https://tenor.com/view/pewds-pewdiepie-easy-ez-gif-9475407",
                "https://tenor.com/view/easy-red-easy-button-red-button-gif-4642542",
                "https://tenor.com/view/simple-easy-easy-game-easy-life-deal-with-it-gif-9276124"
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
            print(f">>({user.name} {time.asctime()}) - A parlé de bite")
            text = "8" + "=" * random.randint(0, int(
                today.strftime("%d"))) + "D"
            await channel.send(text)


        if MESSAGE.startswith("stop") or MESSAGE.startswith("arrête") or MESSAGE.startswith("arrete") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé d'arrêter")
            reponses = [
                "https://tenor.com/view/daddys-home2-daddys-home2gifs-stop-it-stop-that-i-mean-it-gif-9694318",
                "https://tenor.com/view/stop-sign-when-you-catch-feelings-note-to-self-stop-now-gif-4850841",
                "https://tenor.com/view/stop-it-get-some-help-gif-7929301"
            ]
            await channel.send(random.choice(reponses))


        if MESSAGE.startswith("exact") and rdnb > 2:
            print(f">>({user.name} {time.asctime()}) - A trouvé ça exacte")
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
            print(f">>({user.name} {time.asctime()}) - A envoyé de l'amour")
            reponses = [
                "Nique ta tante (pardon)",
                "<3",
                "luv luv",
                "moi aussi je t'aime ❤",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE in ["toi-même", "toi-meme", "toi même", "toi meme"]:
            print(f">>({user.name} {time.asctime()}) - A sorti sa meilleure répartie")
            reponses = [
                "Je ne vous permet pas",
                "Miroir magique",
                "C'est celui qui dit qui l'est",
            ]
            await channel.send(random.choice(reponses))

        if "<@!747066145550368789>" in message.content:
            print(f">>({user.name} {time.asctime()}) - A parlé du grand bot")
            reponses = [
                "bae",
                "Ah oui, cette sous-race de <@!747066145550368789>",
                "il a moins de bits que moi",
                "son pere est un con",
                "ca se dit grand mais tout le monde sait que....",
            ]
            await channel.send(random.choice(reponses))

        if "❤" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A envoyé du love")
            await message.add_reaction("❤")

        if (MESSAGE.startswith("hein") or MESSAGE.startswith("1")) and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A commencé par 1", end="")
            reponses = [
                "deux",
                "2",
                "deux ?",
                "2 😏"
            ]
            await channel.send(random.choice(reponses))

            # waits for a message valiudating further instructions
            def check(m):
                return ("3" in m.content or "trois" in m.content) and m.channel == message.channel and not m.startswith(
                    "http")

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
                print(f">>({user.name} {time.asctime()}) - A pas su compter")
            else:
                print(f">>({user.name} {time.asctime()}) - A su compter")
                reponses = [
                    "BRAVO TU SAIS COMPTER !",
                    "SOLEIL !",
                    "4, 5, 6, 7.... oh et puis merde",
                    "HAHAHAHAH non.",
                    "stop.",
                ]
                await channel.send(random.choice(reponses))

        if MESSAGE == "a" and rdnb > 2:
            print(f">>({user.name} {time.asctime()}) - A commencer par a", end="")

            def check(m):
                return m.content.lower() == "b" and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
                print(f">>({user.name} {time.asctime()}) - A pas continué par b")
            else:
                print(f">>({user.name} {time.asctime()}) - A connait son alphabet")
                await channel.send("A B C GNEU GNEU MARRANT TROU DU CUL !!!")

        if MESSAGE == "ah" and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - ", end="")
            if rdnb >= 4:
                print("S'est fait Oh/Bh")
                reponses = ["Oh", "Bh"]
                await channel.send(random.choice(reponses))
            else:
                print("S'est fait répondre avec le dico (ah)")
                await channel.send(finndAndReplace("a", dicoLines))

        if MESSAGE == "oh" and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - ", end="")
            if rdnb >= 4:
                print("S'est fait répondre (oh)")
                reponses = ["Quoi ?",
                            "p",
                            "ah",
                            ":o",
                            "https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif"
                            ]
                await channel.send(random.choice(reponses))
            else:
                print("S'est fait répondre par le dico (oh)")
                await channel.send(finndAndReplace("o", dicoLines))

        if MESSAGE == "eh" and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - ", end="")
            if rdnb >= 4:
                print("S'est fait répondre (eh)")
                reponses = ["hehehehehe", "oh", "Du calme."]
                await channel.send(random.choice(reponses))
            else:
                print("S'est fait répondre par le dico (eh)")
                await channel.send(finndAndReplace("é", dicoLines))

        if MESSAGE.startswith("merci"):
            print(f">>({user.name} {time.asctime()}) - A dit merci")
            if rdnb >= 3:
                reponses = [
                    "De rien hehe",
                    "C'est normal t'inquiète",
                    "Je veux le cul d'la crémière avec.",
                    "non.",
                    "Excuse toi non ?",
                    "Au plaisir",
                ]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("🥰")

        if MESSAGE == "skusku" or MESSAGE == "sku sku":
            print(f">>({user.name} {time.asctime()}) - A demandé qui jouait")
            await channel.send("KICÉKIJOUE ????")

        if ("😢" in MESSAGE or "😭" in MESSAGE) and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - A chialé")
            reponses = [
                "cheh",
                "dur dur",
                "dommage mon p'tit pote",
                "balec",
                "tant pis",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("tu veux") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé si on voulait")
            reponses = [
                "Ouais gros",
                "Carrément ma poule",
                "Mais jamais tes fou ptdr",
                "Oui.",
            ]
            await channel.send(random.choice(reponses))


        if MESSAGE.startswith("quoi") and rdnb > 2:
            print(f">>({user.name} {time.asctime()}) - A demandé quoi")
            reponses = [
                "feur",
                "hein ?",
                "nan laisse",
                "oublie",
                "rien",
                "😯"
            ]

            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("pourquoi") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé pourquoi")
            reponses = [
                "PARCEQUEEEE",
                "Aucune idée.",
                "Demande au voisin",
                "Pourquoi tu demandes ça ?",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE in [

            "facepalm",
            "damn",
            "fait chier",
            "fais chier",
            "ptn",
            "putain"]
            or MESSAGE.startswith("pff") or MESSAGE.startswith("no..")) \
                and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A gifé Conteville")

            await channel.send(
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif"
            )

        if (MESSAGE.startswith("t'es sur") or MESSAGE.startswith("t sur")) and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé si on était sur")
            reponses = [
                "Ouais gros",
                "Nan pas du tout",
                "Qui ne tente rien...",
                "haha 👀",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE.startswith("ah ouais") or MESSAGE.startswith("ah bon")) and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - S'est intérrogé de la véracité du dernier propos")
            reponses = [
                "Ouais gros", "Nan ptdr", "Je sais pas écoute...", "tg"
            ]
            await channel.send(random.choice(reponses))


        if MESSAGE.startswith("au pied") and message.author.id == 359743894042443776:
            print(f">>({user.name} {time.asctime()}) - Le maitre m'a appelé")

            reponses = [
                "wouf wouf",
                "Maître ?",
                "*s'agenouille*\nComment puis-je vous être utile ?",
                "*Nous vous devons une reconnaissance éternelllllllle*",
            ]
            await channel.send(random.choice(reponses))

        if "<@!761898936364695573>" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A parlé de mon pote")
            await channel.send("Tu parles comment de mon pote là ?")

        if "tg" in MESSAGE:

            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "t"
                        and MESSAGE[i + 2] == "g" and MESSAGE[i + 3] == " "):
                    nbtg += 1
                    tgFile = open("txt/tg.txt", "w+")
                    tgFile.write(str(nbtg))
                    tgFile.close()
                    activity = f"insulter {nbtg} personnes"
                    await bot.change_presence(activity=discord.Game(
                        name=activity))
                    await channel.send(random.choice(insultes))
                    if rdnb >= 4:
                        await message.add_reaction('🇹')
                        await message.add_reaction('🇬')
                    print(f">>({user.name} {time.asctime()}) - A insulté")


        if MESSAGE == "cheh" or MESSAGE == "sheh":
            print(f">>({user.name} {time.asctime()}) - A dit cheh")
            if rdnb >= 3:
                reponses = [
                    "Oh tu t'excuses", "Cheh", "C'est pas gentil ça", "🙁"
                ]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("😉")

        if MESSAGE.startswith("non") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A dit non")
            reponses = [
                "si.",
                "ah bah ca c'est sur",
                "SÉRIEUX ??",
                "logique aussi",
                "jure ?",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("lequel") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé lequel")
            reponses = [
                "Le deuxième",
                "Le prochain",
                "Aucun"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("laquelle") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé laquelle")
            reponses = [
                "La deuxième",
                "La prochaine",
                "Aucune"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("miroir magique"):
            print(f">>({user.name} {time.asctime()}) - A sorti une répartie de maternelle")
            await channel.send(MESSAGE)

        if MESSAGE.startswith("jure") and rdnb > 4:
            print(f">>({user.name} {time.asctime()}) - A demandé de jurer")
            if "wola" in MESSAGE:
                await channel.send("Wola")
            elif "wallah" in MESSAGE:
                await channel.send("Wallah")
            else:
                rep = await channel.send(
                    "Je jure de dire la vérité, uniquement la vérité et toute la vérité"
                )
                if rdnb >= 4:
                    await rep.add_reaction("🤞")

        if "☹" in MESSAGE or "😞" in MESSAGE or "😦" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A chialé")
            await message.add_reaction("🥰")

        if MESSAGE == "f" or MESSAGE == "rip":
            print(f">>({user.name} {time.asctime()}) - Payed respect")
            await channel.send(
                "#####\n#\n#\n####\n#\n#\n#       to pay respect")

        if ("quentin" in MESSAGE or "quent1" in MESSAGE) and rdnb >= 4:
            print(f">>({user.name} {time.asctime()}) - A parlé de mon maitre")
            await channel.send("Papa ! 🤗")

        if MESSAGE.startswith("god"):
            print(f">>({user.name} {time.asctime()}) - ", end="")
            day = today.strftime("%d")
            month = today.strftime("%m")
            MESSAGE = MESSAGE.replace("god", "")
            userID = ""
            if "<@!" not in MESSAGE:
                userID = int(user.id)
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
                print("N'est pas dieu aujourd'hui")
                return
            user = await message.guild.fetch_member(userID)
            pfp = user.avatar_url
            gods = [
                ["https://tse4.mm.bing.net/th?id=OIP.IXAIL06o83HxXHGjKHqZMAHaKe&pid=Api", "Loki"],
                ["https://www.wallpaperflare.com/static/810/148/1018/painting-vikings-odin-gungnir-wallpaper.jpg",
                 "Odin"],
                ["https://tse3.mm.bing.net/th?id=OIP.3NR2eZEBm46mrcFM_p14RgHaJ3&pid=Api", "Osiris"],
                ["https://tse1.explicit.bing.net/th?id=OIP.KXfuA_jDa_cfDkrMInOMfQHaJq&pid=Api", "Shiva"],
                ["https://tse2.mm.bing.net/th?id=OIP.BYG-Xfgo4To4PJaY32Gj0gHaKD&pid=Api", "Poseidon"],
                ["https://tse1.mm.bing.net/th?id=OIP.M6A5OIYcaUO5UUrUjVRn5wHaNK&pid=Api", "Arceus"],
                ["https://tse3.mm.bing.net/th?id=OIP.M2w0Dn5HK19lF68UcicLUwHaMv&pid=Api", "Anubis"],
                ["https://tse2.mm.bing.net/th?id=OIP.pVKMpFtFLRjIpAEsPMafJgAAAA&pid=Api", "Tezcatlipoca"],
                ["https://tse2.mm.bing.net/th?id=OIP.8hT9rmQRFhGa11CTdXXPQAHaJ6&pid=Api", "Venus"]
            ]
            embed = discord.Embed(
                title="This is God",
                description="<@%s> is that god." % userID,
                color=0xECCE8B,
                url=random.choice([
                    "https://media.giphy.com/media/USm8tJQzgDAAKJRKkk/giphy.gif",
                    "https://media.giphy.com/media/ZArMUnViJtKaBH0XLg/giphy.gif",
                    "https://tenor.com/view/bruce-almighty-morgan-freeman-i-am-god-hello-hey-gif-4743445"
                ])
            )
            god = gods[((userID // 365 + int(day) * 5) // int(month)) % len(gods)]
            embed.set_thumbnail(url=pfp)
            embed.set_author(name="Le p'tit god", url="https://github.com/NozyZy/Le-ptit-bot",
                             icon_url="https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png")
            embed.set_image(url=god[0])
            embed.set_footer(text=god[1])
            print("Est un dieu aujourd'hui : ", god[1])
            await channel.send("God looks like him.", embed=embed)

        if MESSAGE.startswith("hello") and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - A dit hello")
            await channel.send(file=discord.File("images/helo.jpg"))

        if (MESSAGE == "enculé" or MESSAGE == "enculer") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demander d'aller se faire enculer")
            image = ["images/tellermeme.png", "images/bigard.jpeg"]
            await channel.send(file=discord.File(random.choice(image)))

        if MESSAGE == "stonks":
            print(f">>({user.name} {time.asctime()}) - Stonked")
            await channel.send(file=discord.File("images/stonks.png"))

        if (MESSAGE == "parfait" or MESSAGE == "perfection") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - Perfection")
            await channel.send(file=discord.File("images/perfection.jpg"))

        if MESSAGE.startswith("leeroy"):
            print(f">>({user.name} {time.asctime()}) - LEEROOOOOOOOOOYY")
            await channel.send(file=discord.File("sounds/Leeroy Jenkins.mp3"))

        if "pute" in MESSAGE and rdnb > 4:
            print(f">>({user.name} {time.asctime()}) - Le pute")
            reponses = [
                "https://tenor.com/view/mom-gif-10756105",
                "https://tenor.com/view/wiener-sausages-hotdogs-gif-5295979",
                "https://i.ytimg.com/vi/3HZ0lvpdw6A/maxresdefault.jpg",
            ]
            await channel.send(random.choice(reponses))

        if "guillotine" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - Le guillotine")
            reponses = [
                "https://tenor.com/view/guillatene-behead-lego-gif-12352396",
                "https://tenor.com/view/guillotine-gulp-worried-scared-slug-riot-gif-11539046",
                "https://tenor.com/view/revolution-guillotine-marie-antoinette-off-with-their-heads-behead-gif-12604431",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ouh" or MESSAGE == "oh.") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - 'OUH.', by Velikson")
            await channel.send("https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif")

        if "pd" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A parlé de pd")
            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "p"
                        and MESSAGE[i + 2] == "d" and MESSAGE[i + 3] == " "):
                    await channel.send(file=discord.File("images/pd.jpg"))

        if "oof" in MESSAGE and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - oof")
            reponses = [
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif",
                "https://tenor.com/view/oh-snap-surprise-shocked-johncena-gif-5026702",
                "https://tenor.com/view/oof-damn-wow-ow-size-gif-16490485",
                "https://tenor.com/view/oof-simpsons-gif-14031953",
                "https://tenor.com/view/yikes-michael-scott-the-office-my-bad-oof-gif-13450971",
            ]
            await channel.send(random.choice(reponses))

        if ("money" in MESSAGE or "argent" in MESSAGE) and rdnb >= 4:
            print(f">>({user.name} {time.asctime()}) - Money bitch")
            reponses = [
                "https://tenor.com/view/6m-rain-wallstreet-makeitrain-gif-8203989",
                "https://tenor.com/view/money-makeitrain-rain-guap-dollar-gif-7391084",
                "https://tenor.com/view/taka-money-gif-10114852",
            ]
            await channel.send(random.choice(reponses))

    # teh help command, add commands call, but not reactions
    if MESSAGE == "--help":
        print(f">>({user.name} {time.asctime()}) - A demandé de l'aide")
        await channel.send(
            "Commandes : \n"
            " **F** to pay respect\n"
            " **--serverInfo** pour connaître les infos du server\n"
            " **--clear** *nb* pour supprimer *nb* messages\n"
            " **--addInsult** pour ajouter des insultes et **tg** pour te faire insulter\n"
            " **--game** pour jouer au jeu du **clap**\n"
            " **--presentation** et **--master** pour créer des memes\n"
            " **--repeat** pour que je répète ce qui vient après l'espace\n"
            " **--appel** puis le pseudo de ton pote pour l'appeler (admin only)\n"
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
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de clear {nombre} messages dans le channel {ctx.channel.name} du serveur {ctx.guild.name}")
    messages = await ctx.channel.history(limit=nombre + 1).flatten()
    for message in messages:
        await message.delete()


@bot.command()  # repeat the 'text', and delete the original message
async def repeat(ctx, *text):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé de répéter {' '.join(text)} messages")
    messages = await ctx.channel.history(limit=1).flatten()
    for message in messages:
        await message.delete()
    await ctx.send(" ".join(text))


@bot.command()  # show the number of people in the server, and its name
async def serverinfo(ctx):
    server = ctx.guild
    nbUsers = server.member_count
    text = f"Le serveur **{server.name}** contient **{nbUsers}** personnes !"
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé les infos du serveur {server.name}")
    await ctx.send(text)


@bot.command()  # send the 26 possibilites of a ceasar un/decryption
async def crypt(ctx, *text):
    mot = " ".join(text)
    messages = await ctx.channel.history(limit=1).flatten()
    for message in messages:
        await message.delete()
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé de crypter {mot} en {crypting(mot)}")
    await ctx.send(f"||{mot}|| :\n" + crypting(mot))


@bot.command()  # send a random integer between two numbers, or 1 and 0
async def randint(ctx, *text):
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
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
        print("A demandé un nombre aléatoire sans donner d'encadrement")
        return

    nb1 = strToInt(tab)

    if i != len(MESSAGE):
        nb2 = strToInt(list=nbInStr(MESSAGE, i, len(MESSAGE)))

    if nb1 == nb2:
        text = f"Bah {str(nb1)} du coup... 🙄"
        await ctx.send(text)
        print(f"A demandé le nombre {nb1}")
        return
    if nb2 < nb1:
        temp = nb2
        nb2 = nb1
        nb1 = temp

    rd = random.randint(nb1, nb2)
    print(f"A généré un nombre aléatoire [|{nb1}:{nb2}|] = {rd}")
    await ctx.send(rd)


@bot.command()  # send a random word from the dico, the first to write it wins
async def game(ctx):
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
    dicoFile = open("txt/dico.txt", "r+")
    dicoLines = dicoFile.readlines()
    dicoFile.close()

    mot = random.choice(dicoLines)
    mot = mot.replace("\n", "")
    text = f"Le premier à écrire **{mot}** a gagné"
    print(f"A joué au jeu en devinant {mot}, ", end="")
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
        user = str(msg.author.nick)
        text = f"**{user}** a gagné !"
        print(f"{user} a gagné")
        await ctx.send(text)


@bot.command(
)  # do a simple calcul of 2 numbers and 1 operator (or a fractionnal)
async def calcul(ctx, *text):
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
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
        print("A demandé de calculer l'infini")
        return

    while i < len(Message) and 48 <= ord(Message[i]) <= 57:
        if 48 <= ord(Message[i]) <= 57:
            tab.append(Message[i])
        i += 1

    if len(tab) == 0:
        await ctx.send("Rentre un nombre banane")
        print("A demandé de calculer sans rentrer de nombre")
        return

    if i == len(Message) or Message[i] not in symbols:
        await ctx.send("Rentre un symbole (+, -, *, /, ^, !)")
        print("A demandé de calculer sans rentrer de symbole")
        return

    symb = Message[i]

    nb1 = strToInt(tab)

    if symb == "!":
        if nb1 > 806:  # can't go above 806 recursion deepth
            await ctx.send("806! maximum, désolé 🤷‍♂️")
            print("A demandé de calculer plus de 806! (erreur récursive)")
            return
        rd = facto(nb1)
        text = str(nb1) + "! =" + str(rd)
        await ctx.send(text)
        print(f"A demandé de calculer {text}")
        return

    if i != len(Message):
        tab = nbInStr(Message, i, len(Message))

        if len(tab) == 0:
            await ctx.send("Rentre un deuxième nombre patate")
            print("A demandé de calculer sans reentrer de deuxième nombre")
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
            print("A demandé de calculer une division par 0 (le con)")
            return
        rd = float(nb1 / nb2)
    elif symb == "^":
        rd = nb1**nb2
    text = str(nb1) + str(symb) + str(nb2) + "=" + str(rd)
    print(text)
    print(f"A demandé de calculer {text}")
    await ctx.send(text)


@bot.command(
)  # create a reaction poll with a question, and max 10 propositions
async def poll(ctx, *text):
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
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
        print("A demandé un poll sans choix")
        return
    if len(tab) > 11:
        await ctx.send("Ca commence à faire beaucoup non ?... 10 max ca suffit"
                       )
        print("A demandé un poll e plus de 10 choix")
        return
    text = ""
    print("A demandé un poll avec : ", end="")
    for i in range(len(tab)):
        print(tab[i], sep=" - ")
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


@bot.command(
)  # find and send all the prime numbers until 14064991, can calcul above but can't send it (8Mb limit)
async def prime(ctx, nb: int):
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
    if nb < 2:
        await ctx.send("Tu sais ce que ca veut dire 'prime number' ?")
        print("A demandé de calculer des nombre premier sen dessous de 2")
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
        await ctx.send(text,
                       file=discord.File("txt/prime.txt"))
    print(f"A demandé de claculer tous les nombres premiers juqu'à {nb}")


@bot.command()  # find if 'nb' is a prime number, reacts to the message
async def isPrime(ctx, nb: int):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé si {nb} est premier : ", end="")
    if is_prime(nb):
        await ctx.message.add_reaction("👍")
        print("oui")
    else:
        await ctx.message.add_reaction("👎")
        print("non")


@bot.command()  # send 'nb' random words of the dico, can repeat itself
async def randomWord(ctx, nb: int):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé {nb} mots aléatoires dans le dico : ", end="")
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
    print(text)
    await ctx.send(text)


@bot.command()  # join the vocal channel fo the caller
async def join(ctx):
    channel = ctx.author.voice.channel
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je rejoigne le vocal {channel} du serveur {ctx.guild.name}")
    await channel.connect()


@bot.command()  # leaves it
async def leave(ctx):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je quitte le vocal {ctx.author.voice.channel} du serveur {ctx.guild.name}")
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
            before_options=
            "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
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
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je traduise {toTranslate} en {fromLang} vers {toLang} : {text}")
    await ctx.send(text)


@bot.command()
async def master(ctx, *text):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé un meme master ", end="")
    text = " ".join(text)
    if not len(text) or text.count(",") != 2:
        text = ["add 3", "f*cking terms", "splited by ,"]
    else:
        text = text.split(",")
        for term in text:
            if len(term) not in range(1, 20):
                text = ["add terms", "between", "1 and 20 chars"]
                break
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
    print(f"avec le texte : {text}")
    img.save("images/mastermeme.jpg")
    await ctx.send(file=discord.File("images/mastermeme.jpg"))


@bot.command()
async def presentation(ctx, *base):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé un meme presentation ", end="")
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
    print(f"avec le texte : {text}")
    await ctx.send(file=discord.File("images/presentationmeme.png"))


@bot.command()
async def ban(ctx):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de me bannir du channel {ctx.channel.name} du serveur {ctx.guild.name} : ",
        end="")
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("T'es pas admin, nananananère 😜")
        print("mais n'a pas les droits")
        return
    bansFile = open("txt/bans.txt", "r+")
    bansLines = bansFile.readlines()
    bansFile.close()
    chanID = str(ctx.channel.id) + "\n"
    if chanID in bansLines:
        await ctx.send("Jsuis déjà ban, du calme...")
        print("mais j'étais déjà ban (sad)")
    else:
        bansFile = open("txt/bans.txt", "a+")
        bansFile.write(chanID)
        bansFile.close()
        await ctx.send("D'accord, j'arrete de vous embeter ici... mais les commandes sont toujours dispos")
        print("et je suis ban")



@bot.command()
async def unban(ctx):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de me débannir du channel {ctx.channel.name} du serveur {ctx.guild.name} : ",
        end="")
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("T'es pas admin, nananananère 😜")
        print("mais n'a pas les droits")
        return
    bansFile = open("txt/bans.txt", "r+")
    bansLines = bansFile.readlines()
    bansFile.close()
    chanID = str(ctx.channel.id) + "\n"
    if chanID not in bansLines:
        await ctx.send("D'accord, mais j'suis pas ban, hehe.")
        print("mais j'étais pas ban")
    else:
        bansFile = open("txt/bans.txt", "w+")
        bansFile.write("")
        bansFile.close()
        bansFile = open("txt/bans.txt", "a+")
        for id in bansLines:
            if id == chanID:
                bansLines.remove(id)
                await ctx.send("JE SUIS LIIIIIIBRE")
                print("et je suis libre (oui!)")
            else:
                bansFile.write(id)
        bansFile.close()


@bot.command()
async def invite(ctx):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé une invitation dans le serveur {ctx.guild.name}")
    await ctx.send(
        "Invitez-moi 🥵 !\n"
        "https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8"
    )


"""
@bot.command()
async def say(ctx, number, *text):
    for i in range(int(number)):
        await ctx.send(" ".join(text))
"""


@bot.command()  # PERSONAL USE ONLY
async def amongus(ctx):
    print(f">>({ctx.author.name} {time.asctime()}) - A demandé une game Among Us {ctx.guild.name}")

    def equal_games(liste):
        # Il vaut mieux que la liste soit déjà mélangée, mais on peut le faire ici aussi.
        # Le programme renvoie une liste 2D composant les équipes

        tailleListe = len(liste)
        tailleMin, tailleMax = 5, 10
        tailleEquip = []
        nbEquip = 0
        equip = []

        for i in range(tailleMax, tailleMin, -1):
            if tailleListe % i == 0:
                nbEquip = tailleListe // i
                for _ in range(nbEquip):
                    tailleEquip.append(i)
                break
            elif tailleListe % i == 1 and i < tailleMax:
                nbEquip = tailleListe // i
                for j in range(nbEquip):
                    if j == 0:
                        tailleEquip.append(i + 1)
                    else:
                        tailleEquip.append(i)
                break

        if nbEquip == 0:
            tailleEquip.append(tailleMax)
            while tailleListe > 0 and tailleMin < tailleEquip[0] and nbEquip < 8:
                tailleListe -= tailleEquip[0]
                nbEquip += 1

                if 0 < tailleListe < tailleMin and nbEquip < 8:
                    tailleEquip[0] -= 1
                    tailleListe = len(liste)
                    nbEquip = 0

            for i in range(1, nbEquip):
                tailleEquip.append(tailleEquip[0])

        j = 0
        for i in range(nbEquip):
            list1 = []
            for _ in range(tailleEquip[i]):
                if j < len(liste):
                    list1.append(liste[j])
                    j += 1
            equip.append(list1)
        return equip

    tour = 0
    while 1:
        tour += 1
        message = "Réagis avec ✅ pour jouer !"
        totalTime = 60
        timeLeft = totalTime
        firstMessage = await ctx.send(f"Réagis avec ✅ pour jouer ! Il reste {timeLeft} sec")

        yes = "✅"

        await firstMessage.add_reaction(yes)

        for _ in range(totalTime):
            time.sleep(1)
            timeLeft -= 1
            await firstMessage.edit(content=message + f" Il reste {str(timeLeft)} sec")
        await firstMessage.edit(content="Inscriptions fermées !")

        firstMessage = await firstMessage.channel.fetch_message(firstMessage.id
                                                                )
        users = set()
        for reaction in firstMessage.reactions:

            if str(reaction.emoji) == yes:
                async for user in reaction.users():
                    users.add(user)

        ids = [i for i in range(23)]
        for user in users:
            if user.id != bot.user.id:
                ids.append(user.id)
        random.shuffle(ids)
        if len(ids) < 5:
            if len(ids) == 0:
                await firstMessage.add_reaction("😭")
                await firstMessage.add_reaction("💔")
                await firstMessage.add_reaction("😢")
            else:
                await ctx.send("En dessous de 5 joueurs on va avoir du mal...")
        else:
            playersID = equal_games(ids)
            color = [
                0x0000FF,
                0x740001,
                0x458B74,
                0x18EEFF,
                0xEAE4D3,
                0xFF8100,
                0x9098FF,
                0xFF90FA,
                0xFF1443,
                0xFF1414,
                0x7FFFD4,
                0x05FF3C,
                0x05FFA1,
            ]
            text = f"**Partie n°{str(tour)} ---- {len(ids)} joueurs**"
            await ctx.send(text)
            for i in range(len(playersID)):
                y = 0
                embed = discord.Embed(title=f"**Equipe n°{str(i + 1)}**",
                                      color=random.choice(color))
                embed.set_thumbnail(

                    url="https://tse1.mm.bing.net/th?id=OIP.3WhrRCJd4_GTM2VaWSC4SAAAAA&pid=Api")

                for user in playersID[i]:
                    y += 1
                    embed.add_field(name=f"Joueur {str(y)}",
                                    value=f"<@!{str(user)}>",
                                    inline=True)
                await ctx.send(embed=embed)
            await ctx.send("**NEXT** pour relancer\n**END** poure terminer")

        def check(m):
            id_list = [321216514986606592, 359743894042443776,
                       135784465065574401, 349548485797871617]
            return (m.content == "NEXT" or m.content == "END") and m.channel == ctx.channel and m.author.id in id_list

        try:
            if len(ids) == 0:
                msg = await bot.wait_for('message',
                                         timeout=60.0,
                                         check=check)
            else:
                msg = await bot.wait_for('message',

                                         timeout=3600.0,
                                         check=check)
            if msg.content == "END":
                await ctx.send("**Fin de la partie...**")
                break
        except asyncio.TimeoutError:
            await ctx.send("**Fin de la partie...**")
            break
    print(f">>({ctx.author.name} {time.asctime()}) - La game Among Us a prit fin {ctx.guild.name}")


@bot.command()
async def puissance4(ctx):
    print(f">>({ctx.author.name} {time.asctime()}) - A lancé une partie de puissance 4 {ctx.guild.name}")
    grid = [[0 for _ in range(7)] for _ in range(6)]
    """grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 1, 0, 0],
            [0, 0, 0, 2, 2, 1, 0],
            [0, 0, 0, 2, 2, 2, 1]]"""

    async def updateGrid(grid, text, message):
        text += "\n" + "".join(numbers) + "\n"
        print("\n")
        for row in grid:
            print(row)
            for case in row:
                if case == 0:
                    text += "🔵"
                elif case == 1:
                    text += "🔴"
                elif case == 2:
                    text += "🟡"
                else:
                    print("ERROR - ", case, row)
            text += "\n"
        await message.edit(content=text)

        return gridMessage

    async def addChip(grid, col, tour):
        i = 5
        while i >= 0:
            if grid[i][col] != 0:
                i -= 1
            else:
                grid[i][col] = tour % 2 + 1
                if i == 0:
                    await gridMessage.remove_reaction(str(numbers[col]), bot.user)
                    numbers[col] = "#️⃣"
                break
        return i >= 0

    async def checkWin(grid, tour):
        for row in range(len(grid) - 1, -1, -1):
            for col in range(0, len(grid[row])):
                if await checkRight(grid, row, col, 0, tour) \
                        or await checkLeft(grid, row, col, 0, tour) \
                        or await checkUp(grid, row, col, 0, tour) \
                        or await checkLeftDiag(grid, row, col, 0, tour) \
                        or await checkRightDiag(grid, row, col, 0, tour):
                    return True
        return False

    async def checkRight(grid, row, col, size, tour):
        if size >= 4:
            return True
        if row >= len(grid) or col >= len(grid[row]) or row < 0 or col < 0:
            return False
        if grid[row][col] != tour % 2 + 1:
            return False
        return await checkRight(grid, row, col + 1, size + 1, tour)

    async def checkLeft(grid, row, col, size, tour):
        if size >= 4:
            return True
        if row >= len(grid) or col >= len(grid[row]) or row < 0 or col < 0:
            return False
        if grid[row][col] != tour % 2 + 1:
            return False
        return await checkLeft(grid, row, col - 1, size + 1, tour)

    async def checkUp(grid, row, col, size, tour):
        if size >= 4:
            return True
        if row >= len(grid) or col >= len(grid[row]) or row < 0 or col < 0:
            return False
        if grid[row][col] != tour % 2 + 1:
            return False
        return await checkUp(grid, row - 1, col, size + 1, tour)

    async def checkRightDiag(grid, row, col, size, tour):
        if size >= 4:
            return True
        if row >= len(grid) or col >= len(grid[row]) or row < 0 or col < 0:
            return False
        if grid[row][col] != tour % 2 + 1:
            return False
        return await checkRightDiag(grid, row - 1, col + 1, size + 1, tour)

    async def checkLeftDiag(grid, row, col, size, tour):
        if size >= 4:
            return True
        if row >= len(grid) or col >= len(grid[row]) or row < 0 or col < 0:
            return False
        if grid[row][col] != tour % 2 + 1:
            return False
        return await checkLeftDiag(grid, row - 1, col - 1, size + 1, tour)

    tour = 1
    red = ""
    yellow = ""
    end = False
    numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]

    yellowMessage = await ctx.send("**⬇ Joueur jaune ⬇**")
    await yellowMessage.add_reaction("🟡")

    def check(reaction, user):
        return user != bot.user and str(reaction.emoji) == "🟡"

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
        yellow = user
    except asyncio.TimeoutError:
        await yellowMessage.edit(content="Pas de joueur jaune ❌")
        return
    print(f">>({yellow} {time.asctime()}) - Est le joueur jaune {ctx.guild.name}")

    redMessage = await ctx.send("**⬇ Joueur rouge ⬇**")
    await redMessage.add_reaction("🔴")

    def check(reaction, user):
        return user != bot.user and user != yellow and str(reaction.emoji) == "🔴"

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
        red = user
    except asyncio.TimeoutError:
        await redMessage.edit(content="Pas de joueur rouge ❌")
        return
    print(f">>({red} {time.asctime()}) - Est le joueur red {ctx.guild.name}")

    yellowPing = "<@!" + str(yellow.id) + "> 🟡"
    redPing = "<@!" + str(red.id) + "> 🔴"

    text = yellowPing + " et " + redPing + " tenez vous prêts !"
    gridMessage = await ctx.send(text)

    time.sleep(5)

    while not end:
        if tour == 1:
            text = "Tour n°" + str(tour) + " - " + yellowPing + "\n\n"
            text += "".join(numbers) + "\n"
            for row in grid:
                for case in row:
                    if case == 0:
                        text += "🔵"
                    elif case == 1:
                        text += "🔴"
                    elif case == 2:
                        text += "🟡"
                    else:
                        print("ERROR - ", case, row)
                text += "\n"
            await gridMessage.edit(content=text)
            await gridMessage.add_reaction("1️⃣")
            await gridMessage.add_reaction("2️⃣")
            await gridMessage.add_reaction("3️⃣")
            await gridMessage.add_reaction("4️⃣")
            await gridMessage.add_reaction("5️⃣")
            await gridMessage.add_reaction("6️⃣")
            await gridMessage.add_reaction("7️⃣")
        elif tour % 2 == 0:
            await updateGrid(grid, "Tour n°" + str(tour) + " - " + redPing + "\n", gridMessage)
        else:
            await updateGrid(grid, "Tour n°" + str(tour) + " - " + yellowPing + "\n", gridMessage)

        if tour % 2 == 0:
            def check(reaction, user):
                return user == red and str(reaction.emoji) in numbers
        else:
            def check(reaction, user):
                return user == yellow and str(reaction.emoji) in numbers

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)

            await gridMessage.remove_reaction(reaction, user)

            for i in range(len(numbers)):
                if str(reaction.emoji) == numbers[i]:
                    await addChip(grid, i, tour)

            if tour > 6 and await checkWin(grid, tour):
                if tour % 2 == 0:
                    print(f">>({red} {time.asctime()}) - Est le gagnant ! {ctx.guild.name}")
                    await addScoreLeaderboard(red.id, red)
                    await updateGrid(grid, "Tour n°" + str(tour) + " - " + redPing + "\n", gridMessage)
                    text = redPing + " gagne ! **Score actuel : " + await getScoreLeaderBoard(
                        red.id) + " victoires** - " \
                           + await getPlaceLeaderbord(red.id)
                else:
                    print(f">>({yellow} {time.asctime()}) - Est le gagnant ! {ctx.guild.name}")
                    await addScoreLeaderboard(yellow.id, yellow)
                    await updateGrid(grid, "Tour n°" + str(tour) + " - " + yellowPing + "\n", gridMessage)
                    text = yellowPing + " gagne ! **Score actuel : " + await getScoreLeaderBoard(
                        yellow.id) + " victoires** - " \
                           + await getPlaceLeaderbord(yellow.id)
                await ctx.send(text)
                end = True

            elif tour >= 42:
                await addScoreLeaderboard(yellow.id, yellow)
                await addScoreLeaderboard(red.id, red)
                print(f">>({red} et {yellow} {time.asctime()}) - Sont à égalité ! {ctx.guild.name}")
                text = "Bravo à vous deux, c'est une égalité ! Bien que rare, ça arrive... Donc une victoire en plus chacun ! gg\n" \
                       "**Score de " + yellowPing + " : " + await getScoreLeaderBoard(yellow.id) + " victoires !**\n" \
                       "**Score de " + redPing + " : " + await getScoreLeaderBoard(red.id) + " victoires !**"
                await ctx.send(text)
                end = True

        except asyncio.TimeoutError:
            await gridMessage.add_reaction("❌")
            await gridMessage.add_reaction("⌛")
            if tour % 2 == 0:
                print(f">>({yellow} {time.asctime()}) - Est le gagnant ! {ctx.guild.name}")
                await updateGrid(grid, "Tour n°" + str(tour) + " - " + redPing + "\n", gridMessage)
                await addScoreLeaderboard(yellow.id, yellow)
                text = redPing + " n'a pas joué ! Alors **" + yellowPing + " gagne !** (c'est le jeu ma pov lucette)\n" \
                                                                           "Score actuel : " + await getScoreLeaderBoard(
                    yellow.id) + \
                       " victoires - " + await getPlaceLeaderbord(yellow.id)
            else:
                print(f">>({red} {time.asctime()}) - Est le gagnant ! {ctx.guild.name}")
                await updateGrid(grid, "Tour n°" + str(tour) + " - " + redPing + "\n", gridMessage)
                await addScoreLeaderboard(red.id, red)
                text = yellowPing + " n'a pas joué ! Alors **" + redPing + " gagne !** (fallait jouer, 2 min t'es large !)\n " \
                                                                           "Score actuel : " + await getScoreLeaderBoard(
                    red.id) + \
                       " victoires - " + await getPlaceLeaderbord(red.id)
            await ctx.send(text)
            end = True

        tour += 1


@bot.command()
async def p4(ctx):
    await puissance4(ctx)


async def updateLeaderboard(liste):
    file = open("txt/leaderboard.txt", "w+")
    for line in liste:
        line = "-".join(line)
        if line[len(line) - 1] != "\n":
            line += "\n"
        file.write(line)
    file.close()


async def getScoreLeaderBoard(id):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        if str(id) in leaderboard[i]:
            leaderboard[i] = leaderboard[i].split("-")
            return leaderboard[i][1].replace("\n", "")


async def getPlaceLeaderbord(id):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        if str(id) in leaderboard[i]:
            i += 1
            if i == 1:
                return "1er/" + str(len(leaderboard))
            else:
                return str(i) + "e/" + str(len(leaderboard))


async def addScoreLeaderboard(id, name):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    isIn = False
    for i in range(len(leaderboard)):
        leaderboard[i] = leaderboard[i].split("-")
        if str(id) in leaderboard[i]:
            isIn = True
            leaderboard[i][1] = str(int(leaderboard[i][1]) + 1)
    if not isIn:
        line = (str(id) + "-1-" + str(name) + "\n").split("-")
        leaderboard.append(line)

    leaderboard.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard)


@bot.command()
async def classement(ctx):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()

    numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "Le classement du puissance 4 est composé de : \n\n"
    if len(leaderboard) <= 10:
        if len(leaderboard) <= 0:
            text = "Bah ya personne... ***jouez !***"
        else:
            for i in range(len(leaderboard)):
                name = leaderboard[i].split("-")
                text += numbers[i] + " : **" + name[2].replace("\n", "") + "** avec **" + name[1] + " victoires**\n"
    else:
        for i in range(10):
            name = leaderboard[i].split("-")
            text += numbers[i] + " : **" + name[2].replace("\n", "") + "** avec **" + name[1] + " victoires**\n"
        text += "*+" + str(len(leaderboard) - 10) + " autres joueurs*"

    await ctx.send(text)

@bot.command()
async def leaderboard(ctx):
    await classement

@bot.command()
async def monRang(ctx):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        if str(ctx.author.id) in leaderboard[i]:
            await ctx.send(f"Tu es {str(i+1)}e/{len(leaderboard)}, avec {leaderboard[i].split('-')[1]} victoires !")
            return
    await ctx.send("Mmmmh... Tu n'es pas dans le classement, essaies de jouer !")

bot.run(secret.TOKEN)

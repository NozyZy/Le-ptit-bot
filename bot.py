import asyncio
import time
from datetime import date

import discord
import requests
import secret
import json

from bs4 import BeautifulSoup
from discord.ext import commands
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from fonctions import *

# ID : 653563141002756106
# https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="--",
                   description="Le p'tit bot !",
                   case_insensitive=True,
                   intents=intents)
tgFile = open("txt/tg.txt", "r+")
nbtg: int = int(tgFile.readlines()[0])
nbprime: int = 0
tgFile.close()

# Load server names from file
def load_server_names():
    try:
        with open("txt/server_names.txt", "r") as f:
            lines = f.readlines()
            names = {}
            for line in lines:
                if ":" in line:
                    server_id, name = line.strip().split(":", 1)
                    names[server_id] = name
            return names
    except FileNotFoundError:
        return {}

# Save server names to file
def save_server_names(server_names):
    with open("txt/server_names.txt", "w") as f:
        for server_id, name in server_names.items():
            f.write(f"{server_id}:{name}\n")

server_names = load_server_names()

GUILD_IDS = [
    410766134569074691,
    1193546302970146846,
    1420660433722802188
]

# On ready message
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(
        name=f"insulter {nbtg} personnes"))
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("Synchronizing slash commands for guilds :")
    for guild_id in GUILD_IDS:
        guild = discord.Object(id=guild_id)
        try:
            await bot.tree.sync(guild=guild)
            print(f"\t- {guild_id}")
        except Exception as e:
            print(f"\t- Failed for {guild_id}, reason : {e}")
    print("------")
    
    # Apply saved names to servers
    for guild in bot.guilds:
        if str(guild.id) in server_names:
            try:
                await guild.me.edit(nick=server_names[str(guild.id)])
                print(f"Applied saved name '{server_names[str(guild.id)]}' to server {guild.name}")
            except discord.Forbidden:
                print(f"No permission to change nickname in server {guild.name}")


# Get every message sent, stocked in 'message'
@bot.event
async def on_message(message):
    global nbtg
    global nbprime
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
                        print(
                            f">>({user.name} {time.asctime()}) - nouveau mot : {mot}"
                        )
                        dicoLines.append(mot)
                mot = ""

    dicoLines.sort()
    if len(dicoLines) > 0 and len(dicoLines) > dicoSize:
        dicoFile = open("txt/dico.txt", "w+")
        for i in dicoLines:
            dicoFile.write(i)
        dicoFile.close()

    # stock file full of insults (yes I know...)
    fichierInsulte = open("txt/insultes.txt", "r+", encoding="utf-8")
    insultes = fichierInsulte.read().split("\n")
    fichierInsulte.close()

    # stock file full of branlettes (yes I know...)
    fichierBranlette = open("txt/branlette.txt", "r")
    linesBranlette = fichierBranlette.readlines()
    branlette = []
    for line in linesBranlette:
        line = line.replace("\n", "")
        branlette.append(line)
    fichierBranlette.close()



    if message.content.startswith("--addInsult"):
        print(f">>({user.name} {time.asctime()})", end=" - ")
        mot = ' '.join(MESSAGE.split()[1:])
        if len(mot) <= 2:
            await channel.send("Sympa l'insulte...")
            return
        mot = mot+'\n'
        fichierInsulte = open("txt/insultes.txt", "a")
        fichierInsulte.write(mot)
        fichierInsulte.close()
        print("Nouvelle insulte :", mot)
        await channel.send("Je retiens...")

    if message.content.startswith("--addBranlette"):
        print(f">>({user.name} {time.asctime()})", end=" - ")
        mot = ' '.join(MESSAGE.split()[1:])
        if len(mot) <= 2:
            await channel.send("super la Branlette...")
            return
        if not mot.startswith(("jme", "j'me", "jm'", "je m")):
            await channel.send("C'est moi qui ME, alors JME... stp 🍆")
            return
        mot = mot+'\n'
        fichierBranlette = open("txt/branlette.txt", "a")
        fichierBranlette.write(mot)
        fichierBranlette.close()
        print("Nouvelle branlette :", mot)
        await channel.send("Je retiens...")

    # ping a people 10 time, once every 3 sec
    if MESSAGE.startswith("--appel"):
        print(f">>({user.name} {time.asctime()})", end=" - ")
        if "<@!653563141002756106>" in MESSAGE:
            await channel.send("T'es un marrant toi")
            print("A tenté d'appeler le bot")
        elif "<@" not in MESSAGE:

            await channel.send(
                "Tu veux appeler quelqu'un ? Bah tag le ! *Mondieu...*")
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
        if user == "None":
            user = message.author.name

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
        print(
            f">>({user.name} {time.asctime()}) - A généré une phrase aléatoire"
        )
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
        print(
            f">>({user.name} {time.asctime()}) - A compter le nombe de mots du dico"
        )
        text = f"J'ai actuellement {str(len(dicoLines))} mots enregistrés, nickel"
        await channel.send(text)

    # rename bot command (admin only)
    if MESSAGE.startswith("--rename "):
        if not message.author.guild_permissions.administrator:
            await channel.send("❌ Seuls les administrateurs peuvent utiliser cette commande.")
            return
        
        new_name = message.content[9:]  # Remove "--rename "
        if len(new_name) > 32:
            await channel.send("❌ Le nom ne peut pas dépasser 32 caractères.")
            return
        
        if len(new_name) == 0:
            await channel.send("❌ Veuillez spécifier un nom. Usage: `--rename NouveauNom`")
            return
        
        try:
            await message.guild.me.edit(nick=new_name)
            server_names[str(message.guild.id)] = new_name
            save_server_names(server_names)
            await channel.send(f"✅ Mon nom a été changé en '{new_name}' sur ce serveur.")
            print(f">>({user.name} {time.asctime()}) - A renommé le bot en '{new_name}' sur {message.guild.name}")
        except discord.Forbidden:
            await channel.send("❌ Je n'ai pas la permission de changer mon pseudo sur ce serveur.")
        except discord.HTTPException as e:
            await channel.send(f"❌ Erreur lors du changement de nom: {e}")

    # reset bot name to default (admin only)
    if MESSAGE == "--resetname":
        if not message.author.guild_permissions.administrator:
            await channel.send("❌ Seuls les administrateurs peuvent utiliser cette commande.")
            return
        
        try:
            await message.guild.me.edit(nick=None)
            if str(message.guild.id) in server_names:
                del server_names[str(message.guild.id)]
                save_server_names(server_names)
            await channel.send("✅ Mon nom a été remis par défaut sur ce serveur.")
            print(f">>({user.name} {time.asctime()}) - A remis le nom par défaut sur {message.guild.name}")
        except discord.Forbidden:
            await channel.send("❌ Je n'ai pas la permission de changer mon pseudo sur ce serveur.")
        except discord.HTTPException as e:
            await channel.send(f"❌ Erreur lors du reset du nom: {e}")

    # begginning of reaction programs, get inspired
    if not MESSAGE.startswith("--"):

        if "enerv" in MESSAGE or "énerv" in MESSAGE and rdnb >= 2:
            print(f">>({user.name} {time.asctime()}) - S'est enervé")
            await channel.send("(╯°□°）╯︵ ┻━┻")

        if "(╯°□°）╯︵ ┻━┻" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A balancé la table")
            await channel.send("┬─┬ ノ( ゜-゜ノ)")

        if MESSAGE.strip(".;,?! \"')").endswith("lucas"):
            print(f">>({user.name} {time.asctime()}) - A dit Lucas (goubet)")
            await channel.send("goubet")

        if (MESSAGE.startswith("tu sais") or MESSAGE.startswith("vous savez")
                or MESSAGE.startswith("savez vous")
                or MESSAGE.startswith("savez-vous")
                or MESSAGE.startswith("savais-tu")
                or MESSAGE.startswith("savais tu")) and rdnb > 3:
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
            reponses = ["mouais", "peut mieux faire", "woaw", ":o"]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ez" or MESSAGE == "easy") and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - A trouvé ça facile")
            reponses = [
                "https://tenor.com/view/walking-dead-easy-easy-peasy-lemon-squeazy-gif-7268918",
                "https://tenor.com/view/pewds-pewdiepie-easy-ez-gif-9475407",
                "https://tenor.com/view/easy-red-easy-button-red-button-gif-4642542",
                "https://tenor.com/view/simple-easy-easy-game-easy-life-deal-with-it-gif-9276124",
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

        if MESSAGE == "pouet":
          await channel.send("Roooooh ta gueuuuuule putaiiiiin")

        if MESSAGE == "poueth":
          await channel.send("Poueth poueth !! 🐤")

        if (MESSAGE.startswith("stop") or MESSAGE.startswith("arrête")
                or MESSAGE.startswith("arrete") and rdnb > 3):
            print(f">>({user.name} {time.asctime()}) - A demandé d'arrêter")
            reponses = [
                "https://tenor.com/view/daddys-home2-daddys-home2gifs-stop-it-stop-that-i-mean-it-gif-9694318",
                "https://tenor.com/view/stop-sign-when-you-catch-feelings-note-to-self-stop-now-gif-4850841",
                "https://tenor.com/view/stop-it-get-some-help-gif-7929301",
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
            print(
                f">>({user.name} {time.asctime()}) - A sorti sa meilleure répartie"
            )
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

        if (MESSAGE.startswith("hein")
                or MESSAGE.startswith("1")) and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A commencé par 1",
                  end="")
            reponses = ["deux", "2", "deux ?", "2 😏"]
            await channel.send(random.choice(reponses))

            # waits for a message valiudating further instructions
            def check(m):
                print(m.content)
                return (("3" in m.content or "trois" in m.content)
                        and m.channel == message.channel
                        and not m.content.startswith("http"))

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
            print(f">>({user.name} {time.asctime()}) - A commencer par a",
                  end="")

            def check(m):
                return m.content.lower(
                ) == "b" and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
                print(
                    f">>({user.name} {time.asctime()}) - A pas continué par b")
            else:
                print(
                    f">>({user.name} {time.asctime()}) - A connait son alphabet"
                )
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

        if MESSAGE == "oh" and rdnb >= 2:
            print(f">>({user.name} {time.asctime()}) - ", end="")
            if rdnb >= 4:
                print("S'est fait répondre (oh)")
                reponses = [
                    "Quoi ?",
                    "p",
                    "ah",
                    ":o",
                    "https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif",
                ]
                await channel.send(random.choice(reponses))
            else:
                print("S'est fait répondre par le dico (oh)")
                await channel.send(finndAndReplace("o", dicoLines))

        if MESSAGE == "eh" and rdnb >= 2:
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
            print(
                f">>({user.name} {time.asctime()}) - A demandé si on voulait")
            reponses = [
                "Ouais gros",
                "Carrément ma poule",
                "Mais jamais tes fou ptdr",
                "Oui.",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("quoi") and rdnb > 2:
            print(f">>({user.name} {time.asctime()}) - A demandé quoi")
            reponses = ["feur", "hein ?", "nan laisse", "oublie", "rien", "😯", "coubeh", "drilatère"]

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
                "facepalm", "damn", "fait chier", "fais chier", "ptn", "putain"
        ] or MESSAGE.startswith("pff")
                or MESSAGE.startswith("no..")) and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A gifé Conteville")

            await channel.send(
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif"
            )

        if (MESSAGE.startswith("t'es sur")
                or MESSAGE.startswith("t sur")) and rdnb > 3:
            print(
                f">>({user.name} {time.asctime()}) - A demandé si on était sur"
            )
            reponses = [
                "Ouais gros",
                "Nan pas du tout",
                "Qui ne tente rien...",
                "haha 👀",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE.startswith("ah ouais")
                or MESSAGE.startswith("ah bon")) and rdnb > 3:
            print(
                f">>({user.name} {time.asctime()}) - S'est intérrogé de la véracité du dernier propos"
            )
            reponses = [
                "Ouais gros", "Nan ptdr", "Je sais pas écoute...", "tg"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("au pied"):
            if message.author.id == 359743894042443776:
                print(
                    f">>({user.name} {time.asctime()}) - Le maitre m'a appelé")

                reponses = [
                    "wouf wouf",
                    "Maître ?",
                    "*s'agenouille*\nComment puis-je vous être utile ?",
                    "*Nous vous devons une reconnaissance éternelllllllle*",
                ]
            else:
                print(
                    f">>({user.name} {time.asctime()}) - Un faux maître m'a appelé"
                )
                reponses = [
                    "ratio",
                    "ptdr t ki ?",
                    "mais lèche moi le pied",
                    "vous êtes ?",
                    "*vu*",
                    "<@359743894042443776> quelqu'un cherche à vous usurper maître.",
                    "dégage.",
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
                        await message.add_reaction("🇹")
                        await message.add_reaction("🇬")
                    print(f">>({user.name} {time.asctime()}) - A insulté")
                    return

        if "branle" in MESSAGE:

            await channel.send(random.choice(branlette))
            return

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
            reponses = ["Le deuxième", "Le prochain", "Aucun"]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("laquelle") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - A demandé laquelle")
            reponses = ["La deuxième", "La prochaine", "Aucune"]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("miroir magique"):
            print(
                f">>({user.name} {time.asctime()}) - A sorti une répartie de maternelle"
            )
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

        if MESSAGE == "chaud" or MESSAGE == "cho":
            print(f">>({user.name} {time.asctime()}) - A dit chaud")
            await channel.send("Cacao !")

        di = ["dy", "di"]
        for index, word in enumerate(MESSAGE.split(" ")):
            if any(word.startswith(i) for i in di) and word[2] != 'n':
                msg = MESSAGE.split(" ")[index][2:].replace(",", "").replace(".", "")
                if len(msg) > 4 and rdnb > 3:
                  # random number to avoid "Dit moi" => "t"
                    await channel.send(msg.capitalize() + " !")
                    return

        if MESSAGE == "go":
            print(f">>({user.name} {time.asctime()}) - Is going fast !")
            day = today.strftime("%d")
            month = today.strftime("%m")
            gos = [
                "https://c.tenor.com/LJn9eialwjgAAAAC/sonic-the-hedgehog.gif",
                "https://c.tenor.com/w0BpwA8t3QEAAAAC/sonic-movie2-sonic-dance.gif",
                "https://c.tenor.com/L8fy18ZJ7JEAAAAC/run-gotta-go-fast.gif",
                "https://c.tenor.com/2NUm_masBmEAAAAC/sonic-floss.gif",
                "https://c.tenor.com/jozKhaebUZ4AAAAS/ugly-sonic-chip-n-dale-rescue-rangers.gif",
                "https://c.tenor.com/Znb6cHabDbAAAAAS/mpreg-sonic.gif",
                "https://c.tenor.com/BfBt0RyGkTwAAAAC/sonic.gif",
            ]
            embed = discord.Embed(
                title="Gotta GO fast!",
                description="You spin'n'go",
                color=0x174B96,
                url="https://github.com/BenjaminLesieux/Gotta-Go-Fast",
            )
            go = gos[((int(user.id) // 365 + int(day) * 5) // int(month)) %
                     len(gos)]
            embed.set_thumbnail(url=random.choice([
                "https://ih1.redbubble.net/image.1040577258.9748/st,small,507x507-pad,600x600,f8f8f8.jpg",
                "https://static.wikia.nocookie.net/meme/images/4/42/1385136139955.png/revision/latest?cb=20150207013804",
                "https://www.pngitem.com/pimgs/m/135-1357735_transparent-sanic-png-sonic-meme-png-png-download.png",
            ]))
            embed.set_author(
                name="Le p'tit god",
                url="https://github.com/NozyZy/Le-ptit-bot",
                icon_url=
                "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
            )
            embed.set_image(url=go)
            embed.set_footer(text="SOinc")
            print("GOes fast today")
            await channel.send("GOtta GO fast !", embed=embed)

        if MESSAGE == "kanye":
            url = "https://api.kanye.rest/"
            response = requests.get(url)
            json_p = response.content.decode('utf-8')
            quote = json.loads(json_p)['quote']

            embed = discord.Embed(
                description="Kanye said",
                title=quote,
                color=0xfed400,
                url=url
            )
            embed.set_author(
                name="Kanye West",
                url=url,
                icon_url=
                "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
            )
            embed.set_footer(text="provided by kanye.rest")
            await channel.send("Kanyeah", embed=embed)

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
            if userID == 890084641317478400 and rdnb >= 3:
                await channel.send("Lâche l'affaire David")
                print("C'était David")
                return
            if userID % 5 != (int(day) + int(month)) % 5:
                await channel.send("Not today (☞ﾟヮﾟ)☞")
                print("N'est pas dieu aujourd'hui")
                return
            user = await message.guild.fetch_member(userID)
            pfp = user.avatar.url
            gods = [
                [
                    "https://tse4.mm.bing.net/th?id=OIP.IXAIL06o83HxXHGjKHqZMAHaKe&pid=Api",
                    "Loki",
                ],
                [
                    "https://www.wallpaperflare.com/static/810/148/1018/painting-vikings-odin-gungnir-wallpaper.jpg",
                    "Odin",
                ],
                [
                    "https://tse3.mm.bing.net/th?id=OIP.3NR2eZEBm46mrcFM_p14RgHaJ3&pid=Api",
                    "Osiris",
                ],
                [
                    "https://tse1.explicit.bing.net/th?id=OIP.KXfuA_jDa_cfDkrMInOMfQHaJq&pid=Api",
                    "Shiva",
                ],
                [
                    "https://tse2.mm.bing.net/th?id=OIP.BYG-Xfgo4To4PJaY32Gj0gHaKD&pid=Api",
                    "Poseidon",
                ],
                [
                    "https://tse1.mm.bing.net/th?id=OIP.M6A5OIYcaUO5UUrUjVRn5wHaNK&pid=Api",
                    "Arceus",
                ],
                [
                    "https://tse3.mm.bing.net/th?id=OIP.M2w0Dn5HK19lF68UcicLUwHaMv&pid=Api",
                    "Anubis",
                ],
                [
                    "https://tse2.mm.bing.net/th?id=OIP.pVKMpFtFLRjIpAEsPMafJgAAAA&pid=Api",
                    "Tezcatlipoca",
                ],
                [
                    "https://www.spiritmiracle.com/wp-content/uploads/2023/04/goddess-venus-cupid.jpg",
                    "Venus",
                ],
                [
                    "https://image.tensorartassets.com/cdn-cgi/image//posts/images/613335434814121629/5f9b14dc-12f8-45f4-8cfd-8fb38dc3cb02.jpg",
                    "God zilla",
                ],
                [
                    "https://www.writersandy.com/uploads/1/2/5/4/12545559/published/goddess-inanna2.jpg?1524448024",
                    "Ishtar",
                ],
                [
                    "https://1.bp.blogspot.com/-J6h4vRgHTEg/WDkQztXD12I/AAAAAAAANRY/TeAWIz6L3_kBZr86cTWS4YVHYoCXCmx3gCLcB/s1600/Karna-Vimanika-Comics.jpg",
                    "Karna",
                ],
                [
                    "https://i.pinimg.com/originals/32/d6/55/32d6553b6a36d8872734998af9312c71.jpg",
                    "Brynhild",
                ],
                [
                    "https://static.wikia.nocookie.net/omniversal-battlefield/images/7/73/Sun_Wukong_%28Art%29.jpg/revision/latest?cb=20210823031548",
                    "Sun Wukong",
                ],
                [
                    "https://i.redd.it/7q9as4hojtd61.jpg",
                    "Apollo",
                ],
                [
                    "https://upload.wikimedia.org/wikipedia/commons/b/b5/Quetzalcoatl_1.jpg",
                    "Quetzacoalt",
                ],
                [
                    "https://static.wikia.nocookie.net/gods_and_demons/images/d/d6/D317f73591e2565cc5617fc7d8f2c630.jpg",
                    "Hades",
                ],
                [
                    "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/6ec0d49d-038d-4900-b498-c8cc3863c8e8/dd2bzrv-c474cf5f-386e-44b4-89f8-e0e69827e1a1.jpg/v1/fill/w_800,h_1000,q_75,strp/ereshkigal_by_irenhorrors_dd2bzrv-fullview.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTAwMCIsInBhdGgiOiJcL2ZcLzZlYzBkNDlkLTAzOGQtNDkwMC1iNDk4LWM4Y2MzODYzYzhlOFwvZGQyYnpydi1jNDc0Y2Y1Zi0zODZlLTQ0YjQtODlmOC1lMGU2OTgyN2UxYTEuanBnIiwid2lkdGgiOiI8PTgwMCJ9XV0sImF1ZCI6WyJ1cm46c2VydmljZTppbWFnZS5vcGVyYXRpb25zIl19.Svr-kqOYRHqmLSi0VW3YORKkt-q8WdvC8FaKvlWxbz0",
                    "Ereshkigal",
                ],
                [
                    "https://www.nautiljon.com/images/description/00/37/1635269992331_image.jpg",
                    "Asclepius",
                ],
                [
                    "https://cdnb.artstation.com/p/assets/images/images/056/675/953/large/gabriel-flauzino-thorcolour.jpg",
                    "Thor",
                ],
                [
                    "https://i.pinimg.com/originals/ae/68/50/ae68509b78c017ecba1f08d64c59c7f8.jpg",
                    "Amon",
                ],
                [
                    "https://cdna.artstation.com/p/assets/images/images/006/489/730/large/boyan-petrov-thoth12.jpg",
                    "Thoth",
                ],
                [
                    "https://cdnb.artstation.com/p/assets/images/images/011/390/921/large/mohamed-sax-sobek.jpg",
                    "Sobek",
                ],
                [
                    "https://cdnb.artstation.com/p/assets/images/images/012/343/689/large/yiye-gong-img-20180806-173554.jpg",
                    "Dio",
                ],
                [
                    "https://upload.wikimedia.org/wikipedia/commons/6/69/Sucellus_MAN_St_Germain.jpg",
                    "Sucellos",
                ],
                [
                    "https://i.pinimg.com/originals/fa/8f/b2/fa8fb2e1f6ec3e529c119b05c2c5c649.png",
                    "Gaïa",
                ],
                [
                    "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/8809c8cd-04d2-4fc2-bc24-f9e2460d0f36/d8vo0pe-00f82d4e-4560-462d-9d19-594b1455f009.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcLzg4MDljOGNkLTA0ZDItNGZjMi1iYzI0LWY5ZTI0NjBkMGYzNlwvZDh2bzBwZS0wMGY4MmQ0ZS00NTYwLTQ2MmQtOWQxOS01OTRiMTQ1NWYwMDkuanBnIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.w8B7yWVQ2_wrZKZvJ_p9JzrXymLB3XWWmEdOx-JXmP4",
                    "Anu",
                ],
                [
                    "https://cdna.artstation.com/p/assets/images/images/019/778/880/large/ekaterina-chesalova-enki.jpg",
                    "Enki",
                ],
                [
                    "https://cdna.artstation.com/p/assets/images/images/030/081/254/large/victoria-ponomarenko-2-zin-enlil-a5.jpg",
                    "Enlil",
                ],
                [
                    "https://i.pinimg.com/originals/01/61/ec/0161ecc12f56d0310f332d6e2714bd6c.png",
                    "Marduk",
                ],
                [
                    "https://static.wikia.nocookie.net/villains/images/7/72/Lovecraft-cthulhu.jpg/revision/latest?cb=20151128095138",
                    "Cthulhu",
                ],
                [
                    "https://tolkiengateway.net/w/images/4/48/Elena_Kukanova_-_Vana_the_Ever-Young.jpg",
                    "Vána",
                ],
                [
                    "https://static.wikia.nocookie.net/dragonball/images/7/7d/BeerusWikia_%283%29.jpg/revision/latest?cb=20240224003806",
                    "Beerus",
                ]
            ]
            embed = discord.Embed(
                title="This is God",
                description="<@%s> is that god." % userID,
                color=0xECCE8B,
                url=random.choice([
                    "https://media.giphy.com/media/USm8tJQzgDAAKJRKkk/giphy.gif",
                    "https://media.giphy.com/media/ZArMUnViJtKaBH0XLg/giphy.gif",
                    "https://tenor.com/view/bruce-almighty-morgan-freeman-i-am-god-hello-hey-gif-4743445",
                ]),
            )
            god = gods[((userID // 365 + int(day) * 5) // int(month)) %
                       len(gods)]
            embed.set_thumbnail(url=pfp)
            embed.set_author(
                name="Le p'tit god",
                url="https://github.com/NozyZy/Le-ptit-bot",
                icon_url=
                "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
            )
            embed.set_image(url=god[0])
            embed.set_footer(text=god[1])
            print("Est un dieu aujourd'hui : ", god[1])
            await channel.send("God looks like him.", embed=embed)

        if MESSAGE.startswith("hello") and rdnb >= 3:
            print(f">>({user.name} {time.asctime()}) - A dit hello")
            await channel.send(file=discord.File("images/helo.jpg"))

        if (MESSAGE == "enculé" or MESSAGE == "enculer") and rdnb > 3:
            print(
                f">>({user.name} {time.asctime()}) - A demander d'aller se faire enculer"
            )
            image = ["images/tellermeme.png", "images/bigard.jpeg"]
            await channel.send(file=discord.File(random.choice(image)))

        if MESSAGE == "kachow":
            responses = [
                "https://c.tenor.com/FfimHvu74ccAAAAC/kachow-backdriving-blink-mcqueen-cars-last-race.gif",
                "https://i.pinimg.com/originals/3a/8b/03/3a8b036011946ab59ea2a8c353372d2b.gif",
            ]
            await channel.send(random.choice(responses))

        if MESSAGE == "stonks":
            print(f">>({user.name} {time.asctime()}) - Stonked")
            await channel.send(file=discord.File("images/stonks.png"))

        if (MESSAGE == "parfait" or MESSAGE == "perfection") and rdnb > 3:
            print(f">>({user.name} {time.asctime()}) - Perfection")
            await channel.send(file=discord.File("images/perfection.jpg"))

        if MESSAGE.startswith("leeroy"):
            print(f">>({user.name} {time.asctime()}) - LEEROOOOOOOOOOYY")
            await channel.send(file=discord.File("sounds/Leeroy Jenkins.mp3"))

       # if "pute" in MESSAGE and rdnb > 4:
       #     print(f">>({user.name} {time.asctime()}) - Le pute")
       #     reponses = [
       #         "https://tenor.com/view/mom-gif-10756105",
       #         "https://tenor.com/view/wiener-sausages-hotdogs-gif-5295979",
       #         "https://i.ytimg.com/vi/3HZ0lvpdw6A/maxresdefault.jpg",
       #     ]
       #    await channel.send(random.choice(reponses))

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
            await channel.send(
                "https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif"
            )

        if "pd" in MESSAGE:
            print(f">>({user.name} {time.asctime()}) - A parlé de pd")
            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "p"
                        and MESSAGE[i + 2] == "d" and MESSAGE[i + 3] == " "):
                    await channel.send(file=discord.File("images/pd.jpg"))

        if "oof" in MESSAGE and rdnb >= 5:
            print(f">>({user.name} {time.asctime()}) - oof")
            reponses = [
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif",
                "https://tenor.com/view/yay-smile-happy-cute-oof-gif-16086929",
                "https://tenor.com/view/oof-damn-wow-ow-size-gif-16490485",
                "https://tenor.com/view/big-oof-size-small-medium-switch-gif-17355313",
                "https://tenor.com/view/oof-saturday-night-live-ouch-yikes-oh-dear-gif-23826406",
                "https://tenor.com/view/big-oof-yikes-gif-15532766",
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

    if MESSAGE.capitalize().startswith("Tralalero"):
        await channel.send("Tralala")
    if MESSAGE.capitalize().startswith("Bombardiro"):
        await channel.send("Crocodilo")
    if MESSAGE.capitalize().startswith("Tung"):
        await channel.send("Tung Tung Tung Tung Tung Tung Tung Tung Sahur")
    if MESSAGE.capitalize().startswith("Lirilì"):
        await channel.send("Larilà")
    if MESSAGE.capitalize().startswith("Boneca"):
        await channel.send("Ambalabu")
    if MESSAGE.capitalize().startswith("Brr"):
        await channel.send("Brr Patapim")
    if MESSAGE.capitalize().startswith("Chimpanzini"):
        await channel.send("Bananini")
    if MESSAGE.capitalize().startswith("Bombombini"):
        await channel.send("Gusini")
    if MESSAGE.capitalize().startswith("Capuccino"):
        await channel.send("Assassino")
    if MESSAGE.capitalize().startswith("Trippi"):
        await channel.send("Troppi")
    if MESSAGE.capitalize().startswith("Frigo"):
        await channel.send("Camelo")
    if MESSAGE.capitalize().startswith("Ballerina"):
        await channel.send("Cappucina")
    if MESSAGE.capitalize().startswith("Trulimero"):
        await channel.send("Trulicina")
    if MESSAGE.capitalize().startswith("Girafa"):
        await channel.send("Celestre")
    if MESSAGE.capitalize().startswith("Bobrito"):
        await channel.send("Bandito")
    if MESSAGE.capitalize().startswith("Frulli"):
        await channel.send("Frulla")
    if MESSAGE.capitalize().startswith("Brri"):
        await channel.send("Brri Bicus Dicus Bombicus")
    if MESSAGE.capitalize().startswith("Tric"):
        await channel.send("Trac Baraboom")
    if MESSAGE.capitalize().startswith("Cocofanto"):
        await channel.send("Elefanto")
    if MESSAGE.capitalize().startswith("Burbaloni"):
        await channel.send("Lulilolli")
    if MESSAGE.capitalize().startswith("Orangutini"):
        await channel.send("Ananasini")
    if MESSAGE.capitalize().startswith("Garamararamararaman"):
        await channel.send("dan Madudungdung tak tuntung perkuntung")
    if MESSAGE.capitalize().startswith("Blueberrinni"):
        await channel.send("Octopussini")
    if MESSAGE.capitalize().startswith("Rhino"):
        await channel.send("Toasterino")
    if MESSAGE.capitalize().startswith("Zibra"):
        await channel.send("Zubra Zibralini")
    if MESSAGE.capitalize().startswith("Graipussi"):
        await channel.send("Medussi")
    if MESSAGE.capitalize().startswith("Tigrrullini"):
        await channel.send("Watermellini")
    if MESSAGE.capitalize().startswith("Tracotucotulu"):
        await channel.send("Delapeladustuz")
    if MESSAGE.capitalize().startswith("Gorillo"):
        await channel.send("Watermellondrillo")
    if MESSAGE.capitalize().startswith("Bananita"):
        await channel.send("Dolfinita")
    if MESSAGE.capitalize().startswith("Tigroligre"):
        await channel.send("Frutonni")
    if MESSAGE.capitalize().startswith("Ballerino"):
        await channel.send("Lololo")
    if MESSAGE.capitalize().startswith("Crocodildo"):
        await channel.send("Penisini")
    if MESSAGE.capitalize().startswith("Špijuniro"):
        await channel.send("Golubiro")
    if MESSAGE.capitalize().startswith("Elephantuchi"):
        await channel.send("Bananuchi")
    if MESSAGE.capitalize().startswith("Crocodillo"):
        await channel.send("Ananasinno")

    if "brainrot" in MESSAGE or "italian" in MESSAGE:
        brainrots = [
            {"name": "Tralalero Tralala", "img": "https://i.namu.wiki/i/Xx4c8zAsZSl_4MPCne2ehJGXkxHfLVevSusjY3nVYTGo6qWtCVlia9OCGo9H6dpl22yROFQY2kjq7SkgMyiSUFZdw1uN-itHSOzFo21_xG8Yn08BchnoUkd1I2Lhx81jIwkYzYpKo6WgqYcrTeaUMQ.webp"},
            {"name": "Bombardiro Crocodilo", "img": "https://i.namu.wiki/i/tDuYiBQRDatd0hIa65v0Q-qWASSh7UI1A9SYkvtF1UybnJvqFU_IGpmkAB_8rlhEZcJVK-inmcK9h4oPEREEJn5-5Ku0LUDlarjM_hsWxoJWYvDsvMxN_hV80nHOOm4lVs-8Sk6SoEoDxn5ih-ShGg.webp"},
            {"name": "Tung Tung Tung Tung Tung Tung Tung Tung Tung Sahur", "img": "https://i.namu.wiki/i/-YZ0x_wWyQ2z92YKH1hTYwuJQCPJw1TE6zt5q7evVOyAW-k1pXxNWp6VXpNMI_RSfpbPcKsaKEbLGXVADX5zaebZmasNey0DOH9yhopRXX5wPT3KocHxhRLSQ-AYPL_rCeyZamTxN0WN3LzaVMxahA.webp"},
            {"name": "Lirilì Larilà", "img": "https://i.namu.wiki/i/dbL-iw2P5t7mGWYIAHKWAn5EIYhcAKwYyeCjoWQWqCIcPr0T4a0svt21GzQVAzUWISnr2U_2U90S_i--14dLyF0zx1wXrMCw3IL6CI1tPGa_3pXV82OWUXVoYcJnz8QNyGCVZ27X1psrSdaanFdebQ.webp"},
            {"name": "Boneca Ambalabu", "img": "https://i.namu.wiki/i/5W9RGh81s6LNY4lZhT65tnbT_9oRiZaHy0kvsajWBZBk9CNQCobnNB9Q_K2TCsP4VrTufhr6LuP0Emj0g8RohJz10W-WjHzPAJcb0ACpiGPGc7kWsrjWx5nmapJcc2M7gTacge6ZwAn8I1lmy_7JlQ.webp"},
            {"name": "Brr Brr Patapim", "img": "https://i.namu.wiki/i/PccZl7Dts7ykLg5Gl2HGZWAP5vuU74lQHzJ6QBHHBlGmnS5WU7nq-f7muafQtm8lmAu9weOI8fP_FkJ_2WBo2Or9asEWpKqZ0Wh8h8ZxRLy836g997Ew7WQ3l2PW5xqHmNv4vwzfpzqs3Rz41sANyA.webp"},
            {"name": "Chimpanzini Bananini", "img": "https://i.namu.wiki/i/49pkt4yi1RO-lKVdrxBNSbMMnbPd38Vo4IV-dSdPnt0gHlydhIkrQHqaEtRSM4c_nyGXyYL5woaEqvQZL2A3TYnizNXvO8MTYbh4PEB9xOC3UPudV5lqlX6xNQ_bFOPyPftbvZ0c7YI9ALsGTvfSFQ.webp"},
            {"name": "Bombombini Gusini", "img": "https://i.namu.wiki/i/NSbDg0Cb8yiySnaL2SYntIwxriTr4HmeowtJwH_s2YX-HBxDhxPRCEZ0ea6_-FuAqu7BdA_RQqwdubg0G5yYiEsuKueysUZF28_RE2P18wjpLhv55Hu2j1Iut1noltjVWofh_KWnmyf5pfVlnXmIvw.webp"},
            {"name": "Cappuccino Assassino", "img": "https://i.namu.wiki/i/rggVL2LkfRxNMc0PQODWdH4x-I_KEIaJTznCs5egmZe96KjJlABkq3pQWaMr9p_zrfUw3-bEqvisfw71YPLMSEbU1RcFGgnRBTzh4UXGN8cjKXcRHLfLC-ViPDxUWltYCUxrRr-fvU8ygSoUxrQvMg.webp"},
            {"name": "Frigo Camelo", "img": "https://i.namu.wiki/i/391NIeZunfajIGAPH1xfALBtP65uh8sqIu2UjQFC70OYt1oYrkntplWaJDkn7D58KmuFTVmdp4DGnWAMMCoEsGDJzCVHiFnCi6dKjm4D0OeHZsMXm7cEVVWPaCXfoMJW0kl_USiEox27CTQ6_-Pe8A.webp"},
            {"name": "La Vaca Saturno Saturnita", "img": "https://i.namu.wiki/i/W4lHNC4WJ9dBjbVFcTFpsR4A2Pg_LIvr09xCf4vCYQMbiWRIsg023TWI_svmjL3DHtIRh8U1T-RVwvSjMlZt6GhzVjVSSGFhPIeMkwo86rSSMk4bNemEqmoy9upGT9mtG9gSygm0o0fk_EGnSkFbJA.webp"},
            {"name": "Ballerina Cappuccina", "img": "https://i.namu.wiki/i/yzm1X6PvZRc36cNhgT1xxD4QwniE7UUZHIwbVesAI7rYy5VreFFB0IxUngc76qHZ1qQo63Bh6OmUeXmc_vOSAX51VFrj0qeHHogTw5SD2teN8N0LTtwNnEpfRby8gU-hoFQpdGl95T3l6awIIDHt_A.webp"},
            {"name": "U Din Din Din Din Dun Ma Din Din Din Dun", "img": "https://i.namu.wiki/i/cq6ASoJxVvPvV0IRNyfRGOkcYAQRIkPWil69Zyjgg267HFSMRIKt25C4XBZVEkeSA8HgFSf9okD28LuQ7_AOwA-MshZfSKIlhX_CtAQ6OzNvECyRWNAAkM5eVfScK7Cu7zGKSGphit3Ko8vzQP9naw.webp"},
            {"name": "Trulimero Trulicina", "img": "https://i.namu.wiki/i/q05gfcRKrv24JlKynBNbsSBuxz7WxMlXROoK1HoSpndeUzJrKv5Yz4JATcjKmuAWD2hHl0s46t43Sd0xlGHoUiV7aT5k3ZRVWSrTpLvo7XiZZUjDif4HWvm5ZLWxIkwnvW4h-A-7Rh_m55YIexoMlg.webp"},
            {"name": "Girafa Celestre", "img": "https://i.namu.wiki/i/JOhT5BefVgf5DG7Hs8c8kZqv9c5GHC8rOtdHnQMFBiouWJ_lk7Jfc5xd2AEq4_9jkmTU3EuPH39utI3KBcLYzIWr09X94clgClO-lscS_q6Hur-EtJDpHn3y2SykserZhZg_36X7M8x6WAFCoVlbBg.webp"},
            {"name": "Bobrito Bandito", "img": "https://i.namu.wiki/i/xUB-o7rksj-QM-sG1G5z0MxUN-doo4YGbZFqdX4yxcsC0gt1ucq7tgmHM_VYfD2T8o30nQHAkVHc4_EqVWFxOvlsxyY1nOm64gnpslCEmItn8ooIMIIBGcWy-sLuy0UaVWBT_XP7LeYTIhhJ_cSWvA.webp"},
            {"name": "Frulli Frulla", "img": "https://i.namu.wiki/i/EvPlhewaa6TNqZ1szVppY4S-9qA4P_1vxbr54tCZonP-Wuedom_4GqpH4N18yd526KuQbTxo0BR8kdVOB1rEg4isItDXwGeAqjvhRdw9gl7b80W3xZYobUqZco71x3Uyn5vnsd6FFFuLqbCYOQXo5A.webp"},
            {"name": "Ta Ta Ta Ta Ta Ta Ta Ta Ta Ta Ta Sahur", "img": "https://i.namu.wiki/i/m-9jVfTspmRX4zNNfh5jYaRL8fgYI0bXhkXuEMlN_k0lVngy4JVTdeqUoRe_6AcWBsF38zOFeJiYrYlC71YG6uzQBi97qmt07vb5ZDo0GYb22IMmWjHExc1Ed6QpHqe-dYbOenk5_PJvwe1hjE0fAA.webp"},
            {"name": "Brri Brri Bicus Dicus Bombicus", "img": "https://i.namu.wiki/i/xwdTlKJqM_fgN0YysgB6YXWowr9NdVTXX2S0CQRsOuia9fULQCT61B3PSxpYplG8_amw5tnP9OHW9uDaLS1A9M0wsj0LWOIMkf9i6ZcNz4mDBGNY9-VJjQUNKFdGpD9BxyQ65cn5wRO2r7cg7UfGyg.webp"},
            {"name": "Tric Trac baraboom", "img": "https://i.namu.wiki/i/-UX1lW3G9HQl5nLGBbcFaKULQbO-ry5iSQORQApRoBjJ9y7FSydIIy1YJwEU-vNPnGihbNq8MqIMVqT826n-QXoU-fnhej9E2OxpGEH5emjZSpxMOQMJ6u5UJFzEUTUouCWtBtvmJsHUei6bEABQJA.webp"},
            {"name": "Cocofanto Elefanto", "img": "https://i.namu.wiki/i/pyia2JHQAqDT3BYFUs9yM1FrpR7sH0vE_thixD0kEMFPqIHnEH22B3elVxOidI4tn00uYSCJVvbiOmfy3343YC5gYu7MtIWC-SJBrrsuFfpKJrmSez1S5IX6mV0nThvJM5En4AVD5xQAAo2Ordniyw.webp"},
            {"name": "Burbaloni Lulilolli", "img": "https://i.namu.wiki/i/UYcxP-mxt7BqXDJJRCLUnVtbVj69-96MkhYuLC_kP_QTxvWqkCzuKfn_TnFpG_3bjzQEfBuagjsz6ImmWxAqFhRh7K7OKhxpj6XcVhYO0UFSDce9FatCaioVDeLmx4Q5aWYpmLTeq_WSgyHXQfe4jg.webp"},
            {"name": "Orangutini Ananasini", "img": "https://i.namu.wiki/i/DXM5l6EtDzjJtUzCRK_ALP5jZvEc3h_xQBM4ALGRyhHwICpfa8KIH-7Cp_k89_BWvZikce_-4E6ZN119kM3B83-zBUcyOduQ-EDdUGLsOyoJ8kfxSYq5d3hjCcgFsV7KBXV3mQZZ0sIDwRd3bpSlpg.webp"},
            {"name": "Il Cacto Hipopotamo", "img": "https://i.namu.wiki/i/RQ9OdtOU87LLkw3vtzlV-vMPgol71hLzlopOQu9fCGqbi34fMPRkH1zmohkwzeB4ul38O7fM17Yhrr7Ld_k4Lla6lQct7infhd4RX7lwocc89EjF4XdWNlZWckr3swedq75Pd6-tPc4TxFsbjGOYKw.webp"},
            {"name": "Blueberrinni Octopussini", "img": "https://i.namu.wiki/i/qyB8WrUykCqdofXbBRrU3YUqG-54YivrSpVkI8HfkkGE0f77QvFynFjkDZZevsaCndymh0EJq_qJ7YEgD9w2vmmuzxV78GtSWfhev_K5t-wzBkMmWyFe_ZBWMNdau3_HwHPxPME1HhC5vJ69TT0taA.webp"},
            {"name": "Glorbo Fruttodrillo", "img": "https://i.namu.wiki/i/QPGeJpiRG4RVUnNxBM0k01wQHSVVDWihyuUF876jftkt512vetssWGg0G1ziCSKe1zTXKJEnCCjpzSFj0Zz5KMzoKPFQJhheqMMM7AwCEkO4OrADnMA84e_ZeAViuQUjZRgtXrLjdjbd21w6awLoLg.webp"},
            {"name": "Rhino Toasterino", "img": "https://i.namu.wiki/i/BgSNGA9KzuCYiDxaspVbG4-cGuRFvG_rZbXmONKjRPje08JDRipjnW2_wwglzBkCLYzSgCa7c8D0A4ojuxvkR3c514GFKAHazzlbUu1FHhTE9J7q3IDRhytCG4wl-RJ5it627zzYVW4rb4yC_BBVHQ.webp"},
            {"name": "Zibra Zubra Zibralini", "img": "https://i.namu.wiki/i/Nr-f89621tXOSrFqcOpfqpSS3wRuxrNjqC8uRylUoFmDHX0BfUq7Skv0VG3IjT5P-0Dbnls6J_bj0AKaS65YuMLgCUozTGqaZXiW74bmILqJjONohzTTGrMV8pDnWW3WN_uxvPcuOFo1WkkLrolBKw.webp"},
            {"name": "Graipussi Medussi", "img": "https://i.namu.wiki/i/3BtP9lthfQy_ogTnzikskfnTlQshcNGJFiTOvlmtAwegxxGWP8sj9YsAe5bObvH3sXw0pV9tMTjG8NfGHqQmuwG1lPa70oi43eMUdidnVehwu6iHk1DzRLnRRQczX2VX2A1v91gkPxpu5bR8BqwQ-g.webp"},
            {"name": "Tigrrullini Watermellini", "img": "https://i.namu.wiki/i/ZC7-STZmiF5-vZ54MueDIcixWk55ljrvGFY67ETw9kK5MN3TdJRwfRfYL1BreWHZ9FTg44r52v3DYtPnvNCZFMJBwEeU-J5vZUbNfhvHRSa-iCWQFhgw8xuKCcyDjxBOmQEyAE5mZwQ17GKRRz_MPA.webp"},
            {"name": "Tracotucotulu Delapeladustuz", "img": "https://i.namu.wiki/i/TBSB0PIlWOrt-6iJuVAlaEYV0zm1MBlgz-VdP8Q9iepDX7OLDvQ6U9xvPLQCQtrVQ8qGcyJ46KXDfr1IljlzT-f7XbCTpeE1wi7Mi6pe4bPeLVDGAM_9_YFY7MTEli-6VyCAtvuuuEwAznkHgqFb4Q.webp"},
            {"name": "Gorillo Watermellondrillo", "img": "https://i.namu.wiki/i/qPtR_6vBLXJqBzeENJpFJU7sPFi1z6ij_E57c3NiaDu3yL8Dg5ZL6PF6K2ygAa0KBmggawSAglQiXldStCIx0TQTwaIXNzW9_bVD5NrGOL-cibNeM_1dnd438-NVieKAD4wRywRU41TDdNNyCPbUlA.webp"},
            {"name": "Bananita Dolfinita", "img": "https://i.namu.wiki/i/DOt7KayBkCvrstXxe7poCe5oBKAo_5sitp9po9YkMXmWsuPyallRQTLaJxUvkvEItdL21kd2pq2UFzNRm0D96nkUJ2VfvMMKIK465WIA1qaOls9y3Y0rJ5gA07Yehtg-P4a8TH4QMmquXgxCz4qZeA.webp"},
            {"name": "Tigroligre Frutonni", "img": "https://i.namu.wiki/i/j4b_PPAS8H5IWSWaymOfCBFy_1V7N5GA75Uz731KTMwOmlcV0pjQYbt8e7QTHf3hzKrhMMW38wqInz6DrW-ASse9dC3MFrJJboWdUVtKbtB6rL8zsvNVWLIHp5ForaPFl3oK5BF0h_r1wcdUTjL-nA.webp"},
            {"name": "Ballerino Lololo", "img": "https://i.namu.wiki/i/EEplz4eBQ87WL3zfjKXlCc2sh-PWc7DN5DGCAdoaeSy0XFV2OpbwOjGIil1KwlMOLccbHmiRMbX7iFZ226Q-Aj7UejvoQy71j71ZIBHoUX1R7kdkbpwebbfrUYN_6ttLWoz1L3Kj_SpRMXBu6Dx-oQ.webp"},
            {"name": "Crocodildo Penisini", "img": "https://i.namu.wiki/i/sv5wFVzFpFgkWj5b86p0-TEIW2K1XaGcBNCCNBIT0jNsn--i0NdvrrI9D5bcdjgKRIKkfqbg3EYMt8QfzsjStalHaRBbfJ0ZqGyB3l9de1XJNhEKJ5r3SCs1yqOSEGSUSXgAzR1QTKlwfulIUCv8kw.webp"},
            {"name": "Matteooooooooooooo", "img": "https://i.namu.wiki/i/x_KXXRuSH8SUSLPiDBnKKoKEA4wlVusBOYk_PoKn2WOAP56spIJ3HjQ8CnX3IYmd2-3nuZvKi5O9rLNWMepRL67QBF7szQOuSEYfkGFv1Jnp5P7ZUcWGhPB8gPRWQ4MVTwL8NbdStlHzeeWhUcGAfg.webp"},
            {"name": "Špijuniro Golubiro", "img": "https://i.namu.wiki/i/KamQxFAa5Hh6LkFe6lF71drZpDAohwfj7Wn_3Hf9laO36a-cyZ4XVpOC70S4CRkqSJcd32M-uvxWHqZ1dXRx7S_dw6gegmd7Ha9RbLAb3N5_zgUc1VjZFCpFMPIMuRe2KTmQ9HRgqguWmPBywtdK7w.webp"},
            {"name": "Elephantuchi Bananuchi", "img": "https://i.namu.wiki/i/1WWoRpgJfsx3P5lt68LqCAVtMU_Lf5gaofQOWDG9Cgpbvot-lSc4WIz4yuTrc7nJ1I1ikUj25gzXSkCd9AecBhjk34MtisY6Dzr6hd4boGszy1kL1sRAsUh5jszKwzZuY6bU35W_aE8aYuXYXo27Cw.webp"},
            {"name": "Crocodillo Ananasinno", "img": "https://i.namu.wiki/i/81ldCM0MA_gmrUdwXBaPYydnqBmzy1xcX6-JIeuYe15j3rIB3396oE8w3jHy6q2yLVQAS0ebAIu9BI5axElbcGkc2HCr0fQBV7W7lHav141sh8W6br79iayBvvdbbJUvgYBnyExxIo0eVXCoKbJpGA.webp"},
            {"name": "Trippa Troppa Tralala Lirilì Rilà Tung Tung Sahur Boneca Tung Tung Tralalelo Trippi Troppa Crocodina", "img": "https://i.namu.wiki/i/nf0_1SDca-a7iyp3LSmGmMqIYNXZ8_t40FJ9gHx2ysherKU6hNwbIcYzBSrPJwAW6RrdEAZOS-pQgaygHAKK5QCjtFvRFkVLFz2AidVzPamj7frU6ePQhTA_wu8HdX05_EvwHrIdLfebT7ILWyc6Vg.webp"},
            {"name": "Tung Tung Tung Tung Tung Tung Tung Tung Tung Assassino Boneca", "img": "https://i.namu.wiki/i/bF_-kxC1C61PasDRoM1xIsHSOBTXlH6Nf9XTm9Texiz7JeSA0BQWfBEII3o5UlGpDU-kGUPjBPvmjjayxNpZ4xfpULHt31bUjHxO_7eIlGxZsj41VwW7-j3vd8M85CCOuS-9bKd4oLDDOXKA3u3xZw.webp"},
            {"name": "Giraffa Meloniera", "img": "https://i.namu.wiki/i/VYtcpg-dA4eNYeuLYwdZAPAZxTM9yNHw_GzYYRSrqKo6eS64rGuwMVwEOY_h8odpDWCbRizLkSMLFrQLATJbA-_1kvGBa6e6I10rWwhtlcAyN9LUvRST4yRkBv38PD3wGswLmnfw9HMG1DRg_nS6LA.webp"},
            {"name": "Pot hotspot", "img": "https://i.namu.wiki/i/vuMpWE6SCxUyOhUqfD2-Hf3Ap4lYOoZIdEQSHnO2QNCIQYnNcaqtwQOTtKIYB6gMYRNryb0U1C7qh7viMV0JSbUud6dCPxRc5bPaMGEa6TpcZOCJjcqOrmS-gl-TrVZ-8WMb6POGGoeaii3xM3Hz_A.webp"},
            {"name": "Svinino Bombondino", "img": "https://i.namu.wiki/i/1IBc1IovYoE2DfRgIYqOD0186N9WNzmMgQuvBC7O3IH7hjEbLoPFPWxGFA4A34K572fq_LbevAU5Cuq41Y406fbVd0IwfB7dlxLXn3efd72y7RS64ytwr9hF_6-VjH9KOs6sIvhxprYZyhgyfbUpxQ.webp"},
            {"name": "Bulbito Bandito Traktorito", "img": "https://i.namu.wiki/i/0zx7IvSdH8ui3rr3W6qz7aOgrVBhO2ES2khhoB0s0j6SDb7NEn0LEkgFo-YGN8u1fEyKiahkFbVUd_YoqflNBEcm5hGQI9cunMO9bmWc1KTE-V_QhiKX9bQUDKYkaiPDhY6j9js3NBQE7f6O60QLIQ.webp"},
            {"name": "Raccooni Watermelunni", "img": "https://i.namu.wiki/i/2_KDt7j19uMSdv7Az7SMcbmsEO1gk0M7UfMfq9N4hwbd8hGnkWm2k9zUy47jbWUihmllQUp1-NJc_N7_9ZBiboPu08TvLuYDbsVFUm9P2leFAN3nnEfHMSAYyAkd578amkQD1nMGOWLiVU4Mudhlnw.webp"},
            {"name": "Ganganzelli Trulala", "img": "https://i.namu.wiki/i/fUhdYeFmITD5YAxMQglbv477M7KSva3zvJW8PJtoIFWwtJpDBleOg4lAHJiZJUEC1QBys-7iXikTr7bm0PWEhfLwx4418OEhk03-K0OaxbKSQVUPAraqYS1frseI1F1qPI9Ir0HqoI8doStDcVN-2g.webp"},
            {"name": "Espressona Signora", "img": "https://i.namu.wiki/i/OZWngxEd8oTM-GYyE-jELeYKhrCoJ3qVkEoYWq1SAYVT6WV1F9W_s6oBfEBP-z8eP4MtSVMwBa2pJlVhS2s_WAgMwv2pj989pIEWv1jl-Qqpm0Y9V_MjcRfquIYyvzD8GJJpErb-yi0Xc8302HZHoQ.webp"},
            {"name": "Spaghetti Tualetti", "img": "https://i.namu.wiki/i/I8XcOJMHMTfryDMaiXk9sY3UMOl2iA8bZEHf2CZibjf2O4I8stuNSvgOI64u02aZq_qDhjMdSGuvei0ySjQPSwIZti75H46t2FiX6ZjpsknRERg3RYFLtZBXI-VIOUP_sxtfCqr9Yumj8GCZfHwCeg.webp"},
            {"name": "Cappuccino Babooino", "img": "https://i.namu.wiki/i/IPeEEv2ZI9h1-TKi3h7XgrKQximjHXRyaiChNfLNb1dIrEgbRcKqtuXpZ4I1ZAPm2gNge3SERZEUMJTHAl7pfmY0SxUikJYtv9HF9hmXG5ll0olqEJ0_JWlMPZSB9RoRhugd2rdEbPzMHN3X9UUpWA.webp"},
            {"name": "Cocossini Mama", "img": "https://i.namu.wiki/i/3x1CKPlD2uJ-4B354G8COfFjP1aET1--pbFSNjuN2r1A-zm_AQBGTPxbauPyxcRE4SYlnQ1yRGceeQxzcIXAfz99BmeMp62N7z4qqtOPIGLCl9BeEpI9cuNhOs9L0IJlJwyBzka29_oDqMfR8f7ZAg.webp"},
            {"name": "Snooffi Zeffirulli", "img": "https://i.namu.wiki/i/4YOLDJK4gyRrtNhJOX__8FCaIwqntbZh4Si_3oEd-r48jjHTquF2PTfnKMB94qInJAPr7fbtzcPUEDtc6dpUDVK77EG4Nomjs7SUKrlHQnkWyhmYLmqazQqKI-i8banj3Owq8WwsQGZjqZl4FT-8iA.webp"},
            {"name": "Perochello Lemonchello", "img": "https://i.namu.wiki/i/hlNzysS0-iUuIP4CKO_OdeX_NjpvfmTgbB6RWhFkZmVFiW_kr1C_wx3F22XVDZB7nCkAs8u1ze2hz0mNlYRIZs56FYRrFKHQLPu2WOqO-1lChc6xkFg6flA5QOKOjL-9yf60AvKG7vZZqFKbMwpYUw.webp"},
            {"name": "Tukanno Bananno", "img": "https://i.namu.wiki/i/V3KEDQO28fCtnhKBgaAIu_eWJ2vc9aeDIhXP8YVgkXKishr6RJw0tCsbGSUzb44LYTN-zewzbtnvFQeXgLiEtfh8Ehx0pNzMo41vNa7xdLidbGXK1KvpwfJKHgCBUbEtQD3XWNkLZnVX5QcLawyEsA.webp"},
            {"name": "Tob Tobi Tob Tob Tobi Tob", "img": "https://i.namu.wiki/i/n_7KPLk50pWKIQzibou-ppp9NUTBJC3LOzEolJv0TnQVOS_WaAvuKhQf-aDkawjfgyaErnsGCwLZxRt-fw8SheA4rYmV8ZnVG8mwn5nnkR25AwEvF0UBhqPVJ_WqqwtLYOOJTEV7iYWM5pz5Lw_78w.webp"},
            {"name": "Ananitto Giraffini", "img": "https://i.namu.wiki/i/9x2V0J7PezBhh6jAjZdRtv39K_Xdx4GQE8m_8MOnjtIgEIW1vTuSYC0om3KCOjaU2aQBUD4o7w9yjcLphBIL6lA0HXNlM60vIjHkv6vanmT6ASKrbrx78wAhUuA8gxGDTwqi-X9HhlasZvYSZB6TKQ.webp"},
        ]

        choice = random.choice(brainrots)

        embed = discord.Embed(title=choice.get("name"),
                              color=0xF4D03F)
        embed.set_image(
            url=choice.get("img")
        )

        await channel.send(embed=embed)

    # teh help command, add commands call, but not reactions
    if MESSAGE == "--help":
        print(f">>({user.name} {time.asctime()}) - A demandé de l'aide")
        await channel.send(
            "Commandes : \n"
            " **F** to pay respect\n"
            " **--serverInfo** pour connaître les infos du server\n"
            " **--clear** *nb* pour supprimer *nb* messages\n"
            " **--addInsult** pour ajouter des insultes et **tg** pour te faire insulter\n"
            " **--addBranlette** pour ajouter une expression de branlette et **branle** pour en avoir une\n"
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
            " **--rename** *nouveau_nom* pour changer mon nom sur ce serveur (admin only)\n"
            " **--resetname** pour remettre mon nom par défaut (admin only)\n"
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
        f">>({ctx.author.name} {time.asctime()}) - A demandé de clear {nombre} messages dans le channel {ctx.channel.name} du serveur {ctx.guild.name}"
    )
    messages = [message async for message in ctx.channel.history(limit=nombre + 1, oldest_first=False)]
    for message in messages:
        await message.delete()


@bot.command()  # repeat the 'text', and delete the original message
async def repeat(ctx, *text):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de répéter {' '.join(text)} messages"
    )
    messages = ctx.channel.history(limit=1)
    for message in messages:
        await message.delete()
    await ctx.send(" ".join(text))


@bot.command()  # show the number of people in the server, and its name
async def serverinfo(ctx):
    server = ctx.guild
    nbUsers = server.member_count
    text = f"Le serveur **{server.name}** contient **{nbUsers}** personnes !"
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé les infos du serveur {server.name}"
    )
    await ctx.send(text)


@bot.command()  # send the 26 possibilites of a ceasar un/decryption
async def crypt(ctx, *text):
    mot = " ".join(text)
    messages = await ctx.channel.history(limit=1).flatten()
    for message in messages:
        await message.delete()
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de crypter {mot} en {crypting(mot)}"
    )
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
        if user == "None":
            user = str(msg.author.name)
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
    global nbprime
    print(f">>({ctx.author.name} {time.asctime()}) - ", end="")
    if nb < 2:
        await ctx.send("Tu sais ce que ca veut dire 'prime number' ?")
        print("A demandé de calculer un nombre premier sen dessous de 2")
        return
    if nbprime > 2:
        await ctx.send("Attends quelques instants stp, je suis occupé...")
        print("A demandé trop de prime ->", nbprime)
        return
    nbprime += 1
    Fprime = open("txt/primes.txt", "r+")
    primes = Fprime.readlines()
    Fprime.close()
    biggest = int(primes[len(primes) - 1].replace("\n", ""))
    text = ""
    ratio_max = 1.02
    n_max = int(biggest * ratio_max)
    print(nb, biggest, n_max)

    if nb > biggest:
        if biggest % 2 == 0:
            biggest -= 1
        if nb <= n_max:
            await ctx.send("Primo no")
            return
            # for i in range(biggest, nb + 1, 2):
            #     if await is_prime(i):
            #         text += str(i) + "\n"
            # Fprime = open("txt/primes.txt", "a+")
            # Fprime.write(text)
            # Fprime.close()

            # if nb > 14064991:  # 8Mb file limit
            #     text = f"Je peux pas en envoyer plus que 14064991, mais tkt je l'ai calculé chez moi là"
            #     await ctx.send(text)
        else:
            text = f"Ca va me prendre trop de temps, on y va petit à petit, ok ? (max : {int(n_max)})"
            await ctx.send(text)
    else:
        text = f"Tous les nombres premiers jusqu'a 14064991 (plus grand : {biggest})"
        await ctx.send(text, file=discord.File("txt/prime.txt"))
    nbprime -= 1
    print(f"A demandé de claculer tous les nombres premiers juqu'à {nb}")

@bot.tree.command(name="isprime", description="Es-tu prime ?")
async def isPrime(interaction: discord.Interaction, nb: int):
    if nb > 99999997979797979797979777797:
        await interaction.send(
            "C'est trop gros, ca va tout casser, demande à papa Google :D", ephemeral=True)
        print("too big")
    elif await is_prime(nb):
        await interaction.add_reaction("👍")
        print("oui")
    else:
        await interaction.add_reaction("👎")
        print("non")


@bot.command()  # find if 'nb' is a prime number, reacts to the message
async def isPrime(ctx, nb: int):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé si {nb} est premier : ",
        end="",
    )
    if nb > 99999997979797979797979777797:
        await ctx.send(
            "C'est trop gros, ca va tout casser, demande à papa Google :D")
        print("too big")
    elif await is_prime(nb):
        await ctx.message.add_reaction("👍")
        print("oui")
    else:
        await ctx.message.add_reaction("👎")
        print("non")


@bot.command()  # send 'nb' random words of the dico, can repeat itself
async def randomWord(ctx, nb: int):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé {nb} mots aléatoires dans le dico : ",
        end="",
    )
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
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je rejoigne le vocal {channel} du serveur {ctx.guild.name}"
    )
    await channel.connect()


@bot.command()  # leaves it
async def leave(ctx):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je quitte le vocal {ctx.author.voice.channel} du serveur {ctx.guild.name}"
    )
    await ctx.voice_client.disconnect()


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
        f">>({ctx.author.name} {time.asctime()}) - A demandé que je traduise {toTranslate} en {fromLang} vers {toLang} : {text}"
    )
    await ctx.send(text)


@bot.command()
async def master(ctx, *text):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé un meme master ",
        end="")
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
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé un meme presentation ",
        end="",
    )
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
        end="",
    )
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
        await ctx.send(
            "D'accord, j'arrete de vous embeter ici... mais les commandes sont toujours dispos"
        )
        print("et je suis ban")


@bot.command()
async def unban(ctx):
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé de me débannir du channel {ctx.channel.name} du serveur {ctx.guild.name} : ",
        end="",
    )
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
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé une invitation dans le serveur {ctx.guild.name}"
    )
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
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé une game Among Us {ctx.guild.name}"
    )

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
            while tailleListe > 0 and tailleMin < tailleEquip[
                    0] and nbEquip < 8:
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
        firstMessage = await ctx.send(
            f"Réagis avec ✅ pour jouer ! Il reste {timeLeft} sec")

        yes = "✅"

        await firstMessage.add_reaction(yes)

        for _ in range(totalTime):
            time.sleep(1)
            timeLeft -= 1
            await firstMessage.edit(content=message +
                                    f" Il reste {str(timeLeft)} sec")
        await firstMessage.edit(content="Inscriptions fermées !")

        firstMessage = await firstMessage.channel.fetch_message(firstMessage.id
                                                                )
        users = set()
        for reaction in firstMessage.reactions:

            if str(reaction.emoji) == yes:
                async for user in reaction.users():
                    users.add(user)

        ids = []
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
                    url=
                    "https://tse1.mm.bing.net/th?id=OIP.3WhrRCJd4_GTM2VaWSC4SAAAAA&pid=Api"
                )

                for user in playersID[i]:
                    y += 1
                    embed.add_field(name=f"Joueur {str(y)}",
                                    value=f"<@!{str(user)}>",
                                    inline=True)
                await ctx.send(embed=embed)
            await ctx.send("**NEXT** pour relancer\n**END** poure terminer")

        def check(m):
            id_list = [
                321216514986606592,
                359743894042443776,
                135784465065574401,
                349548485797871617,
            ]
            return ((m.content == "NEXT" or m.content == "END")
                    and m.channel == ctx.channel and m.author.id in id_list)

        try:
            if len(ids) == 0:
                msg = await bot.wait_for("message", timeout=60.0, check=check)
            else:
                msg = await bot.wait_for("message",
                                         timeout=3600.0,
                                         check=check)
            if msg.content == "END":
                await ctx.send("**Fin de la partie...**")
                break
        except asyncio.TimeoutError:
            await ctx.send("**Fin de la partie...**")
            break
    print(
        f">>({ctx.author.name} {time.asctime()}) - La game Among Us a prit fin {ctx.guild.name}"
    )

FLAG = "`CYBN{Y0u_Kn0w_hOW_7o_Pl4Y_P0w3R_4}`"
FLAG2 = "`CYBN{DR4wiNG_w1Th0Ut_P4p3r_c4N_H4pP3n}`"

@bot.tree.command(name="flag", description="Envoie un message éphémère")
async def flag(interaction: discord.Interaction):
    win, draw = [int(s) for s in (await getScoreLeaderBoard(interaction.user.id, filename="pve.txt"))]
    if win >= 3:
        await interaction.response.send_message("Allez tiens ton flag : " + FLAG, ephemeral=True)
    if draw > 0:
        await interaction.response.send_message("Ca c'est le bonus pour l'égalité : " + FLAG2, ephemeral=True)
    if not(draw > 0) and not(win >= 3):
        await interaction.response.send_message("Va falloir gagner au Puissance 4 si tu veux un flag : `--p4`", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wtf, envoi un MP aux admins en montrant ce message stp : {draw}, {win}, {interaction.user.id}", ephemeral=True)


#@bot.tree.command(name="puissance4", description="Joue au puissance 4 !")
@bot.command()
async def puissance4(interaction):
    print(
        f">>({interaction.author.name} {time.asctime()}) - A lancé une partie de puissance 4 {interaction.guild.name}"
    )

    import copy

    ROWS = 6
    COLS = 7

    def valid_moves(grid):
        return [c for c in range(COLS) if grid[0][c] == 0]

    def simulate_move(grid, col, player):
        new_grid = copy.deepcopy(grid)
        for r in reversed(range(ROWS)):
            if new_grid[r][col] == 0:
                new_grid[r][col] = player
                break
        return new_grid

    def is_winning_move(grid, player):
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(grid[r][c+i] == player for i in range(4)):
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(grid[r+i][c] == player for i in range(4)):
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(grid[r+i][c+i] == player for i in range(4)):
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(grid[r-i][c+i] == player for i in range(4)):
                    return True
        return False

    def evaluate_window(window, player):
        opponent = 2 if player == 1 else 1
        score = 0
        # Offensive
        if window.count(player) == 4:
            score += 200
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 25
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 6
        # Défensive — mais moins pénalisante qu’avant
        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 40
        elif window.count(opponent) == 2 and window.count(0) == 2:
            score -= 2
        return score

    def score_position(grid, player):
        score = 0
        # Bonus central plus marqué
        center_col = [grid[r][COLS // 2] for r in range(ROWS)]
        score += center_col.count(player) * 6
        # Lignes horizontales
        for r in range(ROWS):
            for c in range(COLS - 3):
                score += evaluate_window([grid[r][c+i] for i in range(4)], player)
        # Colonnes verticales
        for r in range(ROWS - 3):
            for c in range(COLS):
                score += evaluate_window([grid[r+i][c] for i in range(4)], player)
        # Diagonales
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += evaluate_window([grid[r+i][c+i] for i in range(4)], player)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += evaluate_window([grid[r-i][c+i] for i in range(4)], player)
        return score

    def future_win_potential(grid, player):
        """Nombre de coups qui mèneraient à une victoire au prochain tour."""
        count = 0
        for col in valid_moves(grid):
            if is_winning_move(simulate_move(grid, col, player), player):
                count += 1
        return count

    def minimax(grid, depth, maximizing, alpha, beta, offensive_factor):
        bot = 1
        human = 2
        valid_cols = valid_moves(grid)
        if depth == 0 or not valid_cols:
            return (None, score_position(grid, bot))

        if maximizing:
            value = -float("inf")
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_grid = simulate_move(grid, col, bot)
                if is_winning_move(new_grid, bot):
                    return (col, 1_000_000)
                _, new_score = minimax(new_grid, depth - 1, False, alpha, beta, offensive_factor)
                # 🔥 Bonus offensif : créer des menaces doubles
                new_score += future_win_potential(new_grid, bot) * 20 * offensive_factor
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float("inf")
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_grid = simulate_move(grid, col, human)
                if is_winning_move(new_grid, human):
                    return (col, -1_000_000)
                _, new_score = minimax(new_grid, depth - 1, True, alpha, beta, offensive_factor)
                new_score -= future_win_potential(new_grid, human) * 15
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    def choose_ai_move(grid, difficulty="moyen", playstyle="offensif"):
        """
        difficulty: "facile", "moyen", "difficile"
        playstyle: "equilibre", "offensif", "defensif"
        """
        bot = 1
        human = 2
        valid_cols = valid_moves(grid)

        # Config selon niveau
        if difficulty == "facile":
            depth = 1
            randomness = 0.3
        elif difficulty == "moyen":
            depth = 2
            randomness = 0.1
        else:
            depth = 3
            randomness = 0.07

        # Ajuste le style de jeu
        offensive_factor = 1.0
        if playstyle == "offensif":
            offensive_factor = 1.5
        elif playstyle == "defensif":
            offensive_factor = 0.7

        # 1️⃣ Gagner immédiatement
        for col in valid_cols:
            if is_winning_move(simulate_move(grid, col, bot), bot):
                return col

        # 2️⃣ Bloquer une victoire immédiate
        for col in valid_cols:
            if is_winning_move(simulate_move(grid, col, human), human):
                return col

        # 3️⃣ Choisir via minimax
        col, _ = minimax(grid, depth, True, -float("inf"), float("inf"), offensive_factor)

        # 4️⃣ 10 % de hasard
        if random.random() < randomness:
            col = random.choice(valid_cols)
        return col

    async def send_mp(user, type="win"):
        time.sleep(4)
        if type == "win":
            await user.send("Coucou")
            time.sleep(4)
            await user.send("Ok bien joué")
            time.sleep(7)
            await user.send("T'es sûr de mériter le flag ?")
            time.sleep(9)
            await user.send("Bon vasy le flag tu me fais pitié : `CYBN{Y0u_Kn0w_hOW_7o_Pl4Y_P0w3R_4}`")
        elif type == "draw":
            await user.send("Stylé l'égalité, je pensais pas que ca arriverait :clap:")
            time.sleep(4)
            await user.send("Tu es de ma trempe pour réussir ça, j'aime bien, bel adversaire")
            time.sleep(3)
            await user.send("Allez tiens un petit cadeau, il rapporte pas beaucoup de points mais c'est toujours sympa : `CYBN{DR4wiNG_w1Th0Ut_P4p3r_c4N_H4pP3n}`")

    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
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
                    await gridMessage.remove_reaction(str(numbers[col]),
                                                      bot.user)
                    numbers[col] = "#️⃣"
                break
        return i >= 0

    async def checkWin(grid, tour):
        for row in range(len(grid) - 1, -1, -1):
            for col in range(0, len(grid[row])):
                if (await checkRight(grid, row, col, 0, tour)
                        or await checkLeft(grid, row, col, 0, tour)
                        or await checkUp(grid, row, col, 0, tour)
                        or await checkLeftDiag(grid, row, col, 0, tour)
                        or await checkRightDiag(grid, row, col, 0, tour)):
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

    yellowMessage = await interaction.send("**⬇ Joueur jaune ⬇**")
    await yellowMessage.add_reaction("🟡")

    def check(reaction, user):
        return (user != bot.user and str(reaction.emoji) == "🟡"
                and reaction.message.id == yellowMessage.id)

    try:
        reaction, user = await bot.wait_for("reaction_add",
                                            timeout=60.0,
                                            check=check)
        yellow = user
    except asyncio.TimeoutError:
        await yellowMessage.edit(content="Pas de joueur jaune ❌")
        return
    print(
        f">>({yellow} {time.asctime()}) - Est le joueur jaune {interaction.guild.name}"
    )

    mode = "pvp"

    if mode == "pvp":
        redMessage = await interaction.send("**⬇ Joueur rouge ⬇**")
        await redMessage.add_reaction("🔴")

        def check(reaction, user):
            return (user != bot.user and user != yellow
                    and str(reaction.emoji) == "🔴"
                    and reaction.message.id == redMessage.id)

        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                timeout=60.0,
                                                check=check)
            red = user
        except asyncio.TimeoutError:
            await redMessage.edit(content="Pas de joueur rouge ❌")
            return
        print(f">>({red} {time.asctime()}) - Est le joueur red {interaction.guild.name}")
    elif mode == "pve":
        red = bot.user
        redMessage = await interaction.send("Je serai l'adversaire rouge, tiens-toi prêt 😈")

    yellowPing = "<@!" + str(yellow.id) + "> 🟡"
    redPing = "<@!" + str(red.id) + "> 🔴"

    text = yellowPing + " et " + redPing + " tenez vous prêts !"
    gridMessage = await interaction.send(text)

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
            await updateGrid(grid,
                             "Tour n°" + str(tour) + " - " + redPing + "\n",
                             gridMessage)
        else:
            await updateGrid(grid,
                             "Tour n°" + str(tour) + " - " + yellowPing + "\n",
                             gridMessage)

        if tour % 2 == 0:
            if mode == "pvp":
                def check(reaction, user):
                    return (user == red and str(reaction.emoji) in numbers
                            and reaction.message.id == gridMessage.id)
            elif mode == "pve":
                col = choose_ai_move(grid, difficulty="difficile", playstyle="offensif")
                await addChip(grid, col, tour)
                # Do some auto play

        else:

            def check(reaction, user):
                return (user == yellow and str(reaction.emoji) in numbers
                        and reaction.message.id == gridMessage.id)

        try:
            if not(tour % 2 == 0 and mode == "pve"):
                reaction, user = await bot.wait_for("reaction_add",
                                                    timeout=120.0,
                                                    check=check)

                await gridMessage.remove_reaction(reaction, user)

                for i in range(len(numbers)):
                    if str(reaction.emoji) == numbers[i]:
                        await addChip(grid, i, tour)

            if tour > 6 and await checkWin(grid, tour):
                sent = False
                if tour % 2 == 0:
                    loser   = yellow
                    winner  = red
                    ping    = redPing
                    if mode == "pve":
                        messages = [
                            "Hop-là, ca dégage la racaille", 
                            "Robots 1 - 0 Humain", 
                            "Pas de flag pour toi ce soir 🤠", 
                            "Tu pensais vraiment pouvoir me battre ?",
                            "Trop facile",
                            "Ptdr tu l'avais pas vu genre ?",
                            "C'est pas avec ce niveau que tu arriveras à flagguer...",
                            "Try again. Noob.",
                            "Je me suis presque ennuyé tiens",
                            "Retourne aux challs Intro, ils sont plus de ton niveau"
                        ]
                        print(
                            f">>({loser} {time.asctime()}) - A perdu contre le bot au P4 (noob)"
                        )
                        await changeScoreLeaderboard(loser.id, loser, win=False, filename="pve.txt")
                        text = f"{ping} gagne ! (c'est moi)\n{random.choice(messages)}"
                else:
                    loser   = red
                    winner  = yellow
                    ping    = yellowPing
                    if mode == "pve":
                        print(
                            f">>({winner} {time.asctime()}) - A gagné contre le bot au P4 (gg)"
                        )
                        await changeScoreLeaderboard(winner.id, winner, win=True, filename="pve.txt")
                        score = int((await getScoreLeaderBoard(winner.id, filename="pve.txt"))[0])
                        if score == 3:
                            text = ping + " remporte ses 3 victoires d'affilé ! Voilà le flag : ||t'as vraiment cru que j'allais donner le flag en public ? Regarde tes DM petit filou, ou fais `/flag`||"
                            await interaction.send(text)
                            await send_mp(winner)
                            sent = True
                            # send MP
                            # flag, gg
                        elif score > 3:
                            text = f"Allez t'as gagné {ping}, t'es content avec tes {score} victoires d'affilé ? T'as déjà eu ton flag, va jouer ailleurs..."
                            # ouais bon on a compris
                        else:
                            text = f"{ping} remporte la victoire ! **Score actuel : {score} / 3** - Plus que {3-score} avant le flag"
                            # play again
                print(
                    f">>({winner} {time.asctime()}) - Est le gagnant vs {loser} ! {interaction.guild.name}"
                )
                if mode == "pvp":
                    await addScoreLeaderboard(winner.id, winner)
                    await addLoseLeaderboard(loser.id, loser)
                await gridMessage.add_reaction("✅")
                await updateGrid(
                    grid,
                    "Tour n°" + str(tour) + " - " + ping + "\n",
                    gridMessage,
                )
                if mode == "pvp":
                    text = (ping + " gagne ! **Score actuel : " +
                            (await getScoreLeaderBoard(winner.id))[0] +
                            " victoires** - " +
                            await getPlaceLeaderbord(winner.id))
                if not sent:
                    await interaction.send(text)
                end = True

            elif tour >= 42:
                await gridMessage.add_reaction("✅")
                print(
                    f">>({red} et {yellow} {time.asctime()}) - Sont à égalité ! {interaction.guild.name}"
                )
                if mode == "pvp":
                    await addScoreLeaderboard(yellow.id, yellow)
                    await addScoreLeaderboard(red.id, red)
                    text = (
                        "Bravo à vous deux, c'est une égalité ! Bien que rare, ça arrive... Donc une victoire en plus chacun ! gg\n"
                        "**Score de " + yellowPing + " : " +
                        (await getScoreLeaderBoard(yellow.id))[0] +
                        " victoires !**\n **Score de " + redPing + " : " +
                        (await getScoreLeaderBoard(red.id))[0] + " victoires !**")
                    await interaction.send(text)
                elif mode == "pve":
                    text = "Ah bah une égalité tiens, c'est rare... Viens on en discute en MP? Sinon fais `/flag`"
                    await changeScoreLeaderboard(yellow.id, yellow, win=False, filename="pve.txt", draw=True)
                    await interaction.send(text)
                    await send_mp(yellow, type="draw")

                end = True

        except asyncio.TimeoutError:
            await gridMessage.add_reaction("❌")
            await gridMessage.add_reaction("⌛")
            if tour % 2 == 0:
                print(
                    f">>({yellow} {time.asctime()}) - Est le gagnant ! {interaction.guild.name}"
                )
                await updateGrid(
                    grid, "Tour n°" + str(tour) + " - " + redPing + "\n",
                    gridMessage)
                await addScoreLeaderboard(yellow.id, yellow)
                await addLoseLeaderboard(red.id, red)
                text = (
                    redPing + " n'a pas joué ! Alors **" + yellowPing +
                    " gagne !** (c'est le jeu ma pov lucette)\n Score actuel : "
                    + (await getScoreLeaderBoard(yellow.id))[0] + " victoires - " +
                    await getPlaceLeaderbord(yellow.id))

            else:
                print(
                    f">>({red} {time.asctime()}) - Est le gagnant ! {interaction.guild.name}"
                )
                await updateGrid(
                    grid, "Tour n°" + str(tour) + " - " + redPing + "\n",
                    gridMessage)

                if mode == "pvp":
                    await addScoreLeaderboard(red.id, red)
                    await addLoseLeaderboard(yellow.id, yellow)
                    text = (
                        yellowPing + " n'a pas joué ! Alors **" + redPing +
                        " gagne !** (fallait jouer, 2 min t'es large !)\n Score actuel : "
                        + (await getScoreLeaderBoard(red.id))[0] + " victoires - " +
                        await getPlaceLeaderbord(red.id))
                elif mode == "pve":
                    await changeScoreLeaderboard(yellow.id, yellow, win=False, filename="pve.txt")
                    text = f"J'en connais un qui est parti flag d'autres challs, et a abandonné le miens... Bah t'as perdu {yellowPing}, cheh"
            await interaction.send(text)
            end = True

        tour += 1


@bot.command()
async def p4(ctx):
    await puissance4(ctx)


async def updateLeaderboard(liste, filename="leaderboard.txt"):
    file = open("txt/" + filename, "w+")
    for line in liste:
        line = "-".join(line)
        if line[len(line) - 1] != "\n":
            line += "\n"
        file.write(line)
    file.close()


async def getScoreLeaderBoard(id, filename="leaderboard.txt"):
    file = open("txt/" + filename, "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        if str(id) in leaderboard[i]:
            leaderboard[i] = leaderboard[i].split("-")
            return leaderboard[i][1].replace("\n", ""), leaderboard[i][2].replace("\n", "")
    return "0", "0"

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


async def changeScoreLeaderboard(id, name, win=False, filename="leaderboard.txt", draw=False):
    file = open("txt/" + filename, "r+")
    leaderboard = file.readlines()
    file.close()
    isIn = False
    for i in range(len(leaderboard)):
        leaderboard[i] = leaderboard[i].split("-")
        if str(id) in leaderboard[i]:
            isIn = True
            leaderboard[i][1] = "0" if not win else str(int(leaderboard[i][1]) + 1)
            leaderboard[i][2] = leaderboard[i][2] if not draw else "1"
            if int(leaderboard[i][2]) == 0:
                leaderboard[i][3] = leaderboard[i][1]
            else:
                leaderboard[i][3] = str(
                    round(
                        float(leaderboard[i][1]) / float(leaderboard[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-1-0-1-" + str(name) + "\n").split("-")
        leaderboard.append(line)

    print(leaderboard)
    leaderboard.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard, filename=filename)


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
            if int(leaderboard[i][2]) == 0:
                leaderboard[i][3] = leaderboard[i][1]
            else:
                leaderboard[i][3] = str(
                    round(
                        float(leaderboard[i][1]) / float(leaderboard[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-1-0-1-" + str(name) + "\n").split("-")
        leaderboard.append(line)

    print(leaderboard)
    leaderboard.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard)


async def addLoseLeaderboard(id, name):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    isIn = False
    for i in range(len(leaderboard)):
        leaderboard[i] = leaderboard[i].split("-")
        if str(id) in leaderboard[i]:
            isIn = True
            leaderboard[i][2] = str(int(leaderboard[i][2]) + 1)
            if int(leaderboard[i][2]) == 0:
                leaderboard[i][3] = leaderboard[i][1]
            else:
                leaderboard[i][3] = str(
                    round(
                        float(leaderboard[i][1]) / float(leaderboard[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-0-1-0-" + str(name) + "\n").split("-")
        leaderboard.append(line)

    leaderboard.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard)


@bot.command()
async def classement(ctx):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        leaderboard[i] = leaderboard[i].split("-")

    numbers = [
        "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
    ]
    text = "Le classement du puissance 4 est composé de : \n\n"
    leaderSize = 5
    if len(leaderboard) <= leaderSize:
        if len(leaderboard) <= 0:
            text = "Bah ya personne... ***jouez !***"
        else:
            text += "Avec le plus de victoires : \n"
            for i in range(len(leaderboard)):
                name = leaderboard[i]
                text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                         "** avec **" + name[1] + " victoires**\n")

            leaderboard.sort(reverse=True, key=lambda score: float(score[3]))
            text += "\nAvec le plus grand ratio Victoire/Défaite\n"
            for i in range(len(leaderboard)):
                name = leaderboard[i]
                text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                         "** avec **" + name[3] + " V/D** (" + str(
                             round(
                                 int(name[1]) /
                                 (int(name[1]) + int(name[2])) * 100, 2)) +
                         "%)\n")
    else:
        text += "Avec le plus de victoires : \n"
        for i in range(leaderSize):
            name = leaderboard[i]
            text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                     "** avec **" + name[1] + " victoires**\n")
        text += "*+" + str(len(leaderboard) -
                           leaderSize) + " autres joueurs*\n\n"

        leaderboard.sort(reverse=True, key=lambda score: float(score[3]))
        text += "Avec le plus grand ratio Victoire/Défaite\n"
        for i in range(leaderSize):
            name = leaderboard[i]
            text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                     "** avec **" + name[3] + " V/D** (" + str(
                         round(
                             int(name[1]) /
                             (int(name[1]) + int(name[2])) * 100, 2)) + "%)\n")
        text += "*+" + str(len(leaderboard) - leaderSize) + " autres joueurs*"

    await ctx.send(text)


@bot.command()
async def rank(ctx):
    await classement(ctx)


@bot.command()
async def monRang(ctx):
    file = open("txt/leaderboard.txt", "r+")
    leaderboard = file.readlines()
    file.close()
    for i in range(len(leaderboard)):
        leaderboard[i] = leaderboard[i].split("-")

    for i in range(len(leaderboard)):
        if str(ctx.author.id) in leaderboard[i]:
            await ctx.send(
                f"Tu es **{str(i + 1)}e/{len(leaderboard)}** des victoires,"
                f" avec **{leaderboard[i][1]} victoires** !")
            break
    leaderboard.sort(reverse=True, key=lambda score: float(score[3]))
    print(leaderboard)
    for i in range(len(leaderboard)):
        name = leaderboard[i]
        if str(ctx.author.id) in name:
            await ctx.send(
                f"Tu es **{str(i + 1)}e/{len(leaderboard)}** des ratios,"
                f" avec **{name[3]} V/D**"
                f" ({str(round(int(name[1]) / (int(name[1]) + int(name[2])) * 100, 2))}%) !"
            )
            print(round(33.3333333333333333, 2))
            return
    await ctx.send(
        "Mmmmh... Tu n'es pas dans le classement, essaies de jouer !")


@bot.command()
async def myRank(ctx):
    await monRang(ctx)


@bot.command()
async def github(ctx):
    await ctx.send("Mais avec plaisir !\nhttps://github.com/NozyZy/Le-ptit-bot")


@bot.command()
async def ask(ctx):
    text = ctx.message.content.replace(str(ctx.prefix) + str(ctx.command), "")
    text.replace("’", "")
    print(
        f">>({ctx.author.name} {time.asctime()}) - A demandé '{text}' - {ctx.guild.name} : ",
        end="",
    )

    if text == "":
        await ctx.send("Pose une question andouille")
        return

    if len(text) < 4:
        await ctx.send("Je vais avoir du mal à te répondre là 🤔")
        return

    if text[len(text) - 1] != "?":
        await ctx.send("C'est pas une question ça tu sais ?")
        return

    counter = 0
    for letter in text:
        counter += ord(letter)

    counter += ctx.author.id

    responses = [
        "Bah oui",
        "Qui sait ? 👀",
        "Absolument pas. Non. Jamais.",
        "Demande à ta mère",
        "Bientôt, tkt frr",
        "https://tenor.com/view/well-yes-but-actually-no-well-yes-no-yes-yes-no-gif-13736934",
        "Peut-être bien écoute",
        "Carrément ma poule",
    ]

    await ctx.send(responses[counter % len(responses)])
    print(responses[counter % len(responses)])


@bot.command()
async def skin(ctx):
    url = "https://mskins.net"
    response = requests.get(url + "/en/skins/random")
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.find_all("a")[62]
    img = tag.find("img")["src"]
    author = img.split("/")[-1].split("-")[0]
    embed = discord.Embed(
        description="Skin of %s" % author,
        title="Random minecraft skin",
        color=0xECCE8B,
        url=url + "/en/skins/random",
    )
    embed.set_thumbnail(
        url=
        "https://imagepng.org/wp-content/uploads/2017/08/minecraft-icone-icon.png"
    )
    embed.set_author(
        name=author,
        url=tag["href"],
        icon_url=
        "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
    )
    embed.set_image(url=url + img)
    embed.set_footer(text="%s - by mskins.net" % author)
    await ctx.send("Get skinned", embed=embed)

@bot.command()
async def panda(ctx):
    url = "https://generatorfun.com"
    response = requests.get(url + "/random-panda-image")
    soup = BeautifulSoup(response.text, "html.parser")
    img = soup.find_all("img")[0]["src"]
    embed = discord.Embed(
        title="Take that Panda",
        color=0xffffff,
        url=url + "/random-panda-image",
    )
    embed.set_author(
        name=ctx.message.author.display_name,
        icon_url=
        "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
    )
    embed.set_image(url=url + "/" + img)
    embed.set_footer(text="panda - by generatorfun.com")
    await ctx.send("🐼", embed=embed)

ips = list(range(3, 40)) + list(range(80, 150))

@bot.command()
async def dhcp(ctx, iprange: str):
    if ips:
        message = "Réagis avec ✅ pour obtenir une ip !"
        totalTime = 3
        timeLeft = totalTime
        firstMessage = await ctx.send(
            f"Réagis avec ✅ pour obtenir une ip ! Il reste {timeLeft} sec")

        yes = "✅"

        await firstMessage.add_reaction(yes)

        for _ in range(totalTime):
            time.sleep(1)
            timeLeft -= 1
            await firstMessage.edit(content=message +
                                    f" Il reste {str(timeLeft)} sec")
        await firstMessage.edit(content="Haha ya plus d'IP !")

        firstMessage = await firstMessage.channel.fetch_message(firstMessage.id)
        users = set()
        for reaction in firstMessage.reactions:

            if str(reaction.emoji) == yes:
                async for user in reaction.users():
                    if user.id != bot.user.id:
                        users.add(user)
        text = """
        Suis les étapes suivantes :
        - Paramètres **Ethernet**
            - Paramètres **IP** : modifier
        - Manuel
        - IPv4 : **activé**
        - Adresse ip **{0}.{1}**
        - **SI WINDOWS 11 :**
            - Préfixe sous-réseaux : **255.255.255.0**
        - **SI WINDOWS 10 :**
            - Longueur du préfixe sous-réseaux : **24**
        - Passerelle : **10.10.51.1**
        """

        for i in range(5):
            for user in users:
                ip = ips.pop(0)
                await user.send(text.format(iprange, ip))
    else:
        await ctx.send("Sah ya plus d'IP")


@bot.command()
async def activity(ctx):
    args = ctx.message.content.replace(str(ctx.prefix) + str(ctx.command), "").strip()
    participants = 0
    if len(args) > 0 and args.isnumeric() and int(args) > 0:
        participants = int(args)
    url = "https://www.boredapi.com/api/activity"
    if participants > 0:
        url += f"?participants={participants}"

    response = requests.get(url)
    json_p = response.content.decode('utf-8')
    activity = json.loads(json_p)
    author = ctx.message.author.display_name
    embed = discord.Embed(
        title=activity['activity'],
        color=0xECCE8B,
        url=activity['link'],
    )
    embed.add_field(name="Type", value=activity['type'])
    embed.add_field(name="Participants", value=activity['participants'])
    embed.add_field(name="Difficulty", value=str(100*(1-activity['accessibility'])) + "%")
    embed.set_author(
        name=author,
        url=url,
        icon_url=
        "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
    )
    embed.set_footer(text="provided by boredapi.com")
    await ctx.send("Use `--activity <nb>` to chose participants", embed=embed)

@bot.command()
async def sync(ctx):
    print("sync command")
    if ctx.author.id == 359743894042443776:
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
    else:
        await ctx.send('You must be the owner to use this command!')

bot.run(secret.TOKEN)

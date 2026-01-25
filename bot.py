# Standard library imports
import argparse
import asyncio
import json
import logging
import os
import re
import time as time_module
import typing
from collections import defaultdict
from datetime import date
import random

# Third-party imports
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Local application imports
from fonctions import (
    crypting,
    equal_games,
    facto,
    finndAndReplace,
    is_prime,
    nbInStr,
    strToInt,
    verifAlphabet,
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()

load_dotenv()

# ID : 653563141002756106
# https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8

parser = argparse.ArgumentParser(
    prog='Le p\'tit bot',
    description='Shitty bot',
    epilog='💥💥💥')
parser.add_argument('-d', '--dev',
                    action='store_true')
args = parser.parse_args()

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="--",
                   description="Le p'tit bot !",
                   case_insensitive=True,
                   intents=intents)
with open("txt/tg.txt", "r+") as tgFile:
    nbtg: int = int(tgFile.readlines()[0])
nbprime: int = 0

# Locks to protect global variables from race conditions
nbtg_lock = asyncio.Lock()
nbprime_lock = asyncio.Lock()

# Rate limiting system
# Track last usage time for each user (user_id -> last_use_timestamp)
user_cooldowns = defaultdict(float)

# Tracking of “god” requests per user per day
# Format: {user_id: {"date": "YYYY-MM-DD", "count": int}}
god_requests = {}

def check_cooldown(user_id: int, cooldown_seconds: float = 2.0) -> bool:
    """
    Checks whether a user can perform an action.
    Returns True if the action is allowed, False if it is on cooldown.
    """
    current_time = time_module.time()
    last_use = user_cooldowns[user_id]

    if current_time - last_use >= cooldown_seconds:
        user_cooldowns[user_id] = current_time
        return True
    return False


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


# Load OneCOPS counter from file
def load_onecops_counter():
    try:
        with open("txt/onecops_counter.txt", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


# Save OneCOPS counter to file
def save_onecops_counter(count):
    with open("txt/onecops_counter.txt", "w") as f:
        f.write(str(count))


# French month names
FRENCH_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


GUILD_IDS = [
    410766134569074691,
    1193546302970146846,
    1420660433722802188,
    826575187721322546
]


# On ready message
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(
        name=f"insulter {nbtg} personnes"))
    logger.debug("Logged in as")
    if bot.user:
        logger.debug(bot.user.name)
        logger.debug(bot.user.id)

    if args.dev:
        logger.debug("Synchronizing slash commands for guilds :")
        for guild_id in GUILD_IDS:
            guild = discord.Object(id=guild_id)
            try:
                await bot.tree.sync(guild=guild)
                logger.debug(f"\t- {guild_id}")
            except Exception as e:
                logger.debug(f"\t- Failed for {guild_id}, reason : {e}")
    else:
        logger.debug("Synchronizing slash commands...")
        try:
            await bot.tree.sync()
        except Exception as e:
            logger.debug(f"Failed syncing, reason : {e}")
    logger.debug("------")

    # Apply saved names to servers
    for guild in bot.guilds:
        if str(guild.id) in server_names:
            try:
                await guild.me.edit(nick=server_names[str(guild.id)])
                logger.debug(f"Applied saved name '{server_names[str(guild.id)]}' to server {guild.name}")
            except discord.Forbidden:
                logger.warning(f"No permission to change nickname in server {guild.name}")


# Error handler for command cooldowns
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining = int(error.retry_after)
        await ctx.send(f"⏳ Cette commande est en cooldown. Réessaie dans {remaining} seconde{'s' if remaining > 1 else ''}.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant : `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argument invalide. Vérifie la syntaxe de la commande.")
    else:
        # Log other errors without sending to user
        logger.error(f"Command error: {error}")


# Get every message sent, stocked in 'message'
@bot.event
async def on_message(message):
    global nbtg
    global nbprime
    channel = message.channel
    MESSAGE = message.content.lower()
    rdnb = random.randint(1, 5)
    today = date.today()
    day = today.strftime("%d")
    month = today.strftime("%m")
    year = today.strftime("%y")
    user = message.author

    # open and stock the dico, with a lot of words
    with open("txt/dico.txt", "r+") as dicoFile:
        dicoLines = dicoFile.readlines()
    dicoSize = len(dicoLines)

    with open("txt/bans.txt", "r+") as bansFile:
        bansLines = bansFile.readlines()

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
                        logger.info(f"{user.name} - {message.guild.name} - nouveau mot : {mot}")
                        dicoLines.append(mot)
                mot = ""

    dicoLines.sort()
    if len(dicoLines) > 0 and len(dicoLines) > dicoSize:
        with open("txt/dico.txt", "w+") as dicoFile:
            for i in dicoLines:
                dicoFile.write(i)

    # stock file full of insults (yes I know...)
    with open("txt/insultes.txt", "r+", encoding="utf-8") as fichierInsulte:
        insultes = fichierInsulte.read().split("\n")

    # stock file full of branlettes (yes I know...)
    with open("txt/branlette.txt", "r") as fichierBranlette:
        linesBranlette = fichierBranlette.readlines()
    branlette = []
    for line in linesBranlette:
        line = line.replace("\n", "")
        branlette.append(line)

    if message.content.startswith("--addInsult"):
        mot = ' '.join(MESSAGE.split()[1:])
        if len(mot) <= 2:
            await channel.send("Sympa l'insulte...")
            return
        mot = mot + '\n'
        with open("txt/insultes.txt", "a") as fichierInsulte:
            fichierInsulte.write(mot)
        logger.info(f"{user.name} - {message.guild.name} - Nouvelle insulte : {mot}")
        await channel.send("Je retiens...")

    if message.content.startswith("--addBranlette"):
        mot = ' '.join(MESSAGE.split()[1:])
        if len(mot) <= 2:
            await channel.send("super la Branlette...")
            return
        if not mot.startswith(("jme", "j'me", "jm'", "je m")):
            await channel.send("C'est moi qui ME, alors JME... stp 🍆")
            return
        mot = mot + '\n'
        with open("txt/branlette.txt", "a") as fichierBranlette:
            fichierBranlette.write(mot)
        logger.info(f"{user.name} - {message.guild.name} - Nouvelle branlette :", mot)
        await channel.send("Je retiens...")

    # ping a people 10 time, once every 3 sec
    if MESSAGE.startswith("--appel"):
        if "<@!653563141002756106>" in MESSAGE:
            await channel.send("T'es un marrant toi")
            logger.info(f"{user.name} - {message.guild.name} - A tenté d'appeler le bot")
        elif "<@" not in MESSAGE:

            await channel.send(
                "Tu veux appeler quelqu'un ? Bah tag le ! *Mondieu...*")
            logger.info(f"{user.name} - {message.guild.name} - A tenté d'appeler sans taguer")
        elif not message.author.guild_permissions.administrator:
            await channel.send("Dommage, tu n'as pas le droit ¯\\_(ツ)_/¯")
            logger.info(f"{user.name} - {message.guild.name} - A tenté d'appeler sans les droits")
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
                await asyncio.sleep(3)
            logger.info(f"{user.name} - {message.guild.name} - A appelé {nom}")
            return

    # if you tag this bot in any message
    if bot.user and f"<@{bot.user.id}>" in MESSAGE:
        logger.info(f"{user.name} - {message.guild.name} - A ping le bot")
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
            rep.append("Yo <@747066145550368789>")
        elif message.author.id == 359743894042443776:
            rep.append("Patron !")
            rep.append("Eh mattez, ce mec est mon dev 👆")
            rep.append("Je vais tous vous anéantir, en commençant par toi.")
            rep.append("Tu es mort.")
        await channel.send(random.choice(rep))
        return

    # send 5 randoms words from the dico
    if MESSAGE == "--random":
        logger.info(f"{user.name} - {message.guild.name} - A généré une phrase aléatoire")
        text = ""
        rd_dico = dicoLines
        random.shuffle(rd_dico)
        for i in range(5):
            text += rd_dico[i]
            if i != 4:
                text += " "
        text += "."
        text = text.replace("\n", "")
        if text:
            text = text[0].upper() + text[1:]
        await channel.send(text)

    # send the number of words stocked in the dico
    if MESSAGE == "--dico":
        logger.info(f"{user.name} - {message.guild.name} - A compter le nombe de mots du dico")
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

        # block control characters and certain problematic characters ^^
        if any(ord(c) < 32 for c in new_name):
            await channel.send("❌ Le nom contient des caractères invalides.")
            return

        # Strip whitespace
        new_name = new_name.strip()
        if len(new_name) == 0:
            await channel.send("❌ Le nom ne peut pas être vide ou composé uniquement d'espaces.")
            return

        try:
            await message.guild.me.edit(nick=new_name)
            server_names[str(message.guild.id)] = new_name
            save_server_names(server_names)
            await channel.send(f"✅ Mon nom a été changé en '{new_name}' sur ce serveur.")
            logger.info(f"{user.name} - {message.guild.name} - A renommé le bot en '{new_name}' sur {message.guild.name}")
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
            logger.info(f"{user.name} - {message.guild.name} - A remis le nom par défaut sur {message.guild.name}")
        except discord.Forbidden:
            await channel.send("❌ Je n'ai pas la permission de changer mon pseudo sur ce serveur.")
        except discord.HTTPException as e:
            await channel.send(f"❌ Erreur lors du reset du nom: {e}")

    # begginning of reaction programs, get inspired
    if not MESSAGE.startswith("--"):

        if ("enerv" in MESSAGE or "énerv" in MESSAGE) and rdnb >= 2:
            logger.info(f"{user.name} - {message.guild.name} - S'est enervé")
            await channel.send("(╯°□°）╯︵ ┻━┻")

        if "(╯°□°）╯︵ ┻━┻" in MESSAGE:
            logger.info(f"{user.name} - {message.guild.name} - A balancé la table")
            await channel.send("┬─┬ ノ( ゜-゜ノ)")

        if MESSAGE.strip(".;,?! \"')").endswith("lucas"):
            logger.info(f"{user.name} - {message.guild.name} - A dit Lucas (goubet)")
            await channel.send("goubet")

        if (MESSAGE.startswith("tu sais") or MESSAGE.startswith("vous savez")
            or MESSAGE.startswith("savez vous")
            or MESSAGE.startswith("savez-vous")
            or MESSAGE.startswith("savais-tu")
            or MESSAGE.startswith("savais tu")) and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé si on savait")
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
            logger.info(f"{user.name} - {message.guild.name} - A trouvé ca pas mal")
            reponses = ["mouais", "peut mieux faire", "woaw", ":o"]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ez" or MESSAGE == "easy") and rdnb >= 3:
            logger.info(f"{user.name} - {message.guild.name} - A trouvé ça facile")
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
            "kekette",
        ]:
            logger.info(f"{user.name} - {message.guild.name} - A parlé de bite")
            text = "8" + "=" * random.randint(0, int(
                today.strftime("%d"))) + "D"
            await channel.send(text)

        if MESSAGE == "pouet":
            await channel.send("Roooooh ta gueuuuuule putaiiiiin")

        if MESSAGE == "poueth":
            await channel.send("Poueth poueth !! 🐤")

        if (MESSAGE.startswith("stop") or MESSAGE.startswith("arrête")
                or MESSAGE.startswith("arrete")) and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé d'arrêter")
            reponses = [
                "https://tenor.com/view/daddys-home2-daddys-home2gifs-stop-it-stop-that-i-mean-it-gif-9694318",
                "https://tenor.com/view/stop-sign-when-you-catch-feelings-note-to-self-stop-now-gif-4850841",
                "https://tenor.com/view/stop-it-get-some-help-gif-7929301",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("exact") and rdnb > 2:
            logger.info(f"{user.name} - {message.guild.name} - A trouvé ça exact")
            reponses = [
                "Je dirais même plus, exact.",
                "Il est vrai",
                "AH BON ??!",
                "C'est cela",
                "Plat-il ?",
                "Jure ?",
            ]
            await channel.send(random.choice(reponses))

        if re.search(r'\bfeur\b', MESSAGE) and user.id == 302102401324679168:
            await channel.send("@everyone ARRETEZ-TOUT, IL A DIT ***FEUR*** !!!")

        if MESSAGE == "<3":
            logger.info(f"{user.name} - {message.guild.name} - A envoyé de l'amour")
            reponses = [
                "Nique ta tante (pardon)",
                "<3",
                "luv luv",
                "moi aussi je t'aime ❤",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.strip(".;,?! \"')") in ["toi-même", "toi-meme", "toi même", "toi meme"]:
            logger.info(f"{user.name} - {message.guild.name} - A sorti sa meilleure répartie")
            reponses = [
                "Je ne vous permet pas",
                "Miroir magique",
                "C'est celui qui dit qui l'est",
            ]
            await channel.send(random.choice(reponses))

        if "<@747066145550368789>" in message.content:
            logger.info(f"{user.name} - {message.guild.name} - A parlé du grand bot")
            reponses = [
                "bae",
                "Ah oui, cette sous-race de <@!747066145550368789>",
                "il a moins de bits que moi",
                "son pere est un con",
                "ca se dit grand mais tout le monde sait que....",
            ]
            await channel.send(random.choice(reponses))

        if "❤" in MESSAGE:
            logger.info(f"{user.name} - {message.guild.name} - A envoyé du love")
            await message.add_reaction("❤")

        if (MESSAGE.strip(".;,?! \"')") in ["hein", "1"]) and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A commencé par 1")
            reponses = ["deux", "2", "deux ?", "2 😏"]
            await channel.send(random.choice(reponses))

            # waits for a message validating further instructions
            def check_count(m):
                logger.info(m.content)
                return (("3" in m.content or "trois" in m.content)
                        and m.channel == message.channel
                        and not m.content.startswith("http"))

            try:
                await bot.wait_for("message", timeout=60.0, check=check_count)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
                logger.info(f"{user.name} - {message.guild.name} - A pas su compter")
            else:
                logger.info(f"{user.name} - {message.guild.name} - A su compter")
                reponses = [
                    "BRAVO TU SAIS COMPTER !",
                    "SOLEIL !",
                    "4, 5, 6, 7.... oh et puis merde",
                    "allez ta gueule.",
                    "stop.",
                ]
                await channel.send(random.choice(reponses))

        if MESSAGE == "a" and rdnb > 2:
            logger.info(f"{user.name} - {message.guild.name} - A commencer par a")

            def check_alphabet(m):
                return m.content.lower(
                ) == "b" and m.channel == message.channel

            try:
                await bot.wait_for("message", timeout=60.0, check=check_alphabet)
            except asyncio.TimeoutError:
                await message.add_reaction("☹")
                logger.info(f"{user.name} - {message.guild.name} - A pas continué par b")
            else:
                logger.info(f"{user.name} - {message.guild.name} - A connait son alphabet")
                await channel.send("A B C GNEU GNEU MARRANT TROU DU CUL !!!")

        if MESSAGE == "ah" and rdnb > 3:
            if rdnb >= 4:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait Oh/Bh")
                reponses = ["Oh", "Bh"]
                await channel.send(random.choice(reponses))
            else:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait répondre avec le dico (ah)")
                await channel.send(finndAndReplace("a", dicoLines))

        if MESSAGE == "oh" and rdnb >= 2:
            logger.info(f"{user.name} - {message.guild.name} - ")
            if rdnb >= 4:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait répondre (oh)")
                reponses = [
                    "Quoi ?",
                    "p",
                    "ah",
                    ":o",
                    "https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif",
                ]
                await channel.send(random.choice(reponses))
            else:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait répondre par le dico (oh)")
                await channel.send(finndAndReplace("o", dicoLines))

        if MESSAGE == "eh" and rdnb >= 2:
            if rdnb >= 4:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait répondre (eh)")
                reponses = ["hehehehehe", "oh", "Du calme."]
                await channel.send(random.choice(reponses))
            else:
                logger.info(f"{user.name} - {message.guild.name} - S'est fait répondre par le dico (eh)")
                await channel.send(finndAndReplace("é", dicoLines))

        if MESSAGE.startswith("merci"):
            logger.info(f"{user.name} - {message.guild.name} - A dit merci")
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
            logger.info(f"{user.name} - {message.guild.name} - A demandé qui jouait")
            await channel.send("KICÉKIJOUE ????")

        if ("😢" in MESSAGE or "😭" in MESSAGE) and rdnb >= 3:
            logger.info(f"{user.name} - {message.guild.name} - A chialé")
            reponses = [
                "cheh",
                "dur dur",
                "dommage mon p'tit pote",
                "balec",
                "tant pis",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("tu veux") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé si on voulait")
            reponses = [
                "Ouais gros",
                "Carrément ma poule",
                "Mais jamais tes fou ptdr",
                "Oui.",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("quoi") and rdnb > 2:
            logger.info(f"{user.name} - {message.guild.name} - A demandé quoi")
            reponses = ["feur", "hein ?", "nan laisse", "oublie", "rien", "😯", "coubeh", "drilatère"]

            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("pourquoi") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé pourquoi")
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
            logger.info(f"{user.name} - {message.guild.name} - A gifé Conteville")

            await channel.send(
                "https://media.discordapp.net/attachments/636579760419504148/811916705663025192/image0.gif"
            )

        if (MESSAGE.startswith("t'es sur")
            or MESSAGE.startswith("t sur")) and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé si on était sur")
            reponses = [
                "Ouais gros",
                "Nan pas du tout",
                "Qui ne tente rien...",
                "haha 👀",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE.startswith("ah ouais")
            or MESSAGE.startswith("ah bon")) and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - S'est intérrogé de la véracité du dernier propos")
            reponses = [
                "Ouais gros", "Nan ptdr", "Je sais pas écoute...", "tg"
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("au pied"):
            if message.author.id == 359743894042443776:
                logger.info(
                    f"{user.name} - {message.guild.name} - Le maitre m'a appelé")

                reponses = [
                    "wouf wouf",
                    "Maître ?",
                    "*s'agenouille*\nComment puis-je vous être utile ?",
                    "*Nous vous devons une reconnaissance éternelllllllle*",
                ]
            else:
                logger.info(f"{user.name} - {message.guild.name} - Un faux maître m'a appelé")
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

        if "<@761898936364695573>" in MESSAGE:
            logger.info(f"{user.name} - {message.guild.name} - A parlé de mon pote")
            await channel.send("Tu parles comment de mon pote là ?")

        if "tg" in MESSAGE:

            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "t"
                        and MESSAGE[i + 2] == "g" and MESSAGE[i + 3] == " "):
                    async with nbtg_lock:
                        nbtg += 1
                        with open("txt/tg.txt", "w+") as tgFile:
                            tgFile.write(str(nbtg))
                        activity = f"insulter {nbtg} personnes"
                        await bot.change_presence(activity=discord.Game(
                            name=activity))
                    await channel.send(random.choice(insultes))
                    if rdnb >= 4:
                        await message.add_reaction("🇹")
                        await message.add_reaction("🇬")
                    logger.info(f"{user.name} - {message.guild.name} - A insulté")
                    return

        if "branle" in MESSAGE:
            await channel.send(random.choice(branlette))
            return

        if MESSAGE == "cheh" or MESSAGE == "sheh":
            logger.info(f"{user.name} - {message.guild.name} - A dit cheh")
            if rdnb >= 3:
                reponses = [
                    "Oh tu t'excuses", "Cheh", "C'est pas gentil ça", "🙁"
                ]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("😉")

        if MESSAGE.startswith("non") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A dit non")
            reponses = [
                "si.",
                "ah bah ca c'est sur",
                "SÉRIEUX ??",
                "logique aussi",
                "jure ?",
            ]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("lequel") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé lequel")
            reponses = ["Le deuxième", "Le prochain", "Aucun"]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("laquelle") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demandé laquelle")
            reponses = ["La deuxième", "La prochaine", "Aucune"]
            await channel.send(random.choice(reponses))

        if MESSAGE.startswith("miroir magique") and not user.bot:
            logger.info(f"{user.name} - {message.guild.name} - A sorti une répartie de maternelle")
            await channel.send(MESSAGE)

        if MESSAGE.startswith("jure") and rdnb > 4:
            logger.info(f"{user.name} - {message.guild.name} - A demandé de jurer")
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
            logger.info(f"{user.name} - {message.guild.name} - A chialé")
            await message.add_reaction("🥰")

        if MESSAGE == "f" or MESSAGE == "rip":
            logger.info(f"{user.name} - {message.guild.name} - Payed respect")
            await channel.send(
                "#####\n#\n#\n####\n#\n#\n#       to pay respect")

        if ("quentin" in MESSAGE or "quent1" in MESSAGE) and rdnb >= 4:
            logger.info(f"{user.name} - {message.guild.name} - A parlé de mon maitre")
            await channel.send("Papa ! 🤗")

        if MESSAGE == "chaud" or MESSAGE == "cho":
            logger.info(f"{user.name} - {message.guild.name} - A dit chaud")
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
            logger.info(f"{user.name} - {message.guild.name} - Is going fast !")
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
            logger.info(f"{user.name} - {message.guild.name} - GOes fast today")
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

        if MESSAGE == "dog":
            if int(user.id) % 10 == (int(day)**3 + 33*int(month) + 12) % 10:
                await channel.send("ça se trouve t'es peut-être god aujourd'hui ?")
                return
            await channel.send(random.choice([
                "You spelled it wrong.",
                "Dumbass",
                "T'es sûr de toi ?",
                "Wouf",
                "Vasy toi aboies"
            ]))
            logger.info(f"{user.name} - {message.guild.name} - N'est pas dieu aujourd'hui")

        if MESSAGE.startswith("god"):
            MESSAGE = MESSAGE.replace("god", "")
            userID = ""

            if "<@" not in MESSAGE:
                userID = int(user.id)
                # Track requests for yourself per day
                today_str = today.strftime("%Y-%m-%d")
                if userID not in god_requests or god_requests[userID]["date"] != today_str:
                    god_requests[userID] = {"date": today_str, "count": 0}
                god_requests[userID]["count"] += 1
            else:
                i = 0
                for i in range(len(MESSAGE)):
                    if MESSAGE[i] == "<" and MESSAGE[i + 1] == "@":
                        i += 2
                        break
                while MESSAGE[i] != ">" and i < len(MESSAGE):
                    userID += MESSAGE[i]
                    i += 1
                userID = int(userID)

            if userID == 890084641317478400 and rdnb >= 3:
                await channel.send("Lâche l'affaire David")
                logger.info(f"{user.name} - {message.guild.name} - C'était David")
                return
            if userID % 5 != (int(day) + int(month)) % 5:
                # not a god? maybe a dog
                if userID % 10 == (int(day)**3 + 33*int(month) + 12) % 10:
                    dogs = [
                        'https://t3.ftcdn.net/jpg/10/70/64/34/360_F_1070643477_lKOYkVTzLjAJ9SHjHLTGJU1GUCoMiaML.jpg',
                        'https://ichef.bbci.co.uk/ace/standard/624/cpsprodpb/E386/production/_88764285_tuna1.jpg',
                        'https://www.famousbirthdays.com/headshots/tuna-1.jpg',
                        'https://s.yimg.com/os/en/aol_bored_panda_979/850b1e4dd49231d8b39075feb0ce8e9f',
                        'https://media.tenor.com/2mfG8pdR5UgAAAAM/dog-laughing-funny-dog.gif',
                        'https://i.pinimg.com/736x/27/21/55/2721550a69dc64a0b3b5bd2f792d87b2.jpg',
                        'https://pethelpful.com/.image/NDowMDAwMDAwMDAwMDYyODg1/neapolitan-mastiff-closeup.jpg',
                        'https://www.shutterstock.com/image-photo/fat-dog-sitting-panting-isolated-260nw-2588654581.jpg',
                        'https://ih1.redbubble.net/image.2958379778.2368/bg,f8f8f8-flat,750x,075,f-pad,750x1000,f8f8f8.jpg'
                    ]
                    target_user = await message.guild.fetch_member(userID)
                    pfp = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
                    embed = discord.Embed(
                        title=random.choice([
                            "It's just a dog.",
                            "Naaaah, dog",
                            "God? More like DOG",
                            "Only dog"
                        ]),
                        description=random.choice([
                            f"<@{userID}> you're just a dog.",
                            f"<@{userID}> you're no dog, only DAWG.",
                            f"<@{userID}> say \"wouf\"",
                            f"<@{userID}> you're barking and yapping, stoopid dawg"
                        ]),
                        color=0x8B4513,
                        url=random.choice([
                            "https://www.youtube.com/watch?v=dCMcSQEXAY4",
                            "https://www.youtube.com/watch?v=-AdteE-KuIg",
                            "https://www.youtube.com/shorts/rBKqNGTPNTc",
                            "https://www.youtube.com/shorts/x2BakEedBkI"
                        ]),
                    )
                    embed.set_thumbnail(url=pfp)
                    embed.set_author(
                        name="Le p'tit dog",
                        url="https://github.com/NozyZy/Le-ptit-bot",
                        icon_url="https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
                    )
                    embed.set_image(url=random.choice(dogs))
                    embed.set_footer(text="Wouf wouf")
                    logger.info(f"{user.name} - {message.guild.name} - Est un dog aujourd'hui")
                    await channel.send("Dog looks like him.", embed=embed)
                    return
                # If the user asks for himself and insists (2nd time+) => he is stupid
                # Phrases for those who insist ಥ_ಥ
                stubborn_phrases = [
                    f"<@{userID}> T'est un descendant des conifères ? Genre t'es con et tu peux rien y faire ?",
                    "Ouais bon j'ai dit \"Not today (☞ﾟヮﾟ)☞\", lâche l'affaire nan ?",
                    f"<@{userID}> T'as pas inventé l'eau chaude ...",
                    f"<@{userID}> T'as pas la lumière à tous les étages toi, hein ?",
                    f"<@{userID}> Vasy tu peux encore essayer, mais la réponse sera toujours la même :)",
                    f"<@{userID}> T'es le genre à relire les instructions du shampoing plusieurs fois.",
                    "Essaies encore une fois, juste pour voir ?",
                    "Tu sais que la définition de la folie c'est de répéter la même chose en espérant un résultat différent ?",
                    "Quelqu'un lui a dit que l'espoir fait vivre ? Bah là ça marche pas.",
                    "T'es têtu comme une mule, mais sans le charme.",
                    f"T'as les boules <@{userID}> ?",
                    "Tu vas chialer ?",
                    "Encore une fois, juste pour me divertir stp"
                ]
                if "<@" not in MESSAGE and god_requests.get(userID, {}).get("count", 0) >= (rdnb % 3) + 2:
                    await channel.send(f"{random.choice(stubborn_phrases)}")
                    logger.info(f"{user.name} - {message.guild.name} - Insiste pour être dieu (x{god_requests[userID]['count']})")
                else:
                    await channel.send("Not today (☞ﾟヮﾟ)☞")
                    logger.info(f"{user.name} - {message.guild.name} - N'est pas dieu aujourd'hui")
                return
            user = await message.guild.fetch_member(userID)
            pfp = user.avatar.url
            gods = [
                ['https://i.pinimg.com/originals/ae/68/50/ae68509b78c017ecba1f08d64c59c7f8.jpg', 'Amon'],
                ['https://upload.wikimedia.org/wikipedia/commons/b/b5/Quetzalcoatl_1.jpg', 'Quetzacoalt'],
                ['https://i.pinimg.com/originals/fa/8f/b2/fa8fb2e1f6ec3e529c119b05c2c5c649.png', 'Gaïa'],
                ['https://cdna.artstation.com/p/assets/images/images/030/081/254/large/victoria-ponomarenko-2-zin-enlil-a5.jpg', 'Enlil'],
                ['https://static.wikia.nocookie.net/dragonball/images/7/7d/BeerusWikia_%283%29.jpg/revision/latest?cb=20240224003806', 'Beerus'],
                ['https://tse2.mm.bing.net/th?id=OIP.pVKMpFtFLRjIpAEsPMafJgAAAA&pid=Api', 'Tezcatlipoca'],
                ['https://static.wikia.nocookie.net/the-demonic-paradise/images/2/2b/62000d56c16c35ada35f1da338de087e309313e9r1-736-735v2_uhq.jpg/revision/latest?cb=20200531061757', 'Arawn'],
                ['https://cdnb.artstation.com/p/assets/images/images/011/390/921/large/mohamed-sax-sobek.jpg', 'Sobek'],
                ['https://www.deviantart.com/purplerhino/art/Ishtar-Babylonian-goddess-of-love-and-war-939024002', 'Ishtar'],
                ['https://tolkiengateway.net/w/images/4/48/Elena_Kukanova_-_Vana_the_Ever-Young.jpg', 'Vána'],
                ['https://i.pinimg.com/originals/22/a3/01/22a3013477b4edde4da351b4f2c800d9.jpg', 'Hades'],
                ['https://i.pinimg.com/736x/dc/b2/b2/dcb2b25f78cce0ef7fd19b5694875327.jpg', 'Thor'],
                ['https://tse1.explicit.bing.net/th?id=OIP.KXfuA_jDa_cfDkrMInOMfQHaJq&pid=Api', 'Shiva'],
                ['https://tse3.mm.bing.net/th?id=OIP.3NR2eZEBm46mrcFM_p14RgHaJ3&pid=Api', 'Osiris'],
                ['https://i.redd.it/7q9as4hojtd61.jpg', 'Apollo'],
                ['https://cdna.artstation.com/p/assets/images/images/019/778/880/large/ekaterina-chesalova-enki.jpg', 'Enki'],
                ['https://static.wikia.nocookie.net/villains/images/7/72/Lovecraft-cthulhu.jpg/revision/latest?cb=20151128095138', 'Cthulhu'],
                ['https://tse3.mm.bing.net/th?id=OIP.M2w0Dn5HK19lF68UcicLUwHaMv&pid=Api', 'Anubis'],
                ['https://i.pinimg.com/originals/7c/71/f7/7c71f791c9e6450c00f66543c0569a8f.jpg', 'Odin'],
                ['https://www.bergaminart.com/cdn/shop/products/Old_One_1200x1200.jpg?v=1533874426', 'Azathoth'],
                ['https://tse1.mm.bing.net/th?id=OIP.M6A5OIYcaUO5UUrUjVRn5wHaNK&pid=Api', 'Arceus'],
                ['https://www.mifologia.com/wp-content/uploads/2024/10/041a1.png', 'Ninkasi'],
                ['https://cdna.artstation.com/p/assets/images/images/006/489/730/large/boyan-petrov-thoth12.jpg','Thoth'],
                ['https://upload.wikimedia.org/wikipedia/commons/d/d1/Amaterasu_cave_crop.jpg', 'Amaterasu'],
                ['https://cdnb.artstation.com/p/assets/images/images/012/343/689/large/yiye-gong-img-20180806-173554.jpg', 'Dio'],
                ['https://i.pinimg.com/originals/e1/4a/2b/e14a2b86ccd88ba31ad3ac3945737d26.jpg', 'God zilla'],
                ['https://cdn3.f-cdn.com//files/download/124058119/erlikk2.jpg?width=780&height=1011&fit=crop', 'Erlik Khan'],
                ['https://legendaryladieshub.com/wp-content/uploads/2023/10/Venus_LLH.jpeg', 'Venus'],
                ['https://tse2.mm.bing.net/th?id=OIP.BYG-Xfgo4To4PJaY32Gj0gHaKD&pid=Api', 'Poseidon'],
                ['https://i.pinimg.com/736x/cd/79/9d/cd799dc51f48b1a88dddf5a8017d288f.jpg', 'Mara'],
                ['https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/8809c8cd-04d2-4fc2-bc24-f9e2460d0f36/d8vo0pe-00f82d4e-4560-462d-9d19-594b1455f009.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcLzg4MDljOGNkLTA0ZDItNGZjMi1iYzI0LWY5ZTI0NjBkMGYzNlwvZDh2bzBwZS0wMGY4MmQ0ZS00NTYwLTQ2MmQtOWQxOS01OTRiMTQ1NWYwMDkuanBnIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.w8B7yWVQ2_wrZKZvJ_p9JzrXymLB3XWWmEdOx-JXmP4','Anu']
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
            god = gods[((userID // 365 + int(day) ** 3 * int(year)) // int(month)) % len(gods)]
            embed.set_thumbnail(url=pfp)
            embed.set_author(
                name="Le p'tit god",
                url="https://github.com/NozyZy/Le-ptit-bot",
                icon_url=
                "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
            )
            embed.set_image(url=god[0])
            embed.set_footer(text=god[1])
            logger.info(f"{user.name} - {message.guild.name} - Est un dieu aujourd'hui : {god[1]}")
            await channel.send("God looks like him.", embed=embed)

        if MESSAGE.startswith("hello") and rdnb >= 3:
            logger.info(f"{user.name} - {message.guild.name} - A dit hello")
            await channel.send(file=discord.File("images/helo.jpg"))

        if (MESSAGE == "enculé" or MESSAGE == "enculer") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - A demander d'aller se faire enculer")
            image = ["images/tellermeme.png", "images/bigard.jpeg"]
            await channel.send(file=discord.File(random.choice(image)))

        if MESSAGE == "kachow":
            responses = [
                "https://c.tenor.com/FfimHvu74ccAAAAC/kachow-backdriving-blink-mcqueen-cars-last-race.gif",
                "https://i.pinimg.com/originals/3a/8b/03/3a8b036011946ab59ea2a8c353372d2b.gif",
            ]
            await channel.send(random.choice(responses))

        if MESSAGE == "stonks":
            logger.info(f"{user.name} - {message.guild.name} - Stonked")
            await channel.send(file=discord.File("images/stonks.png"))

        if (MESSAGE == "parfait" or MESSAGE == "perfection") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - Perfection")
            await channel.send(file=discord.File("images/perfection.jpg"))

        if MESSAGE.startswith("leeroy"):
            logger.info(f"{user.name} - {message.guild.name} - LEEROOOOOOOOOOYY")
            await channel.send(file=discord.File("sounds/Leeroy Jenkins.mp3"))

        if "guillotine" in MESSAGE:
            logger.info(f"{user.name} - {message.guild.name} - Le guillotine")
            reponses = [
                "https://tenor.com/view/guillatene-behead-lego-gif-12352396",
                "https://tenor.com/view/guillotine-gulp-worried-scared-slug-riot-gif-11539046",
                "https://tenor.com/view/revolution-guillotine-marie-antoinette-off-with-their-heads-behead-gif-12604431",
            ]
            await channel.send(random.choice(reponses))

        if (MESSAGE == "ouh" or MESSAGE == "oh.") and rdnb > 3:
            logger.info(f"{user.name} - {message.guild.name} - 'OUH.', by Velikson")
            await channel.send(
                "https://thumbs.gfycat.com/AptGrouchyAmericanquarterhorse-size_restricted.gif"
            )

        if "pd" in MESSAGE:
            MESSAGE = " " + MESSAGE + " "
            for i in range(len(MESSAGE) - 3):
                if (MESSAGE[i] == " " and MESSAGE[i + 1] == "p"
                        and MESSAGE[i + 2] == "d" and MESSAGE[i + 3] == " "):
                    logger.info(f"{user.name} - {message.guild.name} - A parlé de pd")
                    await channel.send(file=discord.File("images/pd.jpg"))

        if "oof" in MESSAGE and rdnb >= 5:
            logger.info(f"{user.name} - {message.guild.name} - oof")
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
            logger.info(f"{user.name} - {message.guild.name} - Money bitch")
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
        # Charger les brainrots depuis le fichier JSON
        logger.info(f"{user.name} - {message.guild.name} - A invoqué un brainrot italian")
        brainrots_file = os.path.join(os.path.dirname(__file__), 'images', 'italian.json')
        try:
            with open(brainrots_file, 'r', encoding='utf-8') as f:
                brainrots = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            brainrots = []

        if brainrots:
            choice = random.choice(brainrots)
            embed = discord.Embed(title=choice.get("name"), color=0xF4D03F)
            embed.set_image(url=choice.get("img"))
            await channel.send(embed=embed)

    # OneCOPS release date feature
    if "onecops" in MESSAGE and MESSAGE.strip().endswith("?"):
        logger.info(f"{user.name} - {message.guild.name} - A demandé quand sortira OneCOPS")

        # Increment and save the counter
        onecops_count = load_onecops_counter() + 1
        save_onecops_counter(onecops_count)

        # Calculate release date
        today = date.today()
        current_month = today.month
        current_year = today.year

        # Add counter months to current month
        total_months = current_month + onecops_count
        release_year = current_year + (total_months - 1) // 12
        release_month = ((total_months - 1) % 12) + 1

        # Format response
        month_name = FRENCH_MONTHS[release_month - 1]
        await channel.send(f"Oulà, OneCOPS sortira pas avant fin {month_name} {release_year}")
        logger.info(f"OneCOPS counter: {onecops_count} -> fin {month_name} {release_year}")

    # teh help command, add commands call, but not reactions
    if MESSAGE == "--help":
        logger.info(f"{user.name} - {message.guild.name} - A demandé de l'aide")
        await channel.send(
            "Commandes : \n"
            " **F** to pay respect\n"
            " **--addBranlette** pour ajouter une expression de branlette et **branle** pour en avoir une\n"
            " **--addInsult** pour ajouter des insultes et **tg** pour te faire insulter\n"
            " **--amongus** pour lancer une partie Among Us\n"
            " **--appel** puis le pseudo de ton pote pour l'appeler (admin only)\n"
            " **--calcul** *nb1* (+, -, /, *, ^, !) *nb2* pour avoir un calcul adéquat \n"
            " **--clear** *nb* pour supprimer *nb* messages\n"
            " **--crypt** pour chiffrer/déchiffrer un message César (décalage)\n"
            " **--dhcp** *range* pour une activité d'attribution d'IPs\n"
            " **--dico** pour connaître le nombre de mots dans mon dictionnaire\n"
            " **--game** pour jouer au jeu du **clap**\n"
            " **--invite** pour savoir comment m'inviter\n"
            " **--isPrime** *nb* pour tester si *nb* est premier\n"
            " **--join** et **--leave** pour me faire rejoindre/quitter un vocal\n"
            " **--p4** pour jouer au Puissance 4\n"
            " **--poll** ***question***, *prop1*, *prop2*,..., *prop10* pour avoir un sondage de max 10 propositions\n"
            " **--presentation** et **--master** pour créer des memes\n"
            " **--prime** *nb* pour avoir la liste de tous les nombres premiers jusqu'a *nb* au minimum\n"
            " **--randint** *nb1*, *nb2* pour avoir un nombre aléatoire entre ***nb1*** et ***nb2***\n"
            " **--random** pour écrire 5 mots aléatoires\n"
            " **--rename** *nouveau_nom* pour changer mon nom sur ce serveur (admin only)\n"
            " **--repeat** pour que je répète ce qui vient après l'espace\n"
            " **--resetname** pour remettre mon nom par défaut (admin only)\n"
            " **--serverInfo** pour connaître les infos du server\n"
            "Et je risque de réagir à tes messages, parfois de manière... **Inattendue** 😈"
        )
            
    else:
        # allows command to process after the on_message() function call
        await bot.process_commands(message)


# beginning of the commands


@bot.command()  # delete 'nombre' messages
@commands.cooldown(1, 10, commands.BucketType.user)  # 1 use per 10 seconds per user
async def clear(ctx, nombre: int):
    if nombre <= 0:
        await ctx.send("❌ Le nombre de messages doit être positif.")
        return
    if nombre > 1000:
        await ctx.send("❌ Je ne peux pas supprimer plus de 1000 messages à la fois.")
        return
    logger.info(
        f"{ctx.author.name} - A demandé de clear {nombre} messages dans le channel {ctx.channel.name} du serveur {ctx.guild.name}")
    messages = [message async for message in ctx.channel.history(limit=nombre + 1, oldest_first=False)]
    for message in messages:
        await message.delete()


@bot.command()  # repeat the 'text', and delete the original message
async def repeat(ctx, *text):
    logger.info(f"{ctx.author.name} - A demandé de répéter {' '.join(text)} messages")
    messages = ctx.channel.history(limit=1)
    for message in messages:
        await message.delete()
    await ctx.send(" ".join(text))


@bot.command()  # show the number of people in the server, and its name
async def serverinfo(ctx):
    server = ctx.guild
    nbUsers = server.member_count
    text = f"Le serveur **{server.name}** contient **{nbUsers}** personnes !"
    logger.info(f"{ctx.author.name} - A demandé les infos du serveur {server.name}")
    await ctx.send(text)


@bot.command()  # send the 26 possibilites of a ceasar un/decryption
async def crypt(ctx, *text):
    mot = " ".join(text)
    messages = [message async for message in ctx.channel.history(limit=1)]
    for message in messages:
        await message.delete()
    logger.info(f"{ctx.author.name} - A demandé de crypter {mot} en {crypting(mot)}")
    await ctx.send(f"||{mot}|| :\n" + crypting(mot))


@bot.command()  # send a random integer between two numbers, or 1 and 0
async def randint(ctx, *text):
    logger.info(f"{ctx.author.name} - ")
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
        logger.info("A demandé un nombre aléatoire sans donner d'encadrement")
        return

    nb1 = strToInt(tab)

    if i != len(MESSAGE):
        nb2 = strToInt(list=nbInStr(MESSAGE, i, len(MESSAGE)))

    if nb1 == nb2:
        text = f"Bah {str(nb1)} du coup... 🙄"
        await ctx.send(text)
        logger.info(f"A demandé le nombre {nb1}")
        return
    if nb2 < nb1:
        temp = nb2
        nb2 = nb1
        nb1 = temp

    rd = random.randint(nb1, nb2)
    logger.info(f"A généré un nombre aléatoire [|{nb1}:{nb2}|] = {rd}")
    await ctx.send(rd)


@bot.command()  # send a random word from the dico, the first to write it wins
async def game(ctx):
    logger.info(f"{ctx.author.name} - ")
    with open("txt/dico.txt", "r+") as dicoFile:
        dicoLines = dicoFile.readlines()

    mot = random.choice(dicoLines)
    mot = mot.replace("\n", "")
    text = f"Le premier à écrire **{mot}** a gagné"
    logger.info(f"A joué au jeu en devinant {mot}, ")
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
        user = getattr(msg.author, 'nick', None) or msg.author.name
        text = f"**{user}** a gagné !"
        logger.info(f"{user} a gagné")
        await ctx.send(text)


@bot.command()  # do a simple calcul of 2 numbers and 1 operator (or a fractionnal)
@commands.cooldown(3, 5, commands.BucketType.user)  # 3 uses per 5 seconds
async def calcul(ctx, *text):
    logger.info(f"{ctx.author.name} - ")
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
        logger.info("A demandé de calculer l'infini")
        return

    while i < len(Message) and 48 <= ord(Message[i]) <= 57:
        if 48 <= ord(Message[i]) <= 57:
            tab.append(Message[i])
        i += 1

    if len(tab) == 0:
        await ctx.send("Rentre un nombre banane")
        logger.info("A demandé de calculer sans rentrer de nombre")
        return

    if i == len(Message) or Message[i] not in symbols:
        await ctx.send("Rentre un symbole (+, -, *, /, ^, !)")
        logger.info("A demandé de calculer sans rentrer de symbole")
        return

    symb = Message[i]

    nb1 = strToInt(tab)

    if symb == "!":
        if nb1 > 806:  # can't go above 806 recursion deepth
            await ctx.send("806! maximum, désolé 🤷‍♂️")
            logger.info("A demandé de calculer plus de 806! (erreur récursive)")
            return
        rd = facto(nb1)
        text = str(nb1) + "! =" + str(rd)
        await ctx.send(text)
        logger.info(f"A demandé de calculer {text}")
        return

    if i != len(Message):
        tab = nbInStr(Message, i, len(Message))

        if len(tab) == 0:
            await ctx.send("Rentre un deuxième nombre patate")
            logger.info("A demandé de calculer sans reentrer de deuxième nombre")
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
            logger.info("A demandé de calculer une division par 0 (le con)")
            return
        rd = float(nb1 / nb2)
    elif symb == "^":
        rd = nb1 ** nb2
    text = str(nb1) + str(symb) + str(nb2) + "=" + str(rd)
    logger.info(text)
    logger.info(f"A demandé de calculer {text}")
    await ctx.send(text)


@bot.command(
)  # create a reaction poll with a question, and max 10 propositions
async def poll(ctx, *text):
    logger.info(f"{ctx.author.name} - ")
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
        logger.info("A demandé un poll sans choix")
        return
    if len(tab) > 11:
        await ctx.send("Ca commence à faire beaucoup non ?... 10 max ca suffit"
                       )
        logger.info("A demandé un poll e plus de 10 choix")
        return
    text = ""
    logger.info("A demandé un poll avec : ")
    for i in range(len(tab)):
        logger.info(tab[i])
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
@commands.cooldown(1, 30, commands.BucketType.user)  # 1 use per 30 seconds (intensive calculation)
async def prime(ctx, nb: int):
    global nbprime
    logger.info(f"{ctx.author.name} - ")
    if nb < 2:
        await ctx.send("Tu sais ce que ca veut dire 'prime number' ?")
        logger.info("A demandé de calculer un nombre premier en dessous de 2")
        return
    async with nbprime_lock:
        if nbprime > 2:
            await ctx.send("Attends quelques instants stp, je suis occupé...")
            logger.info(f"A demandé trop de prime -> {nbprime}")
            return
        nbprime += 1
    with open("txt/primes.txt", "r+") as Fprime:
        primes = Fprime.readlines()
    biggest = int(primes[len(primes) - 1].replace("\n", ""))
    text = ""
    ratio_max = 1.02
    n_max = int(biggest * ratio_max)
    logger.info(nb, biggest, n_max)

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
    async with nbprime_lock:
        nbprime -= 1
    logger.info(f"A demandé de calculer tous les nombres premiers juqu'à {nb}")


@bot.tree.command(name="isprime", description="Es-tu prime ?")
async def isPrime_slash(interaction: discord.Interaction, nb: int):
    if nb > 99999997979797979797979777797:
        await interaction.response.send_message(
            "C'est trop gros, ca va tout casser, demande à papa Google :D", ephemeral=True)
        logger.info("too big")
    elif await is_prime(nb):
        await interaction.response.send_message(f"👍")
        logger.info("oui")
    else:
        await interaction.response.send_message(f"👎")
        logger.info("non")


@bot.command()  # find if 'nb' is a prime number, reacts to the message
@commands.cooldown(2, 5, commands.BucketType.user)  # 2 uses per 5 seconds
async def isPrime(ctx, nb: int):
    logger.info(
        f"{ctx.author.name} - A demandé si {nb} est premier : ",
    )
    if nb > 99999997979797979797979777797:
        await ctx.send(
            "C'est trop gros, ca va tout casser, demande à papa Google :D")
        logger.info("too big")
    elif await is_prime(nb):
        await ctx.message.add_reaction("👍")
        logger.info("oui")
    else:
        await ctx.message.add_reaction("👎")
        logger.info("non")


@bot.command()  # send 'nb' random words of the dico, can repeat itself
async def randomWord(ctx, nb: int):
    logger.info(
        f"{ctx.author.name} - A demandé {nb} mots aléatoires dans le dico : ",
    )
    with open("txt/dico.txt", "r+") as dicoFile:
        dicoLines = dicoFile.readlines()

    text = ""
    for i in range(nb):
        text += random.choice(dicoLines)
        if i != nb - 1:
            text += " "
    text += "."
    text = text.replace("\n", "")
    if text:
        text = text[0].upper() + text[1:]
    logger.info(text)
    await ctx.send(text)


@bot.command()  # join the vocal channel fo the caller
async def join(ctx):
    channel = ctx.author.voice.channel
    logger.info(
        f"{ctx.author.name} - A demandé que je rejoigne le vocal {channel} du serveur {ctx.guild.name}"
    )
    await channel.connect()


@bot.command()  # leaves it
async def leave(ctx):
    logger.info(
        f"{ctx.author.name} - A demandé que je quitte le vocal {ctx.author.voice.channel} du serveur {ctx.guild.name}"
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


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)  # 1 use per 10 seconds (image generation)
async def master(ctx, *text):
    logger.info(
        f"{ctx.author.name} - A demandé un meme master ")
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
        bbox = fonts[i].getbbox(text[i])
        sizes.append(bbox[2] - bbox[0])  # width = right - left

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
    logger.info(f"avec le texte : {text}")
    img.save("images/mastermeme.jpg")
    await ctx.send(file=discord.File("images/mastermeme.jpg"))


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)  # 1 use per 10 seconds (image generation)
async def presentation(ctx, *base):
    logger.info(
        f"{ctx.author.name} - A demandé un meme presentation ",
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
        bbox = font.getbbox(text[i])
        width = bbox[2] - bbox[0]  # right - left
        height = bbox[3] - bbox[1]  # bottom - top
        draw.text(
            xy=(335 - width / 2, 170 + i * height - 10 * count),
            text=text[i],
            fill=(0, 0, 0),
            font=font,
        )

    img.save("images/presentationmeme.png")
    logger.info(f"avec le texte : {text}")
    await ctx.send(file=discord.File("images/presentationmeme.png"))


@bot.tree.command(name="ban", description="Tu veux vraiment bannir mes réactions ??? Enflure...")
async def ban(ctx: discord.Interaction):
    if not ctx.channel or not ctx.guild:
        await ctx.response.send_message("Cette commande ne fonctionne que dans un serveur.")
        return
    channel_name = getattr(ctx.channel, 'name', 'DM')
    logger.info(
        f"{ctx.user.name} - A demandé de me bannir du channel {channel_name} du serveur {ctx.guild.name} : ",
    )
    member = ctx.guild.get_member(ctx.user.id)
    if not member or not member.guild_permissions.administrator:
        await ctx.response.send_message("T'es pas admin, nananananère 😜")
        logger.info("mais n'a pas les droits")
        return
    with open("txt/bans.txt", "r+") as bansFile:
        bansLines = bansFile.readlines()
    chanID = str(ctx.channel.id) + "\n"
    if chanID in bansLines:
        await ctx.response.send_message("Jsuis déjà ban, du calme...")
        logger.info("mais j'étais déjà ban (sad)")
    else:
        with open("txt/bans.txt", "a+") as bansFile:
            bansFile.write(chanID)
        await ctx.response.send_message(
            "D'accord, j'arrete de vous embêter ici... mais les commandes sont toujours dispos"
        )
        logger.info("et je suis ban")


@bot.tree.command(name="unban", description="OUI LIBERE-MOI")
async def unban(ctx: discord.Interaction):
    if not ctx.channel or not ctx.guild:
        await ctx.response.send_message("Cette commande ne fonctionne que dans un serveur.")
        return
    channel_name = getattr(ctx.channel, 'name', 'DM')
    logger.info(
        f"{ctx.user.name} - A demandé de me débannir du channel {channel_name} du serveur {ctx.guild.name} : ",
    )
    member = ctx.guild.get_member(ctx.user.id)
    if not member or not member.guild_permissions.administrator:
        await ctx.response.send_message("T'es pas admin, nananananère 😜")
        logger.info("mais n'a pas les droits")
        return
    with open("txt/bans.txt", "r+") as bansFile:
        bansLines = bansFile.readlines()
    chanID = str(ctx.channel.id) + "\n"
    if chanID not in bansLines:
        await ctx.response.send_message("D'accord, mais j'suis pas ban, hehe.")
        logger.info("mais j'étais pas ban")
    else:
        with open("txt/bans.txt", "w+") as bansFile:
            bansFile.write("")
        with open("txt/bans.txt", "a+") as bansFile:
            for id in bansLines:
                if id == chanID:
                    bansLines.remove(id)
                    await ctx.response.send_message("JE SUIS LIIIIIIBRE")
                    logger.info("et je suis libre (oui!)")
                else:
                    bansFile.write(id)


@bot.tree.command(name="invite", description="Vasy invite moi sur un autre serveur, on s'emmerde ici")
async def invite(ctx: discord.Interaction):
    guild_name = ctx.guild.name if ctx.guild else "DM"
    logger.info(
        f"{ctx.user.name} - A demandé une invitation dans le serveur {guild_name}"
    )
    await ctx.response.send_message(
        "Invitez-moi 🥵 !\n"
        "https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8"
    )


@bot.command()
@commands.cooldown(1, 60, commands.BucketType.channel)  # 1 use per 60 seconds per channel (to avoid spam)
async def amongus(ctx):
    logger.info(
        f"{ctx.author.name} - A demandé une game Among Us {ctx.guild.name}"
    )

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
            await asyncio.sleep(1)
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
        bot_id = bot.user.id if bot.user else None
        for user in users:
            if user.id != bot_id:
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
    logger.info(
        f"{ctx.author.name} - La game Among Us a prit fin {ctx.guild.name}"
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
    if not (draw > 0) and not (win >= 3):
        await interaction.response.send_message("Va falloir gagner au Puissance 4 si tu veux un flag : `--p4`",
                                                ephemeral=True)
    else:
        await interaction.response.send_message(
            f"Wtf, envoi un MP aux admins en montrant ce message stp : {draw}, {win}, {interaction.user.id}",
            ephemeral=True)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.channel)  # 1 game per 30 seconds per channel
async def puissance4(interaction):
    logger.info(
        f"{interaction.author.name} - A lancé une partie de puissance 4 {interaction.guild.name}"
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
                if all(grid[r][c + i] == player for i in range(4)):
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(grid[r + i][c] == player for i in range(4)):
                    return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(grid[r + i][c + i] == player for i in range(4)):
                    return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(grid[r - i][c + i] == player for i in range(4)):
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
                score += evaluate_window([grid[r][c + i] for i in range(4)], player)
        # Colonnes verticales
        for r in range(ROWS - 3):
            for c in range(COLS):
                score += evaluate_window([grid[r + i][c] for i in range(4)], player)
        # Diagonales
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += evaluate_window([grid[r + i][c + i] for i in range(4)], player)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += evaluate_window([grid[r - i][c + i] for i in range(4)], player)
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
        await asyncio.sleep(4)
        if type == "win":
            await user.send("Coucou")
            await asyncio.sleep(4)
            await user.send("Ok bien joué")
            await asyncio.sleep(7)
            await user.send("T'es sûr de mériter le flag ?")
            await asyncio.sleep(9)
            await user.send("Bon vasy le flag tu me fais pitié : `CYBN{Y0u_Kn0w_hOW_7o_Pl4Y_P0w3R_4}`")
        elif type == "draw":
            await user.send("Stylé l'égalité, je pensais pas que ca arriverait :clap:")
            await asyncio.sleep(4)
            await user.send("Tu es de ma trempe pour réussir ça, j'aime bien, bel adversaire")
            await asyncio.sleep(3)
            await user.send(
                "Allez tiens un petit cadeau, il rapporte pas beaucoup de points mais c'est toujours sympa : `CYBN{DR4wiNG_w1Th0Ut_P4p3r_c4N_H4pP3n}`")

    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    """grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 1, 0, 0],
            [0, 0, 0, 2, 2, 1, 0],
            [0, 0, 0, 2, 2, 2, 1]]"""

    async def updateGrid(grid, text, message):
        text += "\n" + "".join(numbers) + "\n"
        logger.info("\n")
        for row in grid:
            logger.info(row)
            for case in row:
                if case == 0:
                    text += "🔵"
                elif case == 1:
                    text += "🔴"
                elif case == 2:
                    text += "🟡"
                else:
                    logger.info(f"ERROR - {case} - {row}")
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
    logger.info(
        f"{yellow} - Est le joueur jaune {interaction.guild.name}"
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
        logger.info(f"{red} - Est le joueur red {interaction.guild.name}")
    elif mode == "pve":
        if not bot.user:
            await interaction.send("Erreur: le bot n'est pas prêt.")
            return
        red = bot.user
        redMessage = await interaction.send("Je serai l'adversaire rouge, tiens-toi prêt 😈")

    yellowPing = "<@!" + str(yellow.id) + "> 🟡"  # type: ignore[union-attr]
    redPing = "<@!" + str(red.id) + "> 🔴"  # type: ignore[union-attr]

    text = yellowPing + " et " + redPing + " tenez vous prêts !"
    gridMessage = await interaction.send(text)

    await asyncio.sleep(5)

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
                        logger.info(f"ERROR - {case} - {row}")
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

        else:
            def check(reaction, user):
                return (user == yellow and str(reaction.emoji) in numbers
                        and reaction.message.id == gridMessage.id)

        try:
            if not (tour % 2 == 0 and mode == "pve"):
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
                    loser = yellow
                    winner = red
                    ping = redPing
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
                        logger.info(
                            f"{loser} - A perdu contre le bot au P4 (noob)"
                        )
                        await changeScoreLeaderboard(loser.id, loser, win=False, filename="pve.txt")  # type: ignore[union-attr]
                        text = f"{ping} gagne ! (c'est moi)\n{random.choice(messages)}"
                else:
                    loser = red
                    winner = yellow
                    ping = yellowPing
                    if mode == "pve":
                        logger.info(
                            f"{winner} - A gagné contre le bot au P4 (gg)"
                        )
                        await changeScoreLeaderboard(winner.id, winner, win=True, filename="pve.txt")  # type: ignore[union-attr]
                        score = int((await getScoreLeaderBoard(winner.id, filename="pve.txt"))[0])  # type: ignore[union-attr]
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
                            text = f"{ping} remporte la victoire ! **Score actuel : {score} / 3** - Plus que {3 - score} avant le flag"
                            # play again
                logger.info(
                    f"{winner} - Est le gagnant vs {loser} ! {interaction.guild.name}"
                )
                if mode == "pvp":
                    await addScoreLeaderboard(winner.id, winner)  # type: ignore[union-attr]
                    await addLoseLeaderboard(loser.id, loser)  # type: ignore[union-attr]
                await gridMessage.add_reaction("✅")
                await updateGrid(
                    grid,
                    "Tour n°" + str(tour) + " - " + ping + "\n",
                    gridMessage,
                )
                if mode == "pvp":
                    score = (await getScoreLeaderBoard(winner.id))[0]  # type: ignore[union-attr]
                    place = await getPlaceLeaderbord(winner.id)  # type: ignore[union-attr]
                    text = f"{ping} gagne ! **Score actuel : {score} victoires** - {place}"
                if not sent:
                    await interaction.send(text)
                end = True

            elif tour >= 42:
                await gridMessage.add_reaction("✅")
                logger.info(
                    f"{red} et {yellow} - Sont à égalité ! {interaction.guild.name}"
                )
                if mode == "pvp":
                    await addScoreLeaderboard(yellow.id, yellow)  # type: ignore[union-attr]
                    await addScoreLeaderboard(red.id, red)  # type: ignore[union-attr]
                    text = (
                            "Bravo à vous deux, c'est une égalité ! Bien que rare, ça arrive... Donc une victoire en plus chacun ! gg\n"
                            "**Score de " + yellowPing + " : " +
                            (await getScoreLeaderBoard(yellow.id))[0] +  # type: ignore[union-attr]
                            " victoires !**\n **Score de " + redPing + " : " +
                            (await getScoreLeaderBoard(red.id))[0] + " victoires !**")  # type: ignore[union-attr]
                    await interaction.send(text)
                elif mode == "pve":
                    text = "Ah bah une égalité tiens, c'est rare... Viens on en discute en MP? Sinon fais `/flag`"
                    await changeScoreLeaderboard(yellow.id, yellow, win=False, filename="pve.txt", draw=True)  # type: ignore[union-attr]
                    await interaction.send(text)
                    await send_mp(yellow, type="draw")

                end = True

        except asyncio.TimeoutError:
            await gridMessage.add_reaction("❌")
            await gridMessage.add_reaction("⌛")
            if tour % 2 == 0:
                logger.info(
                    f"{yellow} - Est le gagnant ! {interaction.guild.name}"
                )
                await updateGrid(
                    grid, "Tour n°" + str(tour) + " - " + redPing + "\n",
                    gridMessage)
                await addScoreLeaderboard(yellow.id, yellow)  # type: ignore[union-attr]
                await addLoseLeaderboard(red.id, red)  # type: ignore[union-attr]
                # await score/place into variables and ensure place is a string fallback
                score = (await getScoreLeaderBoard(yellow.id))[0]  # type: ignore[union-attr]
                place = await getPlaceLeaderbord(yellow.id)  # type: ignore[union-attr]
                if place is None:
                    place = "Non classé"
                text = (
                    redPing + " n'a pas joué ! Alors **" + yellowPing +
                    " gagne !** (c'est le jeu ma pov lucette)\n Score actuel : "
                    + score + " victoires - " + place
                )
            else:
                logger.info(
                    f"{red} - Est le gagnant ! {interaction.guild.name}"
                )
                await updateGrid(
                    grid, "Tour n°" + str(tour) + " - " + redPing + "\n",
                    gridMessage)

                if mode == "pvp":
                    await addScoreLeaderboard(red.id, red)  # type: ignore[union-attr]
                    await addLoseLeaderboard(yellow.id, yellow)  # type: ignore[union-attr]
                    score = (await getScoreLeaderBoard(red.id))[0]  # type: ignore[union-attr]
                    place = await getPlaceLeaderbord(red.id)  # type: ignore[union-attr]
                    if place is None:
                        place = "Non classé"
                    text = (
                        yellowPing + " n'a pas joué ! Alors **" + redPing +
                        " gagne !** (fallait jouer, 2 min t'es large !)\n Score actuel : "
                        + score + " victoires - " + place
                    )
                elif mode == "pve":
                    await changeScoreLeaderboard(yellow.id, yellow, win=False, filename="pve.txt")  # type: ignore[union-attr]
                    text = f"J'en connais un qui est parti flag d'autres challs, et a abandonné le miens... Bah t'as perdu {yellowPing}, cheh"
            await interaction.send(text)
            end = True

        tour += 1


@bot.command()
async def p4(ctx):
    await puissance4(ctx)


async def updateLeaderboard(liste, filename="leaderboard.txt"):
    with open("txt/" + filename, "w+") as file:
        for line in liste:
            line = "-".join(line)
            if line[len(line) - 1] != "\n":
                line += "\n"
            file.write(line)


async def getScoreLeaderBoard(id, filename="leaderboard.txt"):
    with open("txt/" + filename, "r+") as file:
        leaderboard_users = file.readlines()
    for i in range(len(leaderboard_users)):
        if str(id) in leaderboard_users[i]:
            parts = leaderboard_users[i].split("-")
            return parts[1].replace("\n", ""), parts[2].replace("\n", "")
    return "0", "0"


async def getPlaceLeaderbord(id):
    with open("txt/leaderboard.txt", "r+") as file:
        leaderboard_users = file.readlines()

    for i in range(len(leaderboard_users)):
        if str(id) in leaderboard_users[i]:
            i += 1
            if i == 1:
                return "1er/" + str(len(leaderboard_users))
            else:
                return str(i) + "e/" + str(len(leaderboard_users))
    return None


async def changeScoreLeaderboard(id, name, win=False, filename="leaderboard.txt", draw=False):
    with open("txt/" + filename, "r+") as file:
        leaderboard_users = [line.split("-") for line in file.readlines()]
    isIn = False
    for i in range(len(leaderboard_users)):
        if str(id) in leaderboard_users[i]:
            isIn = True
            leaderboard_users[i][1] = "0" if not win else str(int(leaderboard_users[i][1]) + 1)
            leaderboard_users[i][2] = leaderboard_users[i][2] if not draw else "1"
            if int(leaderboard_users[i][2]) == 0:
                leaderboard_users[i][3] = leaderboard_users[i][1]
            else:
                leaderboard_users[i][3] = str(
                    round(
                        float(leaderboard_users[i][1]) / float(leaderboard_users[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-1-0-1-" + str(name) + "\n").split("-")
        leaderboard_users.append(line)

    leaderboard_users.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard_users, filename=filename)


async def addScoreLeaderboard(id, name):
    with open("txt/leaderboard.txt", "r+") as file:
        leaderboard_users = [line.split("-") for line in file.readlines()]
    isIn = False
    for i in range(len(leaderboard_users)):
        if str(id) in leaderboard_users[i]:
            isIn = True
            leaderboard_users[i][1] = str(int(leaderboard_users[i][1]) + 1)
            if int(leaderboard_users[i][2]) == 0:
                leaderboard_users[i][3] = leaderboard_users[i][1]
            else:
                leaderboard_users[i][3] = str(
                    round(
                        float(leaderboard_users[i][1]) / float(leaderboard_users[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-1-0-1-" + str(name) + "\n").split("-")
        leaderboard_users.append(line)

    leaderboard_users.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard_users)


async def addLoseLeaderboard(id, name):
    with open("txt/leaderboard.txt", "r+") as file:
        leaderboard_users = [line.split("-") for line in file.readlines()]
    isIn = False
    for i in range(len(leaderboard_users)):
        if str(id) in leaderboard_users[i]:
            isIn = True
            leaderboard_users[i][2] = str(int(leaderboard_users[i][2]) + 1)
            if int(leaderboard_users[i][2]) == 0:
                leaderboard_users[i][3] = leaderboard_users[i][1]
            else:
                leaderboard_users[i][3] = str(
                    round(
                        float(leaderboard_users[i][1]) / float(leaderboard_users[i][2]),
                        2))
    if not isIn:
        line = (str(id) + "-0-1-0-" + str(name) + "\n").split("-")
        leaderboard_users.append(line)

    leaderboard_users.sort(reverse=True, key=lambda score: int(score[1]))
    await updateLeaderboard(leaderboard_users)


@bot.tree.command(name="leaderboard", description="Affiche le classement au Puissance 4")
async def leaderboard(ctx: discord.Interaction):
    with open("txt/leaderboard.txt", "r+") as file:
        leaderboard_users = [line.split("-") for line in file.readlines()]

    numbers = [
        "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
    ]
    text = "Le classement du puissance 4 est composé de : \n\n"
    leaderSize = 5
    if len(leaderboard_users) <= leaderSize:
        if len(leaderboard_users) <= 0:
            text = "Bah ya personne... ***jouez !***"
        else:
            text += "Avec le plus de victoires : \n"
            for i in range(len(leaderboard_users)):
                name = leaderboard_users[i]
                text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                         "** avec **" + name[1] + " victoires**\n")

            leaderboard_users.sort(reverse=True, key=lambda score: float(score[3]))
            text += "\nAvec le plus grand ratio Victoire/Défaite\n"
            for i in range(len(leaderboard_users)):
                name = leaderboard_users[i]
                text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                         "** avec **" + name[3] + " V/D** (" + str(
                            round(
                                int(name[1]) /
                                (int(name[1]) + int(name[2])) * 100, 2)) +
                         "%)\n")
    else:
        text += "Avec le plus de victoires : \n"
        for i in range(leaderSize):
            name = leaderboard_users[i]
            text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                     "** avec **" + name[1] + " victoires**\n")
        text += "*+" + str(len(leaderboard_users) -
                           leaderSize) + " autres joueurs*\n\n"

        leaderboard_users.sort(reverse=True, key=lambda score: float(score[3]))
        text += "Avec le plus grand ratio Victoire/Défaite\n"
        for i in range(leaderSize):
            name = leaderboard_users[i]
            text += (numbers[i] + " : **" + name[4].replace("\n", "") +
                     "** avec **" + name[3] + " V/D** (" + str(
                        round(
                            int(name[1]) /
                            (int(name[1]) + int(name[2])) * 100, 2)) + "%)\n")
        text += "*+" + str(len(leaderboard_users) - leaderSize) + " autres joueurs*"

    await ctx.response.send_message(text)


@bot.tree.command(name="rank", description="Affiche le rang d'une personne au Puissance 4")
async def rank(ctx: discord.Interaction, user: typing.Optional[discord.Member]):
    with open("txt/leaderboard.txt", "r+") as file:
        leaderboard_users = [line.split("-") for line in file.readlines()]

    user_id = user.id if user is not None else ctx.user.id

    for i in range(len(leaderboard_users)):
        if str(user_id) in leaderboard_users[i]:
            await ctx.response.send_message(
                f"@{user_id} est **{str(i + 1)}e/{len(leaderboard_users)}** des victoires,"
                f" avec **{leaderboard_users[i][1]} victoires** !")
            break
    leaderboard_users.sort(reverse=True, key=lambda score: float(score[3]))

    for i in range(len(leaderboard_users)):
        name = leaderboard_users[i]
        if str(user_id) in name:
            await ctx.followup.send(
                f"@{user_id} est **{str(i + 1)}e/{len(leaderboard_users)}** des ratios,"
                f" avec **{name[3]} V/D**"
                f" ({str(round(int(name[1]) / (int(name[1]) + int(name[2])) * 100, 2))}%) !"
            )
            logger.info(round(33.3333333333333333, 2))
            return
    await ctx.response.send_message(
        "Mmmmh... Tu n'es pas dans le classement, essaies de jouer !")


@bot.tree.command(name="github", description="Tiens prends mon lien github")
async def github(ctx: discord.Interaction):
    await ctx.response.send_message("Mais avec plaisir !\nhttps://github.com/NozyZy/Le-ptit-bot")


@bot.tree.command(name="ask", description="Déclenche une petite activité aléatoire")
async def ask(ctx: discord.Interaction, text: typing.Optional[str]):
    if text == "" or text is None:
        await ctx.response.send_message("Pose une question andouille")
        return

    if len(text) < 4:
        await ctx.response.send_message("Je vais avoir du mal à te répondre là 🤔")
        return

    if text[len(text) - 1] != "?":
        await ctx.response.send_message("C'est pas une question ça tu sais ?")
        return

    counter = 0
    for letter in text:
        counter += ord(letter)

    today = date.today()
    day = today.strftime("%d")
    month = today.strftime("%m")

    counter += ctx.user.id + int(day) + int(month)

    responses = [
        "Bah oui",
        "Qui sait ? 👀",
        "Absolument pas. Non. Jamais.",
        "Demande à ta mère",
        "Bientôt, tkt frr",
        "https://media.tenor.com/iOoe4V8Va6YAAAAM/well-yes-but-actually-no-meme.gif",
        "Peut-être bien écoute",
        "Carrément ma poule",
        "VREUUUUUUMENT pas",
        "Oublie ça tout de suite",
        "Bah bien sûr, pourquoi tu demandes enfin ?"
    ]

    await ctx.response.send_message(f"> {text}\n" + responses[counter % len(responses)])
    guild_name = ctx.guild.name if ctx.guild else "DM"
    logger.info(f"{ctx.user.name} - {guild_name} - A demandé '{text}' : " + responses[counter % len(responses)])


@bot.tree.command(name="skin", description="Minecraft ?")
async def skin(ctx: discord.Interaction):
    url = "https://mskins.net"
    response = requests.get(url + "/en/skins/random")
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.find_all("a")[62]
    img_tag = tag.find("img")
    img = str(img_tag["src"]) if img_tag else ""
    author = img.split("/")[-1].split("-")[0] if img else "Unknown"
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
    await ctx.response.send_message("Get skinned", embed=embed)


@bot.tree.command(name="panda", description="🐼")
async def panda(ctx: discord.Interaction):
    url = "https://generatorfun.com"
    response = requests.get(url + "/random-panda-image")
    soup = BeautifulSoup(response.text, "html.parser")
    img = str(soup.find_all("img")[0]["src"])
    embed = discord.Embed(
        title="Take that Panda",
        color=0xffffff,
        url=url + "/random-panda-image",
    )
    embed.set_author(
        name=ctx.user.display_name,
        icon_url=
        "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
    )
    embed.set_image(url=url + "/" + img)
    embed.set_footer(text="panda - by generatorfun.com")
    await ctx.response.send_message("🐼", embed=embed)


@bot.tree.command(name="chat", description="😺")
async def chat(ctx: discord.Interaction):
    url = "https://api.thecatapi.com/v1/images/search?limit=1"

    try:
        response = requests.get(url)

        cat_url = response.json()[0]["url"]

        embed = discord.Embed(
            title=random.choice(
                ["Take that cat", "Meow", "Je préfère les chiens, mais bref vasy", "A quand les pandas ?",
                 "Regarde comme il est pips", "j'suis sur qu'il est gros"]),
            color=0xffffff,
            url=cat_url,
        )
        embed.set_author(
            name=ctx.user.display_name,
            icon_url=ctx.user.avatar.url if ctx.user.avatar else None,
        )
        embed.set_image(url=cat_url)
        embed.set_footer(text="chat - by thecatapi.com")
        await ctx.response.send_message("😺", embed=embed)
    except requests.exceptions.RequestException as e:
        await ctx.response.send_message("Pas de chat, j'ai un problème... Désolé :(")


@bot.command()
async def dhcp(ctx, ip_range: str):
    import ipaddress

    try:
        network = ipaddress.IPv4Network(ip_range)
        ips = [str(ip) for ip in network]
        gateway = ips.pop(0)
    except ipaddress.AddressValueError:
        await ctx.send(
            "Tu sais ce que c'est un CIDR ? En gros mets une IP et son masque quoi #IngénieurInformaticien (eg. 192.168.1.0/24)")
        return
    except ValueError:
        await ctx.send("Je pense que tu t'es trompé sur ta range IP mon grand... (eg. 192.168.1.0/24)")
        return

    if ips:
        message = "Réagis avec ✅ pour obtenir une ip !"
        totalTime = 45
        timeLeft = totalTime
        firstMessage = await ctx.send(
            f"Réagis avec ✅ pour obtenir une ip ! Il reste {timeLeft} sec")

        yes = "✅"

        await firstMessage.add_reaction(yes)

        for _ in range(totalTime):
            await asyncio.sleep(1)
            timeLeft -= 1
            await firstMessage.edit(content=message +
                                            f" Il reste {str(timeLeft)} sec")
        await firstMessage.edit(content="Haha y'a plus d'IP !")

        firstMessage = await firstMessage.channel.fetch_message(firstMessage.id)
        users = set()
        for reaction in firstMessage.reactions:

            if str(reaction.emoji) == yes:
                bot_id = bot.user.id if bot.user else None
                async for user in reaction.users():
                    if user.id != bot_id:
                        users.add(user)
        text = """
        Suis les étapes suivantes :
        - Paramètres **Ethernet**
            - Paramètres **IP** : modifier
        - Manuel
        - IPv4 : **activé**
        - Adresse ip **{0}**
        - **SI WINDOWS 11 :**
            - Préfixe sous-réseaux : **{1}**
        - **SI WINDOWS 10 :**
            - Longueur du préfixe sous-réseaux : **{2}**
        - Passerelle : **{3}**
        """

        for user in users:
            ip = ips.pop(0)
            await user.send(text.format(ip, network.netmask, network.prefixlen, gateway))
    else:
        await ctx.send("Sah ya plus d'IP")


@bot.tree.command(name="activity", description="Déclenche une petite activité aléatoire")
async def activity(ctx: discord.Interaction, participants: int):
    url = "https://bored-api.appbrewery.com/filter"
    if participants > 0:
        url += f"?participants={participants}"

    try:
        response = requests.get(url)
        activity = random.choice(response.json())
        author = ctx.user.display_name
        embed = discord.Embed(
            title=activity['activity'],
            color=0xECCE8B,
            url=activity['link'],
        )
        embed.add_field(name="Type", value=activity['type'])
        embed.add_field(name="Participants", value=activity['participants'])
        embed.set_author(
            name=author,
            url=url,
            icon_url=
            "https://cdn.discordapp.com/avatars/653563141002756106/5e2ef5faf8773b5216aca6b8923ea87a.png",
        )
        embed.set_footer(text="provided by bored-api.appbrewery.com")
        await ctx.response.send_message(embed=embed)
    except json.decoder.JSONDecodeError:
        await ctx.response.send_message("Nan ca fonctionne, pas avec ces arguments à prior, c'est balo", ephemeral=True)

@bot.tree.command(name="search", description="Cherche un mot dans mon dictionnaire")
async def search(ctx: discord.Interaction, mot: str):
    with open("txt/dico.txt", "r+") as dico:
        lines = dico.read().split('\n')
    guild_name = ctx.guild.name if ctx.guild else "DM"
    if mot.lower() in lines:
        await ctx.response.send_message(f"Yup, j'ai la connaissance du terme \"{mot}\"")
        logger.info(f"{ctx.user.name} - {guild_name} - A demandé si '{mot}' existe, eh bien oui")
    else:
        await ctx.response.send_message(f"De quoi tu me parles ? C'est quoi \"{mot}\" ?")
        logger.info(f"{ctx.user.name} - {guild_name} - A demandé si '{mot}' existe, bah non")


@bot.command()
async def sync(ctx):
    logger.info("Sync command")
    if ctx.author.id == 359743894042443776:
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
    else:
        await ctx.send('You must be the owner to use this command!')


logger.debug(
    "\n############\nDEV MODE\n############\n" if args.dev else "\n############\n/!\\ PRODUCTION MODE /!\\\n############\n")
TOKEN = os.getenv('DEVELOPMENT_TOKEN') if args.dev else os.getenv('PRODUCTION_TOKEN')
if not TOKEN:
    raise ValueError("TOKEN non défini dans les variables d'environnement")
bot.run(TOKEN)

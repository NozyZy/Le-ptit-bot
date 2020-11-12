import googletrans
import asyncio
import discord
import time
import youtube_dl
import os

from googletrans import Translator
from discord.ext import commands
from datetime import date
from fonctions import *

# ID : 653563141002756106
# https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8

intents = discord.Intents.default()
intents.members = True
client = discord.Client()
bot = commands.Bot(command_prefix="--", description="Le p'tit bot !")


# On ready message
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


# Get every message sent, stocked in 'message'
@bot.event
async def on_message(message):
    channel = message.channel
    Message = message.content.lower()
    rdnb = random.randint(1, 5)
    today = date.today()

    # open and stock the dico, with a lot of words
    dico_file = open("txt/dico.txt", "r+")
    dico_lines = dico_file.readlines()
    dico_size = len(dico_lines)
    dico_file.close()

    if message.author == bot.user:  # we don't want the bot to repeat itself
        return

    # expansion of the dico, with words of every messages (stock only words, never complete message)
    if message.author.id != 696099307706777610:  # we don't what a specific bot (from a friend) to expand the dico
        if "```" in Message:
            return
        mot = ""
        for i in range(len(Message)):
            mot += Message[i]
            if Message[i] == " " or i == len(Message) - 1:
                ponctuation = [" ", ".", ",", ";", "!", "?", "(", ")", "[", "]", ":", "*"]
                for j in ponctuation:
                    mot = mot.replace(j, "")
                if verifAlphabet(mot) and 0 < len(mot) < 27:
                    mot += "\n"
                    if mot not in dico_lines:
                        print(mot)
                        dico_lines.append(mot)
                mot = ""

    dico_lines.sort()
    if len(dico_lines) > 0 and len(dico_lines) > dico_size:
        dico_file = open("txt/dico.txt", "w+")
        for i in dico_lines:
            dico_file.write(i)
        dico_file.close()

    # stock file full of insults (yes I know...)
    fichier_insulte = open("txt/insultes.txt", "r")
    lines_insultes = fichier_insulte.readlines()
    insultes = []
    for i in lines_insultes:
        i = i.replace("\n", "")
        insultes.append(i)
    fichier_insulte.close()

    if message.content.startswith('--addYoutube'):
        print("Ajout de video...")
        mot = str(Message)
        mot = mot.replace("--addyoutube ", "")
        mot = '\n' + mot
        fichier_youtube = open("txt/youtube.txt", "a")
        fichier_youtube.write(mot)
        fichier_youtube.close()
        print(ytb)
        text = ytb[len(ytb) - 1]
        await channel.send(text)

    if message.content.startswith('--searchYoutube'):
        print("Recherche de video...")
        Message = message.content
        mot = str(Message)
        mot = mot.replace("--searchyoutube ", "")
        mots = [mot[0]]
        k = 0
        for i in range(1, len(mot)):
            if mot[i] == ' ':
                k += 1
                mots.append("")
            else:
                mots[k] += mot[i]
        fichier_youtube = open('txt/youtube.txt')
        youtubes_lines = fichier_youtube.readlines()
        for i in youtubes_lines:
            for k in mots:
                print(k, " ", i)
                if k in i:
                    text = i
                    await channel.send(text)
        fichier_youtube.close()

    if message.content.startswith('--addInsult'):
        print("Ajout d'insulte...")
        mot = str(message.content)
        mot = mot.replace(mot[0:12], "")
        if len(mot) <= 2:
            await channel.send("Sympa l'insulte...")
            return
        mot = '\n' + mot
        fichier_insulte = open("txt/insultes.txt", "a")
        fichier_insulte.write(mot)
        fichier_insulte.close()
        text = insultes[len(insultes) - 1]
        await channel.send(text)

    if Message.startswith("--song"):
        fichier_music = open("txt/music.txt", "r")
        lines_music = fichier_music.readlines()
        music = []
        for i in lines_music:
            i = i.replace("\n", "")
            music.append(i)
        fichier_music.close()

        song = "Mauvaise commande.. Pffff... Essaye *help*"
        if 'add' in Message:
            if "https://" not in Message and ("youtu" not in Message or "spotify" not in Message or
                                              "deezer" not in Message or "apple" not in Message):
                song = "Arretes d'envoyer des nudes, et envoie plutot une URL valide.. Tsss..."
            elif "index" in Message:
                song = "Elle est mignonne ta playlist, mais je veux l'URL seule. Merci <3"

            else:
                song = message.content
                song = song.replace("--song add ", "")
                if song in lines_music:
                    song = "Ta musique y est déjà !"
                else:
                    song = '\n' + song
                    fichier_music = open("txt/music.txt", "a")
                    fichier_music.write(song)
                    print("Music", Message)
                    song = 'Alright'

        elif 'all' in Message:
            song = music
            print(music)

        elif 'random' in Message:
            Message = Message.replace("--song ", "")
            song = random.choice(music)
            print("sending", song)

        await channel.send(song)

    # ping a people 10 time, once every 3 sec
    if Message.startswith("--appel <@") and channel.guild != "EFREI International 2025":
        if "<@!653563141002756106>" in Message:
            await channel.send("T'es un marrant toi")
        else:
            nom = Message.replace("--appel ", "")
            liste = ["Allo ", "T'es la ? ", "Tu viens ", "On t'attend...", "Ca commence a faire long ",
                     "Tu viens un jour ??? ", "J'en ai marre de toi... ", "Allez grouille !! ",
                     "Toujours en rertard de toute facon... ", "ALLOOOOOOOOOOOOOOOOOOOOOOOOOO "]
            for i in range(10):
                text = liste[i] + nom
                await channel.send(text)
                time.sleep(3)

    # if you tag this bot in any message (without the above command)
    if "<@!653563141002756106>" in Message and "appel" not in Message:
        user = str(message.author)
        user = user.replace(user[len(user) - 5:len(user)], "")
        rep = ["ya quoi ?!", "Qu'est ce que tu as " + user + " ?", "Oui c'est moi", "Présent !", "*Oui ma bicheuh <3*"]
        if user == "Le Grand bot":
            rep.append('Oui bb ?')
            rep.append('Yo <@!747066145550368789>')
        await channel.send(random.choice(rep))
        return

    # send 5 randoms words from the dico
    if Message == "--random":
        text = ""
        rd_dico = dico_lines
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
    if Message == '--dico':
        text = "J'ai actuellement " + str(len(dico_lines)) + " mots enregistrés, nickel"
        await channel.send(text)

    if Message.startswith("--isdico "):
        text = Message.replace("--isdico ", "")
        text = text.replace(" ", "")
        text += "\n"
        if text in dico_lines:
            await message.add_reaction("👍")
        else:
            await message.add_reaction("👎")
        return

    # begginning of reaction programs, get inspired
    if not Message.startswith('--'):
        print("ca c'est sur")
        if Message.startswith("hein"):
            await channel.send("deux.")

        if Message == 'pas mal':
            reponses = ["mouais", "peut mieux faire", "woaw", ":o"]
            await channel.send(random.choice(reponses))

        if Message == "ez" or Message == "easy":
            reponses = ["https://tenor.com/view/walking-dead-easy-easy-peasy-lemon-squeazy-gif-7268918"]
            await channel.send(random.choice(reponses))

        if Message == 'bite' or Message == 'zizi':
            text = "8" + '=' * random.randint(0, 9) + "D"
            await channel.send(text)

        if 'yanis' in Message and rdnb == 5:
            await channel.send("La Bretagne c'est pas ouf.")

        if Message.startswith("stop") or Message.startswith("arrête") or Message.startswith("arrete"):
            await channel.send("https://tenor.com/view/stop-it-get-some-help-gif-7929301")

        if Message.startswith("exact"):
            reponses = ["Je dirais même plus, exact.", "Il est vrai", "AH BON ??!", "C'est cela", "Plat-il ?", "Jure ?"]
            await channel.send(random.choice(reponses))

        if Message == '<3':
            reponses = ["Nique ta tante (pardon)", "<3", "luv luv", "moi aussi je t'aime ❤"]
            await channel.send(random.choice(reponses))

        if Message == 'toi-même' or Message == "toi-meme" or Message == "toi même" or Message == "toi meme":
            reponses = ["Je ne vous permet pas", "Miroir magique", "C'est celui qui dit qui l'est"]
            await channel.send(random.choice(reponses))

        if "<@!747066145550368789>" in message.content:
            reponses = ['bae', 'Ah oui, cette sous-race de <@!747066145550368789>', "il a moins de bits que moi",
                        "son pere est un con", "ca se dit grand mais tout le monde sait que...."]
            await channel.send(random.choice(reponses))

        if Message == '❤':
            await channel.send('❤')

        if Message == "ben":
            await channel.send("je suis sa pute")

        if Message == '1':
            await channel.send("2")

            # waits for a message valiudating further instructions
            def check(m):
                return m.content == "3" and m.channel == message.channel

            await bot.wait_for('message', check=check)
            await channel.send("SOLEIL !")

        if Message == 'a':
            def check(m):
                return m.content == "b" and m.channel == message.channel

            await bot.wait_for('message', check=check)
            await channel.send("A B C GNEU GNEU MARRANT TROU DU CUL !!!")

        if Message == 'ah':
            if rdnb >= 4:
                reponses = ["Oh", "Bh"]
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace('a', dico_lines))

        if Message == 'oh':
            if rdnb >= 4:
                reponses = ['Quoi ?', 'p', 'ah', ':o']
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace('o', dico_lines))

        if Message == 'eh':
            if rdnb >= 4:
                reponses = ['hehehehehe', 'oh']
                await channel.send(random.choice(reponses))
            else:
                await channel.send(finndAndReplace('é', dico_lines))

        if Message.startswith('merci'):
            if rdnb > 3:
                reponses = ['De rien hehe', "C'est normal t'inquiète", "Je veux le cul d'la crémière avec.", 'non.',
                            'Excuse toi non ?', 'Au plaisir']
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("🥰")

        if Message == 'skusku' or Message == 'sku sku':
            await channel.send("KICÉKIJOUE ????")

        if ('😢' in Message or '😭' in Message) and rdnb >= 3:
            reponses = ['cheh', 'dur dur', "dommage mon p'tit pote", "balec"]
            await channel.send(random.choice(reponses))

        if Message.startswith('tu veux'):
            reponses = ['Ouais gros', 'Carrément ma poule', 'Mais jamais tes fou ptdr', 'Oui.']
            await channel.send(random.choice(reponses))

        if Message.startswith('quoi'):
            reponses = ['feur', 'hein ?', 'nan laisse', 'oublie', 'rien']
            await channel.send(random.choice(reponses))

        if Message.startswith('pourquoi'):
            reponses = ['PARCEQUEEEE', 'Aucune idée.', 'Demande au voisin', 'Pourquoi tu demandes ça ?']
            await channel.send(random.choice(reponses))

        if Message.startswith("t'es sur"):
            reponses = ['Ouais gros', 'Nan pas du tout', 'Qui ne tente rien...']
            await channel.send(random.choice(reponses))

        if Message.startswith("ah ouais") or Message.startswith("ah bon"):
            reponses = ['Ouais gros', 'Nan ptdr', 'Je sais pas écoute...']
            await channel.send(random.choice(reponses))

        if Message.startswith("lourd") and rdnb >= 4:
            await channel.send("Sku sku")

        if '<@!321216514986606592>' in Message and rdnb >= 4:
            reponses = ['Le VP numéro 2', 'Encore lui ?', 'fasstin']
            await channel.send(random.choice(reponses))

        if '<@!761898936364695573>' in Message:
            await channel.send("Tu parles comment de mon pote là ?")

        if '<@!392746536888696834>' in Message:
            reponses = ['Ce trouduc.', 'Ce connard.', 'Ce petit con.', 'Cette petite pute.']
            await channel.send(random.choice(reponses))

        if 'tg' in Message:
            await channel.send(random.choice(insultes))

        if Message == 'cheh' or Message == 'sheh':
            if rdnb >= 3:
                reponses = ["Oh tu t'excuses", "Cheh", "C'est pas gentil ça", "🙁"]
                await channel.send(random.choice(reponses))
            else:
                await message.add_reaction("🥰")

        if "el ali" in Message or "ali oula" in Message:
            await channel.send("💩")

        if Message == 'non':
            reponses = ['si.', "ah bah ca c'est sur", "SÉRIEUX ??", "logique aussi", "jure ?"]
            await channel.send(random.choice(reponses))

        if Message.startswith('lequel') and Message[4] != 'q':
            await channel.send('Le deuxième.')

        if Message.startswith('laquelle'):
            await channel.send('La deuxième.')

        if Message.startswith('miroir magique'):
            await channel.send(Message)

        if Message.startswith("jure"):
            if "wola" in Message:
                await channel.send("Wola")
            elif "wallah" in Message:
                await channel.send("Wallah")

        if "☹" in Message or "😞" in Message or "😦" in Message:
            await message.add_reaction("🥰")

        if Message == 'bv':
            await channel.send("Tes parents t'ont appris la politesse, alors on dit MERCI")

        if Message == 'f' or Message == 'rip':
            await channel.send("#####\n#\n#\n####\n#\n#\n#       to pay respect")

        if ('quentin' in Message or 'quent1' in Message) and rdnb >= 3:
            await channel.send("Papa ! 🤗")

        if Message.startswith("god"):
            day = today.strftime("%d")
            month = today.strftime("%m")
            Message = Message.replace("god", "")

            userID = ""
            if "<@!" not in Message:
                userID = int(message.author.id)
            else:
                i = 0
                for i in range(len(Message)):
                    if Message[i] == '<' and Message[i + 1] == '@' and Message[i + 2] == '!':
                        i += 3
                        userID = ""
                        break
                while Message[i] != '>' and i < len(Message):
                    userID += Message[i]
                    i += 1
                userID = int(userID)
            if userID % 5 != (int(day) + int(month)) % 5:
                await channel.send("Nope, not him.")
                return
            user = await message.guild.fetch_member(userID)
            pfp = user.avatar_url
            embed = discord.Embed(title="This is God", description='<@%s> is god.' % userID, color=0xecce8b)
            embed.set_thumbnail(url=pfp)

            await channel.send("God looks like him.", embed=embed)

        if Message.startswith("hello"):
            await channel.send(file=discord.File('images/helo.jpg'))

        if Message == "enculé" or Message == "enculer":
            image = ['images/tellermeme.png', 'images/bigard.jpeg']
            await channel.send(file=discord.File(random.choice(image)))

        if Message == "stonks":
            await channel.send(file=discord.File('images/stonks.png'))

        if Message == "parfait" or Message == "perfection":
            await channel.send(file=discord.File('images/perfection.jpg'))

        if 'pute' in Message:
            reponses = ["https://tenor.com/view/mom-gif-10756105",
                        "https://tenor.com/view/wiener-sausages-hotdogs-gif-5295979",
                        "https://i.ytimg.com/vi/3HZ0lvpdw6A/maxresdefault.jpg"]
            await channel.send(random.choice(reponses))

        if "guillotine" in Message:
            reponses = ['https://tenor.com/view/guillatene-behead-lego-gif-12352396',
                        'https://tenor.com/view/guillotine-gulp-worried-scared-slug-riot-gif-11539046',
                        'https://tenor.com/view/revolution-guillotine-marie-antoinette-off-with-their-heads-behead-gif-12604431']
            await channel.send(random.choice(reponses))

        if 'pd' in Message:
            Message = ' ' + Message + ' '
            for i in range(len(Message) - 3):
                if Message[i] == ' ' and Message[i + 1] == 'p' and Message[i + 2] == 'd' and Message[i + 3] == ' ':
                    await channel.send(file=discord.File('images/pd.jpg'))

        if 'oof' in Message and rdnb >= 2:
            reponses = ['https://tenor.com/view/oh-snap-surprise-shocked-johncena-gif-5026702',
                        'https://tenor.com/view/oof-damn-wow-ow-size-gif-16490485',
                        'https://tenor.com/view/oof-simpsons-gif-14031953',
                        'https://tenor.com/view/yikes-michael-scott-the-office-my-bad-oof-gif-13450971']
            await channel.send(random.choice(reponses))

        if ('money' in Message or 'argent' in Message) and rdnb >= 2:
            reponses = ['https://tenor.com/view/6m-rain-wallstreet-makeitrain-gif-8203989',
                        'https://tenor.com/view/money-makeitrain-rain-guap-dollar-gif-7391084',
                        'https://tenor.com/view/taka-money-gif-10114852']
            await channel.send(random.choice(reponses))

    # teh help command, add commands call, but not reactions
    if Message == '--help':
        await channel.send("Commandes : \n"
                           " **F** to pay respect\n"
                           " **--serverInfo** pour connaître les infos du server\n"
                           " **--addInsult** pour ajouter des insultes et **tg** pour te faire insulter\n"
                           " **--addWord** pour ajouter un mot au jeu, et **--game** pour jouer au jeu du **clap**\n"
                           " **--repeat** pour que je répète ce qui vient après l'espace\n"
                           " **--appel** puis le pseudo de ton pote pour l'appeler\n"
                           " **--crypt** pour chiffrer/déchiffrer un message César (décalage)\n"
                           " **--random** pour écrire 5 mots aléatoires\n"
                           " **--randint *nb1*, *nb2* ** pour avoir un nombre aléatoire entre ***nb1*** et ***nb2***\n"
                           " **--calcul *nb1* (+, -, /, *, ^, !) *nb2* ** pour avoir un calcul adéquat \n"
                           " **--isPrime** *nb* pour tester si *nb* est premier\n"
                           " **--prime** *nb* pour avoir la liste de tous les nombres premiers jusqu'a *nb* au minimum\n"
                           " **--poll *question*, *prop1*, *prop2*,..., *prop10* ** pour avoir un sondage de max 10 propositions\n"
                           " **--song** puis : **add** *ajoute un morceau à la liste ([URL youtube] - [titre] - [artiste])*\n"
                           "                         **random** *choisit un morceau dans la liste*\n"
                           "                         **all** *affiche toute la liste*\n"
                           "Et je risque de réagir à tes messages, parfois de manière... **Inattendue** 😈")
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
    Message = "".join(text)
    nb2 = 0
    i = 0
    while i < len(Message) and Message[i] != ',':
        if 48 <= ord(Message[i]) <= 57:
            tab.append(Message[i])
        i += 1

    if len(tab) == 0:
        await ctx.send("Rentre un nombre banane")
        return

    nb1 = strToInt(tab)

    if i != len(Message):
        nb2 = strToInt(list=nbInStr(Message, i, len(Message)))

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
    dico_file = open("txt/dico.txt", "r+")
    dico_lines = dico_file.readlines()
    dico_file.close()

    mot = random.choice(dico_lines)
    mot = mot.replace('\n', '')
    text = 'Le premier à écrire **' + mot + '** a gagné'
    await ctx.send(text)

    if ctx.author == bot.user:
        return

    def check(m):
        return m.content == mot and m.channel == ctx.channel

    msg = await bot.wait_for('message', check=check)
    user = str(msg.author)
    user = user.replace(user[len(user) - 5:len(user)], "")
    text = '**' + user + '** a gagné !'
    await ctx.send(text)


@bot.command()  # do a simple calcul of 2 numbers and 1 operator (or a fractionnal)
async def calcul(ctx, *text):
    tab = []
    symbols = ['-', '+', '/', '*', '^', '!']
    Message = "".join(text)
    Message = Message.lower()
    nb2 = i = rd = 0

    if 'infinity' in Message:
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

    if symb == '!':
        if nb1 > 806:  # can't go above 806 recursion deepth
            await ctx.send("806! maximum, désolé 🤷‍♂️")
            return
        rd = facto(nb1)
        text = str(nb1) + '!=' + str(rd)
        await ctx.send(text)
        return

    if i != len(Message):
        tab = nbInStr(Message, i, len(Message))

        if len(tab) == 0:
            await ctx.send("Rentre un deuxième nombre patate")
            return

        nb2 = strToInt(tab)

    if symb == '+':
        rd = nb1 + nb2
    elif symb == '-':
        rd = nb1 - nb2
    elif symb == '*':
        rd = nb1 * nb2
    elif symb == '/':
        if nb2 == 0:
            await ctx.send("±∞")
            return
        rd = float(nb1 / nb2)
    elif symb == '^':
        rd = nb1 ** nb2
    text = str(nb1) + str(symb) + str(nb2) + '=' + str(rd)
    print(text, rd)
    await ctx.send(text)


@bot.command()  # create a reaction poll with a question, and max 10 propositions
async def poll(ctx, *text):
    tab = []
    Message = " ".join(text)
    text = ""
    for i in range(len(Message)):
        if Message[i] == ',':
            tab.append(text)
            text = ""
        elif i == len(Message) - 1:
            text += Message[i]
            tab.append(text)
        else:
            text += Message[i]
    if len(tab) <= 1:
        await ctx.send("Ecris plusieurs choix séparés par des virgules, c'est pas si compliqué que ça...")
        return
    if len(tab) > 11:
        await ctx.send("Ca commence à faire beaucoup non ?... 10 max ca suffit")
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
            await reponse.add_reaction("🔟 ")


@bot.command()  # find and send all the prime numbers until 14064991, can calcul above but can't send it (8Mb limit)
async def prime(ctx, nb: int):
    if nb < 2:
        await ctx.send("Tu sais ce que ca veut dire 'prime number' ?")
        return
    Fprime = open("txt/primes.txt", "r+")
    primes = Fprime.readlines()
    Fprime.close()
    n_max = int(primes[len(primes) - 1].replace('\n', ""))
    print(n_max)
    text = ""
    await ctx.message.add_reaction("👍")
    if n_max < nb:
        if n_max % 2 == 0:
            n_max -= 1
        for i in range(n_max, nb + 1, 2):
            if is_prime(i):
                text += str(i) + '\n'
        Fprime = open("txt/primes.txt", "a+")
        Fprime.write(text)
        Fprime.close()
    if nb > 14064991:  # 8Mb file limit
        text = "Je peux pas en envoyer plus que 14064991, mais tkt je l'ai calculé chez moi là"
        await ctx.send(text)
    text = "Tous les nombres premiers jusqu'a 14064991"
    await ctx.send(text, file=discord.File("txt/prime.txt"))


@bot.command()  # find if 'nb' is a prime number, reacts to the message
async def isPrime(ctx, nb: int):
    if is_prime(nb):
        await ctx.message.add_reaction("👍")
    else:
        await ctx.message.add_reaction("👎")


@bot.command()  # send 'nb' random words of the dico, can repeat itself
async def randomWord(ctx, nb: int):
    dico_file = open("txt/dico.txt", "r+")
    dico_lines = dico_file.readlines()
    dico_file.close()

    text = ""
    for i in range(nb):
        text += random.choice(dico_lines)
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
        discord.FFmpegPCMAudio(song.stream_url,
                               before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

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
async def reboot(ctx):
    os.system("python bot.py")


@bot.command()
async def dl(ctx, *text):
    link = "".join(text)
    text = link.split(',')

    path = text[0]
    link = text[1]

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'flac',
            'preferredquality': '192',
        }],
        'outtmpl': path + '/%(title)s.%(ext)s',
    }

    print("Downloading...", link)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])


@bot.command()
async def translate(ctx, *text):
    translator = Translator()
    text = " ".join(text).lower()
    text = text.split(',')
    if (text[0] == "showall"):
        text[0] = googletrans.LANGUAGES
        await ctx.send(text[0])
        return
    toTranslate = text[0]
    fromLang = text[1].replace(" ", "")
    toLang = text[2].replace(" ", "")
    try:
        textTranslated = translator.translate(toTranslate, src=fromLang, dest=toLang)
        text = toTranslate + ' (' + textTranslated.src + ') -> ' + textTranslated.text + ' (' + textTranslated.dest + ')'
    except:
        text = "Nope, sorry !"
    await ctx.send(text)


"""
@bot.command()
async def say(ctx, number, *text):
    for i in range(int(number)):
        await ctx.send(" ".join(text))
"""


# runs the bot (if you have a TOKEN hahaha)
bot.run(TOKEN)

# Le-ptit-bot
The best discord python bot

![alt text](https://cdn.discordapp.com/attachments/754976677808832512/771094907996733460/unknown.png)

# What is Le ptit bot

This is a discord chatbot, made in Python, that reacts to some message, and can do some things useful.

It is open to everyone, to use and modify it.

-> [Invite link](/https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8)

# How to contribute

1. Clone/Fork this repository <img src="https://github-images.s3.amazonaws.com/help/bootcamp/Bootcamp-Fork.png" alt="fork" width="300"/>
2. Make your changes, here are the things you need to know. 
 - The main file is `bot.py`, where every commands and reaction are, you can use and add funstions in `functions.py`
 - in the `on_message(message)` function :
 				- `channel` is thje variable of the channel, use `await channel.send(text)` to send message containing `text`
 				- `Message` is the variable where the content of the message sent is stocked, but in lowercase. Use `message.content` if you want to match the case.
				- `rdnb` is a random int variable, between 1 and 5, it is used to add probabilities of each reaction to happen (ex : `if rdnb > 3` => 2/5 chance to happen)
 - To add reactions, take the example inside of the `on_message()` function, here is one :
```
if Message.startswith('quoi'):
	reponses = ['feur', 'hein ?', 'nan laisse', 'oublie', 'rien']
	await channel.send(random.choice(reponses))
```
				
- To add commands, the prexif is set at the beginning of the file (`bot = commands.Bot(command_prefix="--", description="Le p'tit bot !"`), so this is --)
	Then, use `@bot.command()` to begin a new command, next line has to be `async def command_name(ctx, other_parameters):`, and then the command call will be the prexif, past top 	the 	name (so here it'll be `--command_name`)
- Be creative, and do be affraid to add things in english, even if it's firstly programed for french users, mixity is good !
3. When you're done, make a pull request to the `dev_improve` branch of my repository, and hope I'll accept your changes (I'm sure you'll do good stuff that I'll approve !)

ENJOY
============

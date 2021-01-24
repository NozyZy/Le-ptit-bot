# Le-ptit-bot
![GitHub](https://img.shields.io/github/license/NozyZy/Le-ptit-bot?style=flat)

The best discord python bot :100:

<img src="https://cdn.discordapp.com/attachments/754976677808832512/771094907996733460/unknown.png" width="400"/>

### What is Le ptit bot

This is a discord chatbot, made in Python, that reacts to some message, and can do a few things useful.

It is open to everyone, to use and modify it.

Here's the [invite link](/https://discordapp.com/oauth2/authorize?&client_id=653563141002756106&scope=bot&permissions=8).

### How to contribute

Core dependancies:

 - python 3.9.0
 - pip 20.2.4
 - discord.py 1.5.1
 - youtube-dl 2020.11.1.1

 
 However, if you would want to install the full list, run `pip install -r requirements.txt` in your virtual environment. 


1. Clone/Fork this repository:
	- All the packages should be in the `venv/Scripts` folder, run `source venv/Scripts/activate` to activate your virtual environment. If they are not in there by any chance, run the command above to install all the dependencies. 


2. Make your changes and commits, but here are some other tips that might be helpful:
	- The main file is `bot.py`, where every commands and reaction are, you can add/change functions in `functions.py`
	- In the `on_message(message)` function :
		- `channel` is a variable defining the channel, use `await channel.send(text)` to send message containing `text`. Unless it's in a command, then use `await ctx.send(text)`
		- `Message` is the variable containing the message sent by a user in lowercase. Use `message.content` if you want to match the case of the original message.
		- `rdnb` stores a random int, between 1 and 5, it is used to determine the probablity of each reaction happening (eg: `if rdnb > 3` then there is a 2/5 chance of happen)
		- To add message reactions, here's an example from the `on_message()` function:
			```python
			if Message.startswith('quoi'):
			reponses = ['feur', 'hein ?', 'nan laisse', 'oublie', 'rien']
			await channel.send(random.choice(reponses))
			```
	- Then, use `@bot.command()` to begin a new command, next line has to be `async def command_name(ctx, other_parameters):`
	- Last but not least, be creative with your commands and do be afraid to add things in english, even if it's intent was for french users, a mix of it is good!

3. When you're done, make a pull request to the `dev_improve` branch of my repository, and hope I'll accept your changes (I'm sure you'll do good stuff that I'll approve of!)

### Have fun and Enjoy!

## License 
MIT - see [LICENSE](https://github.com/NozyZy/Le-ptit-bot/blob/main/LICENSE) file for more details.

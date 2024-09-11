#!/usr/bin/env python3

import string, asyncio, requests, subprocess, logging, logging.config, yaml, signal, sys
from datetime import datetime, timedelta
from os import path, listdir, remove, environ
from pathlib import Path
from twitchio.ext import commands, routines
# import code
# code.interact(local=locals())

logger = logging.getLogger("microbebingo")
logging.config.dictConfig(yaml.safe_load(Path("logconfig.yaml").read_text()))

BOT_CHANNEL_NAME = "microbebingo"
HEALTH_CHECKER_NAME = "dogelectus"
ENTERED_CHANNELS_PATH = "entered_channels.txt"
CARDS_DIR = "/var/www/html/cards/"

entered_channels = Path(ENTERED_CHANNELS_PATH).read_text().split()

@routines.routine(hours=24)
async def remove_old_cards():
	now = datetime.now()
	for filename in listdir(CARDS_DIR):
		filepath = path.join(CARDS_DIR, filename)
		if now -datetime.fromtimestamp(path.getmtime(filepath)) > timedelta(hours=48):
			remove(filepath)
			print(f"Removed: {filepath}")

@routines.routine(hours=1337)
async def token_refresher():
	# Note: This command will fail if you have more than 50 valid access tokens at a time.
	url = "https://id.twitch.tv/oauth2/token"
	headers = { "Content-Type": "application/x-www-form-urlencoded" }
	data = { "client_id": environ["CLIENT_ID"],
			 "client_secret": environ["CLIENT_SECRET"],
			 "grant_type": "refresh_token",
			 "refresh_token": environ["CARDDEALER_REFRESH_TOKEN"] }

	resp = requests.post(url, data=data, headers=headers)

	if resp.status_code != 200:
		raise Exception("Refresh token became invalid") if resp.status_code == 401 else Exception("Something bad happened")

	bot._connection._token = resp.json()["access_token"]
	environ["CARDDEALER_ACCESS_TOKEN"] = resp.json()["access_token"]

	next_refresh = datetime.now() +timedelta(seconds=resp.json()["expires_in"]) -timedelta(minutes=1)
	token_refresher.change_interval(time=next_refresh, wait_first=True)

class MyBot(commands.Bot):

	def __init__(self):
		token_refresher.start()
		super().__init__(token=environ["CARDDEALER_ACCESS_TOKEN"], prefix='!', initial_channels=[*entered_channels,BOT_CHANNEL_NAME])

	async def event_ready(self):
		print(f"=========================================")
		print(f'Microbe Bingo 🦠')
		print(f'Logged in as: {self.nick}')
		print(f'Connected channels({len(self.connected_channels)}):')
		for channel in self.connected_channels:
			print('  ' +channel.name)
		print(f"=========================================")
		remove_old_cards.start()
		logger.info("server_started")
	
	# stop showing "command not found" errors on the screen.
	async def event_command_error(self, context: commands.Context, error: Exception):
		if isinstance(error, commands.CommandNotFound):
			return
		raise error

	@commands.command()
	async def getcard(self, ctx: commands.Context):
		piccode = subprocess.run(['python3', 'make_bingo_card.py'], capture_output=True, text=True).stdout.strip()
		await ctx.send(f"{ctx.author.name} Here's your card: GivePLZ microbebingo.org/{piccode}.png")

		if ctx.author.name != HEALTH_CHECKER_NAME: # don't polute the log
			logger.info("getcard,{}".format({"author":ctx.author.name,"channel":ctx.channel.name,"piccode":piccode}))

	@commands.command()
	async def bingoenter(self, ctx: commands.Context):
		if ctx.channel.name == BOT_CHANNEL_NAME:
			await ctx.send(f"{ctx.author.name} Ok! I entered your chat CoolStoryBob Use !bingoleave if you want me to go away.")
			if not ctx.author.name in entered_channels and all([l in string.ascii_letters+string.digits for l in ctx.author.name]):
				await self.join_channels([ctx.author.name])

				entered_channels += ctx.author.name
				with open(ENTERED_CHANNELS_PATH, "a") as f:
					f.write(ctx.author.name+"\n")
		else:
			await ctx.send(f"{ctx.author.name} I already joined this chat OSFrog Use !getcard to get a bingo card.")

		logger.info("bingoenter,{}".format({"author":ctx.author.name,"channel":ctx.channel.name}))

	@commands.command()
	async def bingoleave(self, ctx: commands.Context):
		if ctx.channel.name in [BOT_CHANNEL_NAME, ctx.author.name]:
			await ctx.send(f"{ctx.author.name} Leaving this chat now! Boop beep MrDestructoid")
			await self.part_channels([ctx.author.name])
			
			entered_channels.remove(ctx.author.name)
			Path(ENTERED_CHANNELS_PATH).write_text("\n".join(entered_channels))
		else:
			await ctx.send(f"{ctx.author.name} Only the channel owner can make me leave SeemsGood")

		logger.info("bingoleave,{}".format({"author":ctx.author.name,"channel":ctx.channel.name}))

# Cancel tasks before exiting otherwise logging will complain. See https://stackoverflow.com/a/64690062/13412674. This is not a complete graceful shutdown, but it's good enough.
def ctrl_c_handler(sig, frame):
	for task in asyncio.all_tasks(bot.loop):
		task.cancel()
	raise KeyboardInterrupt
signal.signal(signal.SIGINT, ctrl_c_handler)
signal.signal(signal.SIGTERM, ctrl_c_handler)

bot = MyBot()
bot.run()

logger.info("server_stopped")


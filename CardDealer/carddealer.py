#!/usr/bin/env python3

import string, asyncio, requests, subprocess, logging, logging.config, yaml, signal, sys, re
from datetime import datetime, timedelta
from os import path, listdir, remove, environ
from urllib.request import urlretrieve, urlcleanup
from pathlib import Path
from base64 import b64encode
from twitchio.ext import commands, routines
from openai import OpenAI
# import code
# code.interact(local=locals())

# Cancel tasks before exiting otherwise logging will complain. See https://stackoverflow.com/a/64690062/13412674.
def ctrl_c_handler(sig, frame):
	# This is not a complete graceful shutdown, but it's good enough.
	for task in asyncio.all_tasks(bot.loop):
		task.cancel()
	raise KeyboardInterrupt
signal.signal(signal.SIGINT, ctrl_c_handler)
signal.signal(signal.SIGTERM, ctrl_c_handler)

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

@routines.routine(hours=1337)
async def token_refresher():
	# Note: This request will fail if you have >50 valid access tokens at a time.
	url = "https://id.twitch.tv/oauth2/token"
	headers = { "Content-Type": "application/x-www-form-urlencoded" }
	data = { "client_id": environ["CLIENT_ID"],
			 "client_secret": environ["CLIENT_SECRET"],
			 "grant_type": "refresh_token",
			 "refresh_token": environ["CARDDEALER_REFRESH_TOKEN"] }
	resp = requests.post(url, data=data, headers=headers)

	if resp.status_code != 200:
		raise Exception("Refresh token became invalid") if resp.status_code == 401 else Exception("Something bad happened")

	environ["CARDDEALER_ACCESS_TOKEN"] = resp.json()["access_token"]

	try: # 'bot' is undefined at first
		bot._connection._token = resp.json()["access_token"]
	except NameError:
		pass

	next_refresh = datetime.now() +timedelta(seconds=resp.json()["expires_in"]) -timedelta(minutes=1)
	token_refresher.change_interval(time=next_refresh, wait_first=True)

class MyBot(commands.Bot):

	def __init__(self):
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
	async def theheck(self, ctx: commands.Context):
		broadcaster = await ctx.channel.user()
		url = "https://api.twitch.tv/helix/clips?broadcaster_id=" +str(broadcaster.id)
		headers = { "Authorization": "Bearer "+environ["CARDDEALER_ACCESS_TOKEN"],
					"Client-Id": environ["CLIENT_ID"] }
		resp = requests.post(url, headers=headers) # reminder: POST makes a clip. GET lists them

		if resp.status_code == 202: # success! now we wait for the clip to be done cooking
			await ctx.send(f"{ctx.author.name} 🔎 Trying to identify microbe currently on screen... (this will take a few seconds) Keep in mind this is an experimental feature, likely to make mistakes ;)")
			await asyncio.sleep(15) # twitch docs: one should consider it a failed clip attempt if after 15s you still get no response

			clip_id = resp.json()["data"][0]["id"]
			url = f"https://api.twitch.tv/helix/clips?id=" +clip_id
			headers = { "Authorization": "Bearer "+environ["CARDDEALER_ACCESS_TOKEN"],
						"Client-Id": environ["CLIENT_ID"] }
			resp = requests.get(url, headers=headers)

			if resp.status_code == 200 and resp.json()["data"] and clip_id == resp.json()["data"][0]["id"]: # 'data' is empty when the clip is either not done processing, or failed to be processed
				mp4_url = re.sub("-preview.*", ".mp4", resp.json()["data"][0]["thumbnail_url"])
				tmp_mp4,_ = urlretrieve(mp4_url) # puts in /tmp by default
				tmp_png = tmp_mp4 +".png"
				subprocess.run(["ffmpeg","-sseof","-5","-i",tmp_mp4,"-frames:v","1","-update","1",tmp_png],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

				TEXT_PROMPT = "The following is a microscope image. Please describe what microorganism is approximately at the center of the screen. What species or family could it be? What's its usual behaviour?What does it like to do? What does it eat? If you can't make out what organism that is, tell me your best guess. You can use emojis if you want to, but it's not mandatory. Make sure your response is shorter than 400 characters."
				image_prompt = b64encode(Path(tmp_png).read_bytes()).decode('utf-8')
				IMG_MIMETYPE = "image/png"

				for i in range(10):
					try:
						completion = client.chat.completions.create(
							model="gpt-4o-mini",
							messages=[{"role":"user","content": [
									{"type":"text","text": TEXT_PROMPT},
									{"type":"image_url","image_url":{"url":f"data:{IMG_MIMETYPE};base64,{image_prompt}","detail":"high"},},],}],)

						if completion.choices[0].message.refusal != None:
							raise Exception("Model refused to answer.")

						if len(chat_reply := f"{ctx.author.name} {completion.choices[0].message.content}") > 500:
							raise Exception("Generated completion is too long.")

						await ctx.send(chat_reply)

					except Exception as e:
						print(f"Supressing exception: {e}")
						continue

					break
				else:
					await ctx.send(f"{ctx.author.name} Failed to get an AI response after a few tries!")

				urlcleanup()
				subprocess.run(["rm", tmp_png])
			else:
				await ctx.send(f"{ctx.author.name} Something went wrong! Probably on twitch's side.")
		else:
			await ctx.send(f"{ctx.author.name} Failed to take screenshot! Maybe the stream is offline? Or clipping is disabled? Or follower-only/sub-only clipping is enabled?")

	@commands.command(aliases=["test?"])
	async def test(self, ctx: commands.Context):
		await ctx.send(f"{ctx.author.name} test...")

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

client = OpenAI()

# Make sure 'bot' has a valid token when initialized.
first_token_refresh_task = token_refresher.start()
try: 
	first_token_refresh_task.get_loop().run_until_complete(first_token_refresh_task)
except asyncio.exceptions.CancelledError: # change_interval() cancels the current task and creates a new one, even though the token_refresher() corotine finishes successfully.
	pass

bot = MyBot()
bot.run()

logger.info("server_stopped")


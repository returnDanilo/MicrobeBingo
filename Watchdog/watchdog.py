#!/usr/bin/env python3

from os import environ, utime
import sys, string, asyncio, requests, subprocess, signal, logging
from datetime import datetime, timedelta
from twitchio.ext import commands, routines
#import code
#code.interact(local=locals())

def ctrl_c_handler(sig, frame):
	for task in asyncio.all_tasks(bot.loop):
		task.cancel()
	raise KeyboardInterrupt
signal.signal(signal.SIGINT, ctrl_c_handler)
signal.signal(signal.SIGTERM, ctrl_c_handler)

logging.basicConfig(filename="logs/watchdog_debug.log", encoding="utf-8", level=logging.DEBUG)

CARDDEALER_USERNAME = "microbebingo"
WATCHDOG_USERNAME = "dogelectus"
REPLY_TO_LOOK_FOR = "Here's your card"

@routines.routine(minutes=30)
async def ask_for_card():
	await bot.get_channel(WATCHDOG_USERNAME).send("!getcard")

# refer to the carddealer implementation should any code be modified
@routines.routine(hours=1337)
async def token_refresher():
	url = "https://id.twitch.tv/oauth2/token"
	headers = { "Content-Type": "application/x-www-form-urlencoded" }
	data = { "client_id": environ["CLIENT_ID"],
			 "client_secret": environ["CLIENT_SECRET"],
			 "grant_type": "refresh_token",
			 "refresh_token": environ["WATCHDOG_REFRESH_TOKEN"] }
	resp = requests.post(url, data=data, headers=headers)
	if resp.status_code != 200:
		raise Exception("Refresh token became invalid") if resp.status_code == 401 else Exception("Something bad happened")
	environ["WATCHDOG_ACCESS_TOKEN"] = resp.json()["access_token"]
	try:
		bot._connection._token = resp.json()["access_token"]
	except NameError:
		pass
	next_refresh = datetime.now() +timedelta(seconds=resp.json()["expires_in"]) -timedelta(minutes=1)
	token_refresher.change_interval(time=next_refresh, wait_first=True)


class MyBot(commands.Bot):
	def __init__(self):
		super().__init__(token=environ["WATCHDOG_ACCESS_TOKEN"], prefix='!', initial_channels=[WATCHDOG_USERNAME])

	async def event_ready(self):
		print(f"-----------------------------------------")
		print(f"Watchdog 👀 🐾")
		print(f"Logged in as: {self.nick}")
		print(f"Listening for messages from: {CARDDEALER_USERNAME}")
		print(f"on channel: {self.connected_channels[0].name}")
		print(f"that match the string: \"{REPLY_TO_LOOK_FOR}\"")
		print(f"-----------------------------------------")

		ask_for_card.start()

	async def event_message(self, msg):
		if msg.author and msg.author.name == CARDDEALER_USERNAME and REPLY_TO_LOOK_FOR in msg.content:  
			utime("last_heartbeat") # like a unix "touch" command


task = token_refresher.start()
try:
	task.get_loop().run_until_complete(task)
except asyncio.exceptions.CancelledError:
	pass

bot = MyBot()
bot.run()


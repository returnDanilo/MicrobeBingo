#!/usr/bin/env python3

from os import environ, utime
import sys, string, asyncio, requests, subprocess, signal
from datetime import datetime, timedelta
from twitchio.ext import commands, routines
#import code
#code.interact(local=locals())

CARDDEALER_USERNAME = "microbebingo"
WATCHDOG_USERNAME = "dogelectus"
REPLY_TO_LOOK_FOR = "Here's your card"

@routines.routine(minutes=30)
async def ask_for_card():
	await bot.get_channel(WATCHDOG_USERNAME).send("!getcard")

# Note: This fails when there are >50 valid access tokens at the same time because of a twitch-enforced limit.
@routines.routine(hours=1337)
async def token_refresher():

	url = "https://id.twitch.tv/oauth2/token"
	data = { "client_id": environ["CLIENT_ID"],
			 "client_secret": environ["CLIENT_SECRET"],
			 "grant_type": "refresh_token",
			 "refresh_token": environ["WATCHDOG_REFRESH_TOKEN"] }
	headers = { "Content-Type": "application/x-www-form-urlencoded" }
	resp = requests.post(url, data=data, headers=headers)

	if resp.status_code != 200:
		raise Exception("Refresh token became invalid") if resp.status_code == 401 else Exception("Something bad happened")

	environ["WATCHDOG_ACCESS_TOKEN"] = resp.json()["access_token"]

	try: # bot is undefined at first
		bot._connection._token = resp.json()["access_token"]
	except NameError:
		pass

	print(f"Got new token: {resp.json()['access_token']}")

	next_refresh = datetime.now() +timedelta(seconds=resp.json()["expires_in"]) -timedelta(minutes=1)
	print(next_refresh)
	token_refresher.change_interval(time=next_refresh, wait_first=True)

try:
	task = token_refresher.start()
	task.get_loop().run_until_complete(task)
except asyncio.exceptions.CancelledError: # I don't know why this is raised every time
	pass

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
			utime("last_heartbeat") # like a unix "touch"

# Cancel tasks before exiting otherwise logging will complain. See https://stackoverflow.com/a/64690062/13412674. This is not a complete graceful shutdown, but it's good enough.
def ctrl_c_handler(sig, frame):
	for task in asyncio.all_tasks(bot.loop):
		task.cancel()
	raise KeyboardInterrupt
signal.signal(signal.SIGINT, ctrl_c_handler)
signal.signal(signal.SIGTERM, ctrl_c_handler)

bot = MyBot()
bot.run()


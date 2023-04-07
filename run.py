import os

import discord
import logging
from dotenv import load_dotenv
from attendancebot import AttendanceBot

load_dotenv()  # take environment variables from .env.
token = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.voice_states = True

client = AttendanceBot(intents=intents)
client.run(token)

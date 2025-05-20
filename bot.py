import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
# intents.message_content = True
# intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

token = os.getenv("DISCORD_BOT_TOKEN")

if token is None:
    raise ValueError("Environment variable DISCORD_BOT_TOKEN belum di-set!")

bot.run(token)

import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask
import threading

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

@app.route("/ping")
def flask_ping():
    return "Ping received from UptimeRobot!"

def run_flask():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5050))
    app.run(host=host, port=port)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise ValueError("Environment variable DISCORD_BOT_TOKEN belum di-set!")

bot.run(token)

import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONS = [
    "cogs.akten",
    "cogs.kennzeichen",
    "cogs.tickets",
    "cogs.support",
    "cogs.notruf",
    "cogs.dashboard",
    "cogs.bewerbung",
    "cogs.admin",
    "cogs.ueberwachung"
]

@bot.event
async def setup_hook():
    for ext in EXTENSIONS:
        await bot.load_extension(ext)
        print(f"geladen: {ext}")

    await bot.tree.sync()
    print("Slash Commands synced")

@bot.event
async def on_ready():
    print(f"BOT ONLINE: {bot.user}")

bot.run(os.getenv("TOKEN"))

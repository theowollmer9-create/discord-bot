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
"cogs.admin"
]

@bot.event
async def on_ready():
    print(f"BOT ONLINE: {bot.user}")
    await bot.tree.sync()

    for ext in EXTENSIONS:
        await bot.load_extension(ext)

bot.run(os.getenv("TOKEN"))

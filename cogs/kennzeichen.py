import discord
from discord.ext import commands
import sqlite3
import re

conn = sqlite3.connect("stasi.db")
c = conn.cursor()

def valid(kz):
    return re.fullmatch(r"[A-Z]{4}-\d{2}", kz)

class Kennzeichen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="kennzeichen")
    async def kennzeichen(self, interaction, user: str, kz: str, fahrzeug: str):

        if not valid(kz):
            return await interaction.response.send_message("❌ Format AAAA-00", ephemeral=True)

        c.execute("INSERT INTO kennzeichen VALUES (NULL,?,?,?)",
                  (user, kz.upper(), fahrzeug))
        conn.commit()

        await interaction.response.send_message("🚗 gespeichert", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Kennzeichen(bot))

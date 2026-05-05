import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect("stasi.db")
c = conn.cursor()

class Akten(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="akte")
    async def akte(self, interaction, user: str):

        c.execute("SELECT tat FROM akten WHERE roblox_user=?", (user,))
        data = c.fetchall()

        text = "\n".join([d[0] for d in data]) or "Keine Daten"

        embed = discord.Embed(title=f"📁 AKTE {user}", description=text)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Akten(bot))

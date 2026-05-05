import discord
from discord.ext import commands
import sqlite3

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("stasi.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS ueberwachung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    status TEXT
)
""")
conn.commit()


class Ueberwachung(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 🔍 ÜBERWACHUNG STARTEN
    # =========================
    @discord.app_commands.command(name="überwachung_start")
    async def start(self, interaction: discord.Interaction, user: str):

        c.execute("INSERT INTO ueberwachung (user, status) VALUES (?, ?)",
                  (user, "AKTIV"))
        conn.commit()

        embed = discord.Embed(
            title="👁️ ÜBERWACHUNG AKTIV",
            description=f"🎮 User: {user}\n📡 Status: AKTIV",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🛑 ÜBERWACHUNG STOPPEN
    # =========================
    @discord.app_commands.command(name="überwachung_stop")
    async def stop(self, interaction: discord.Interaction, user: str):

        c.execute("UPDATE ueberwachung SET status='INAKTIV' WHERE user=?", (user,))
        conn.commit()

        embed = discord.Embed(
            title="👁️ ÜBERWACHUNG BEENDET",
            description=f"🎮 User: {user}\n📡 Status: INAKTIV",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 📄 STATUS ABFRAGEN
    # =========================
    @discord.app_commands.command(name="überwachung_status")
    async def status(self, interaction: discord.Interaction, user: str):

        c.execute("SELECT status FROM ueberwachung WHERE user=?", (user,))
        data = c.fetchone()

        if not data:
            return await interaction.response.send_message("❌ Kein Eintrag", ephemeral=True)

        embed = discord.Embed(
            title="👁️ ÜBERWACHUNGS STATUS",
            description=f"🎮 User: {user}\n📡 Status: {data[0]}",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Ueberwachung(bot))

import discord
from discord.ext import commands
import sqlite3
import re
import os

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("stasi.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS akten (
id INTEGER PRIMARY KEY AUTOINCREMENT,
roblox_user TEXT,
tat TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS kennzeichen (
id INTEGER PRIMARY KEY AUTOINCREMENT,
roblox_user TEXT,
kennzeichen TEXT UNIQUE,
fahrzeug TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS arbeiter_akten (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
job TEXT,
eintrag TEXT,
erstellt_von TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS bewerbungen (
id INTEGER PRIMARY KEY AUTOINCREMENT,
discord_user TEXT,
roblox_user TEXT,
motivation TEXT,
erfahrung TEXT,
status TEXT DEFAULT 'OFFEN'
)""")

conn.commit()

# =========================
# ROLES
# =========================
def is_fuehrung(member):
    return any(r.name in [
        "👑 Minister für Staatssicherheit",
        "🏛️ Stellv. Minister",
        "🛡️ Hauptabteilungsleiter",
        "🏅 Abteilungsleiter"
    ] for r in member.roles)

def is_agent(member):
    return discord.utils.get(member.roles, name="⚙️ Agent")

# =========================
# SUPPORT CHANNELS
# =========================
SUPPORT_CHANNELS = [
"📨・SUPPORT 1","📨・SUPPORT 2","📨・SUPPORT 3","📨・SUPPORT 4","📨・SUPPORT 5",
"📨・SUPPORT 6","📨・SUPPORT 7","📨・SUPPORT 8","📨・SUPPORT 9","📨・SUPPORT 10"
]

# =========================
# VALID KENNZEICHEN
# =========================
def valid_kz(kz):
    return re.fullmatch(r"[A-Z]{4}-\d{2}", kz)

# =========================
# VERIFY (JEDER DARF)
# =========================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verifizieren", style=discord.ButtonStyle.green)
    async def verify(self, interaction, button):

        role = discord.utils.get(interaction.guild.roles, name="⚙️ Agent")

        await interaction.user.add_roles(role)

        await interaction.response.send_message("✅ Verifiziert", ephemeral=True)

# =========================
# TICKET SYSTEM
# =========================
class CloseTicket(discord.ui.View):
    @discord.ui.button(label="❌ Schließen", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        await interaction.channel.delete()

class TicketSystem(discord.ui.View):
    @discord.ui.button(label="🎫 Ticket erstellen", style=discord.ButtonStyle.green)
    async def ticket(self, interaction, button):

        category = discord.utils.get(interaction.guild.categories, name="🔴 |  TICKETS")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }

        ch = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await ch.send("🎫 Ticket erstellt", view=CloseTicket())
        await interaction.response.send_message("Erstellt", ephemeral=True)

# =========================
# BEWERBUNG MODAL
# =========================
class BewerbungModal(discord.ui.Modal, title="🗳️ Bewerbung"):

    roblox_user = discord.ui.TextInput(label="Roblox Name")
    erfahrung = discord.ui.TextInput(label="RP Erfahrung")
    motivation = discord.ui.TextInput(label="Motivation", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):

        c.execute("""
        INSERT INTO bewerbungen (discord_user, roblox_user, motivation, erfahrung)
        VALUES (?,?,?,?)
        """, (
            str(interaction.user),
            self.roblox_user.value,
            self.motivation.value,
            self.erfahrung.value
        ))

        conn.commit()

        channel = discord.utils.get(interaction.guild.text_channels, name="🗳️-𝗡𝗘𝗨𝗘-𝗕𝗘𝗪𝗘𝗥𝗕𝗨𝗡𝗚𝗘𝗡")

        embed = discord.Embed(title="🗳️ NEUE BEWERBUNG", color=discord.Color.orange())
        embed.add_field(name="User", value=str(interaction.user))
        embed.add_field(name="Roblox", value=self.roblox_user.value)
        embed.add_field(name="Erfahrung", value=self.erfahrung.value)
        embed.add_field(name="Motivation", value=self.motivation.value)

        await channel.send(embed=embed)

        await interaction.response.send_message("📨 gesendet", ephemeral=True)

class BewerbungsButton(discord.ui.View):
    @discord.ui.button(label="📝 Bewerben", style=discord.ButtonStyle.green)
    async def apply(self, interaction, button):
        await interaction.response.send_modal(BewerbungModal())

# =========================
# AKTEN
# =========================
@bot.tree.command(name="akte")
async def akte(interaction, roblox_user: str):

    c.execute("SELECT tat FROM akten WHERE roblox_user=?", (roblox_user,))
    data = c.fetchall()

    embed = discord.Embed(title=f"📁 AKTE {roblox_user}")
    embed.description = "\n".join([d[0] for d in data]) or "Keine Daten"

    await interaction.response.send_message(embed=embed)

# =========================
# ARBEITER AKTE
# =========================
@bot.tree.command(name="arbeiter_akte")
async def arbeiter(interaction, name: str):

    c.execute("SELECT job, eintrag, erstellt_von FROM arbeiter_akten WHERE name=?", (name,))
    data = c.fetchall()

    embed = discord.Embed(title=f"👷 ARBEITER {name}", color=discord.Color.green())

    for d in data:
        embed.add_field(name=d[0], value=f"{d[1]} | {d[2]}", inline=False)

    await interaction.response.send_message(embed=embed)

# =========================
# KENNZEICHEN
# =========================
@bot.tree.command(name="kennzeichen")
async def kz(interaction, roblox_user: str, kennzeichen: str, fahrzeug: str):

    if not valid_kz(kennzeichen):
        return await interaction.response.send_message("❌ AAAA-00", ephemeral=True)

    c.execute("INSERT INTO kennzeichen VALUES (NULL,?,?,?)",
              (roblox_user, kennzeichen, fahrzeug))
    conn.commit()

    await interaction.response.send_message("🚗 gespeichert", ephemeral=True)

# =========================
# NOTRUF MIT ORT
# =========================
@bot.tree.command(name="notruf")
async def notruf(interaction, user: str, ort: str, tat: str):

    ch = await interaction.guild.create_text_channel(f"notruf-{user}")

    embed = discord.Embed(
        title="🚨 NOTRUF",
        description=f"{user}\n📍 {ort}\n⚖️ {tat}",
        color=discord.Color.red()
    )

    await ch.send(embed=embed)
    await interaction.response.send_message("🚨 erstellt", ephemeral=True)

# =========================
# DASHBOARD
# =========================
@bot.tree.command(name="dashboard")
async def dashboard(interaction):

    c.execute("SELECT COUNT(*) FROM akten")
    akten = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM kennzeichen")
    kz = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM arbeiter_akten")
    worker = c.fetchone()[0]

    embed = discord.Embed(title="📡 DASHBOARD", color=discord.Color.dark_red())

    embed.add_field(name="Akten", value=akten)
    embed.add_field(name="Kennzeichen", value=kz)
    embed.add_field(name="Arbeiter", value=worker)

    await interaction.response.send_message(embed=embed)

# =========================
# STRAFKATALOG CHANNEL
# =========================
@bot.tree.command(name="kanal_erstellen")
async def kanal(interaction):

    ch = await interaction.guild.create_text_channel("📜・strafkatalog")

    embed = discord.Embed(
        title="𝗦𝗧𝗥𝗔𝗙 𝗞𝗔𝗧𝗔𝗟𝗢𝗚 ⚖️",
        description="🟢 Verwarnung\n🟡 Strafe\n🔴 Haft\n⚫ Staatsfeind",
        color=discord.Color.orange()
    )

    await ch.send(embed=embed)

    await interaction.response.send_message("📜 erstellt", ephemeral=True)

# =========================
# BEWERBEN START
# =========================
@bot.tree.command(name="bewerben")
async def bewerben(interaction):

    ch = discord.utils.get(interaction.guild.text_channels, name="🗳️-𝗕𝗘𝗪𝗘𝗥𝗕𝗨𝗡𝗚")
    await ch.send("🗳️ Bewerbung starten", view=BewerbungsButton())

    await interaction.response.send_message("📨 ready", ephemeral=True)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerifyView())
    bot.add_view(TicketSystem())
    print("BOT ONLINE")

# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))

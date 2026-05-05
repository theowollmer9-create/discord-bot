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
kennzeichen TEXT,
fahrzeug TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS arbeiter_akten (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
job TEXT,
eintrag TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS bewerbungen (
id INTEGER PRIMARY KEY AUTOINCREMENT,
discord_user TEXT,
roblox_user TEXT,
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
# VALID KENNZEICHEN
# =========================
def valid_kz(kz):
    return re.fullmatch(r"[A-Z]{4}-\d{2}", kz)

# =========================
# SUPPORT CHANNELS
# =========================
SUPPORT_CHANNELS = [
"📨・SUPPORT 1","📨・SUPPORT 2","📨・SUPPORT 3","📨・SUPPORT 4","📨・SUPPORT 5",
"📨・SUPPORT 6","📨・SUPPORT 7","📨・SUPPORT 8","📨・SUPPORT 9","📨・SUPPORT 10"
]

# =========================
# VERIFY SYSTEM
# =========================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verifizieren", style=discord.ButtonStyle.green)
    async def verify(self, interaction, button):

        role = discord.utils.get(interaction.guild.roles, name="⚙️ Agent")

        if role:
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

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send("🎫 Ticket erstellt", view=CloseTicket())
        await interaction.response.send_message("✔ Ticket erstellt", ephemeral=True)

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
# KENNZEICHEN
# =========================
@bot.tree.command(name="kennzeichen")
async def kennzeichen(interaction, roblox_user: str, kz: str, fahrzeug: str):

    if not valid_kz(kz):
        return await interaction.response.send_message("❌ AAAA-00 Format!", ephemeral=True)

    c.execute("INSERT INTO kennzeichen VALUES (NULL,?,?,?)",
              (roblox_user, kz.upper(), fahrzeug))
    conn.commit()

    await interaction.response.send_message("🚗 gespeichert", ephemeral=True)

# =========================
# ARBEITER AKTE
# =========================
@bot.tree.command(name="arbeiter_akte")
async def arbeiter(interaction, name: str, job: str, eintrag: str):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    c.execute("INSERT INTO arbeiter_akten VALUES (NULL,?,?,?)",
              (name, job, eintrag))
    conn.commit()

    await interaction.response.send_message("👷 erstellt", ephemeral=True)

# =========================
# NOTRUF
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

    embed = discord.Embed(title="📡 DASHBOARD")

    embed.add_field(name="Akten", value=akten)
    embed.add_field(name="Kennzeichen", value=kz)
    embed.add_field(name="Arbeiter", value=worker)

    await interaction.response.send_message(embed=embed)

# =========================
# 📁 KANAL ERSTELLEN
# =========================
@bot.tree.command(name="kanal_erstellen")
async def kanal_erstellen(interaction, name: str, emoji: str):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    channel_name = f"{emoji} 𝗕𝗘𝗥𝗘𝗜𝗖𝗛 | {name.upper()}"

    await interaction.guild.create_text_channel(name=channel_name)

    await interaction.response.send_message(f"✔ {channel_name} erstellt", ephemeral=True)

# =========================
# 📂 KATEGORIE ERSTELLEN
# =========================
@bot.tree.command(name="kategorie_erstellen")
async def kategorie_erstellen(interaction, name: str, emoji: str):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    cat_name = f"{emoji} | 𝗕𝗘𝗥𝗘𝗜𝗖𝗛 {name.upper()}"

    await interaction.guild.create_category(name=cat_name)

    await interaction.response.send_message(f"✔ {cat_name} erstellt", ephemeral=True)

# =========================
# =========================
# 🆘 SUPPORT SYSTEM (FIXED & FULL)
# =========================
# =========================

@bot.tree.command(name="support_öffnen")
async def support_öffnen(interaction):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    for name in SUPPORT_CHANNELS:
        ch = discord.utils.get(interaction.guild.text_channels, name=name)

        if ch:
            embed = discord.Embed(
                title="🆘 SUPPORT GEÖFFNET",
                description=f"👤 {interaction.user.mention}",
                color=discord.Color.orange()
            )
            await ch.send(embed=embed)
            return await interaction.response.send_message("✔ Support geöffnet", ephemeral=True)

    await interaction.response.send_message("❌ Kein Support frei", ephemeral=True)

@bot.tree.command(name="support_schließen")
async def support_schließen(interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    for name in SUPPORT_CHANNELS:
        ch = discord.utils.get(interaction.guild.text_channels, name=name)

        if ch:
            overwrite = ch.overwrites_for(interaction.guild.default_role)
            overwrite.view_channel = False
            overwrite.send_messages = False
            await ch.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    await interaction.response.send_message("🔒 Support geschlossen", ephemeral=True)

@bot.tree.command(name="support_öffnen_all")
async def support_öffnen_all(interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    for name in SUPPORT_CHANNELS:
        ch = discord.utils.get(interaction.guild.text_channels, name=name)

        if ch:
            overwrite = ch.overwrites_for(interaction.guild.default_role)
            overwrite.view_channel = True
            overwrite.send_messages = True
            await ch.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    await interaction.response.send_message("🟢 Support offen", ephemeral=True)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerifyView())
    bot.add_view(TicketSystem())
    print("BOT ONLINE | STASI FULL SYSTEM READY")

# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))

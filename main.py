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

c.execute("""
CREATE TABLE IF NOT EXISTS akten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roblox_user TEXT,
    tat TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS kennzeichen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roblox_user TEXT,
    kennzeichen TEXT UNIQUE,
    fahrzeug TEXT
)
""")

conn.commit()

# =========================
# SUPPORT CHANNELS
# =========================
SUPPORT_CHANNELS = [
    "📨・SUPPORT 1",
    "📨・SUPPORT 2",
    "📨・SUPPORT 3",
    "📨・SUPPORT 4",
    "📨・SUPPORT 5",
    "📨・SUPPORT 6",
    "📨・SUPPORT 7",
    "📨・SUPPORT 8",
    "📨・SUPPORT 9",
    "📨・SUPPORT 10",
]

# =========================
# RANK CHECK
# =========================
def is_fuehrung(member: discord.Member):
    return any(role.name in [
        "👑 Minister für Staatssicherheit",
        "🏛️ Stellv. Minister",
        "🛡️ Hauptabteilungsleiter",
        "🏅 Abteilungsleiter"
    ] for role in member.roles)

def is_agent(member: discord.Member):
    return discord.utils.get(member.roles, name="⚙️ Agent") is not None

# =========================
# VALID KENNZEICHEN
# =========================
def valid_kz(kz: str):
    return re.fullmatch(r"[A-Z]{4}-\d{2}", kz) is not None

# =========================
# VERIFIKATION
# =========================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verifizieren", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="⚙️ Agent")

        if not role:
            return await interaction.response.send_message("❌ Rolle fehlt", ephemeral=True)

        await interaction.user.add_roles(role)

        await interaction.response.send_message("✅ Verifiziert → ⚙️ Agent", ephemeral=True)

# =========================
# TICKETS
# =========================
class CloseTicket(discord.ui.View):
    @discord.ui.button(label="❌ Schließen", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class TicketSystem(discord.ui.View):
    @discord.ui.button(label="🎫 Ticket erstellen", style=discord.ButtonStyle.green)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="🔴 |  TICKETS")

        if not category:
            return await interaction.response.send_message("❌ Kategorie fehlt", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send("🎫 Ticket erstellt", view=CloseTicket())
        await interaction.response.send_message("✅ Ticket erstellt", ephemeral=True)

# =========================
# MODERATION
# =========================
@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund"):
    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    await member.kick(reason=reason)
    await interaction.response.send_message("👢 gekickt", ephemeral=True)

@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund"):
    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    await member.ban(reason=reason)
    await interaction.response.send_message("🔨 gebannt", ephemeral=True)

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 gelöscht", ephemeral=True)

# =========================
# AKTEN
# =========================
@bot.tree.command(name="akte_erstellen")
async def akte_erstellen(interaction: discord.Interaction, roblox_user: str, tat: str):
    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    c.execute("INSERT INTO akten (roblox_user, tat) VALUES (?, ?)", (roblox_user, tat))
    conn.commit()

    await interaction.response.send_message("📁 Akte erstellt", ephemeral=True)

# =========================
# KENNZEICHEN
# =========================
@bot.tree.command(name="kennzeichen_eintragen")
async def kz_eintragen(interaction: discord.Interaction, roblox_user: str, kennzeichen: str, fahrzeug: str):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    kennzeichen = kennzeichen.upper()

    if not valid_kz(kennzeichen):
        return await interaction.response.send_message("❌ Format AAAA-00", ephemeral=True)

    try:
        c.execute("INSERT INTO kennzeichen VALUES (NULL, ?, ?, ?)",
                  (roblox_user, kennzeichen, fahrzeug))
        conn.commit()
        await interaction.response.send_message("🚗 gespeichert", ephemeral=True)

    except:
        await interaction.response.send_message("❌ existiert", ephemeral=True)

# =========================
# NOTRUF
# =========================
@bot.tree.command(name="notruf")
async def notruf(interaction: discord.Interaction, user: str, tat: str):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    channel = await interaction.guild.create_text_channel(f"notruf-{user}")
    await channel.send(f"🚨 {user}\n{tat}\n{interaction.user.mention}")

    await interaction.response.send_message("🚨 erstellt", ephemeral=True)

# =========================
# SETUP TICKET
# =========================
@bot.tree.command(name="setup_ticket")
async def setup_ticket(interaction: discord.Interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    await interaction.channel.send("🎫 Ticket System", view=TicketSystem())
    await interaction.response.send_message("✅ Setup erstellt", ephemeral=True)

# =========================
# SUPPORT SCHLIESSEN
# =========================
@bot.tree.command(name="support_schliessen")
async def support_schliessen(interaction: discord.Interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    changed = 0
    for channel in interaction.guild.text_channels:
        if channel.name in SUPPORT_CHANNELS:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            changed += 1

    await interaction.response.send_message(f"🔒 {changed} Support geschlossen", ephemeral=True)

# =========================
# SUPPORT ÖFFNEN
# =========================
@bot.tree.command(name="support_oeffnen")
async def support_oeffnen(interaction: discord.Interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    changed = 0
    for channel in interaction.guild.text_channels:
        if channel.name in SUPPORT_CHANNELS:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            changed += 1

    await interaction.response.send_message(f"🔓 {changed} Support geöffnet", ephemeral=True)

# =========================
# UPBRANK
# =========================
@bot.tree.command(name="upbrank")
async def upbrank(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str = "Kein Grund"):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    await member.add_roles(role)

    await interaction.response.send_message(
        f"📈 {member.mention} befördert zu {role.mention}\n📝 Grund: {reason}",
        ephemeral=False
    )

# =========================
# DOWNRANK
# =========================
@bot.tree.command(name="downrank")
async def downrank(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str = "Kein Grund"):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    try:
        await member.remove_roles(role)

        await interaction.response.send_message(
            f"📉 {member.mention} degradiert von {role.mention}\n📝 Grund: {reason}",
            ephemeral=False
        )
    except:
        await interaction.response.send_message("❌ Fehler beim Degradieren", ephemeral=True)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerifyView())
    bot.add_view(TicketSystem())
    print("BOT ONLINE")

bot.run(os.getenv("TOKEN"))

bot.run(os.getenv("TOKEN"))

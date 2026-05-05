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

# 📁 AKTEN
c.execute("""
CREATE TABLE IF NOT EXISTS akten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roblox_user TEXT,
    tat TEXT
)
""")

# 🚗 KENNZEICHEN
c.execute("""
CREATE TABLE IF NOT EXISTS kennzeichen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roblox_user TEXT,
    kennzeichen TEXT UNIQUE,
    fahrzeug TEXT
)
""")

# 👷 ARBEITER AKTEN (PRO)
c.execute("""
CREATE TABLE IF NOT EXISTS arbeiter_akten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    job TEXT,
    eintrag TEXT,
    erstellt_von TEXT,
    zeit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 🗳️ BEWERBUNGEN
c.execute("""
CREATE TABLE IF NOT EXISTS bewerbungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_user TEXT,
    roblox_user TEXT,
    motivation TEXT,
    erfahrung TEXT,
    status TEXT DEFAULT 'OFFEN'
)
""")

# 📊 LOGS
c.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    action TEXT
)
""")

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
# LOG FUNCTION
# =========================
def add_log(user, action):
    c.execute("INSERT INTO logs (user, action) VALUES (?, ?)", (user, action))
    conn.commit()

# =========================
# VALID KENNZEICHEN
# =========================
def valid_kz(kz):
    return re.fullmatch(r"[A-Z]{4}-\d{2}", kz)

# =========================
# =========================
# 👷 ARBEITER AKTEN SYSTEM
# =========================
# =========================

@bot.tree.command(name="arbeiter_akte_erstellen")
async def arbeiter_akte_erstellen(interaction, name: str, job: str, eintrag: str):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    c.execute("""
    INSERT INTO arbeiter_akten (name, job, eintrag, erstellt_von)
    VALUES (?, ?, ?, ?)
    """, (name, job, eintrag, str(interaction.user)))

    conn.commit()

    embed = discord.Embed(
        title="👷‍♂️ ARBEITER-AKTE ERSTELLT",
        color=discord.Color.green()
    )

    embed.add_field(name="👤 Name", value=name, inline=False)
    embed.add_field(name="🧰 Job", value=job, inline=False)
    embed.add_field(name="📄 Eintrag", value=eintrag, inline=False)
    embed.set_footer(text="Staatssicherheit | Personalakte")

    await interaction.response.send_message(embed=embed)

# =========================
# 👷 ARBEITER AKTE ANZEIGEN
# =========================
@bot.tree.command(name="arbeiter_akte")
async def arbeiter_akte(interaction, name: str):

    if not is_agent(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    c.execute("""
    SELECT job, eintrag, erstellt_von, zeit
    FROM arbeiter_akten
    WHERE name=?
    ORDER BY id DESC
    """, (name,))

    data = c.fetchall()

    embed = discord.Embed(
        title=f"👷 ARBEITER AKTE | {name}",
        color=discord.Color.dark_green()
    )

    if not data:
        embed.description = "❌ Keine Einträge"
    else:
        for i, d in enumerate(data[:5]):
            embed.add_field(
                name=f"📌 Eintrag #{i+1}",
                value=f"🧰 {d[0]}\n📄 {d[1]}\n👮 {d[2]}\n🕒 {d[3]}",
                inline=False
            )

    await interaction.response.send_message(embed=embed)

# =========================
# 📊 ARBEITER STATISTIK
# =========================
@bot.tree.command(name="arbeiter_stats")
async def arbeiter_stats(interaction):

    if not is_fuehrung(interaction.user):
        return await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)

    c.execute("SELECT COUNT(*) FROM arbeiter_akten")
    total = c.fetchone()[0]

    c.execute("SELECT job, COUNT(*) FROM arbeiter_akten GROUP BY job")
    jobs = c.fetchall()

    embed = discord.Embed(
        title="📊 ARBEITER STATISTIK",
        color=discord.Color.blue()
    )

    embed.add_field(name="👷 Gesamt Akten", value=str(total), inline=False)

    embed.add_field(
        name="🧰 Jobs",
        value="\n".join([f"{j[0]}: {j[1]}" for j in jobs]) or "Keine Daten",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# =========================
# 📁 NORMALE AKTEN
# =========================
@bot.tree.command(name="akte")
async def akte(interaction, roblox_user: str):

    c.execute("SELECT tat FROM akten WHERE roblox_user=?", (roblox_user,))
    data = c.fetchall()

    embed = discord.Embed(title=f"📁 AKTE {roblox_user}")

    embed.description = "\n".join([d[0] for d in data]) or "Keine Daten"

    await interaction.response.send_message(embed=embed)

# =========================
# 🚗 KENNZEICHEN
# =========================
@bot.tree.command(name="kennzeichen")
async def kz(interaction, roblox_user: str, kennzeichen: str, fahrzeug: str):

    if not valid_kz(kennzeichen):
        return await interaction.response.send_message("❌ Format AAAA-00", ephemeral=True)

    c.execute("INSERT INTO kennzeichen VALUES (NULL,?,?,?)",
              (roblox_user, kennzeichen, fahrzeug))
    conn.commit()

    await interaction.response.send_message("🚗 gespeichert", ephemeral=True)

# =========================
# 🚨 NOTRUF MIT ORT
# =========================
@bot.tree.command(name="notruf")
async def notruf(interaction, user: str, ort: str, tat: str):

    ch = await interaction.guild.create_text_channel(f"notruf-{user}")

    embed = discord.Embed(
        title="🚨 NOTRUF",
        description=f"👤 {user}\n📍 {ort}\n⚖️ {tat}",
        color=discord.Color.red()
    )

    await ch.send(embed=embed)
    await interaction.response.send_message("🚨 erstellt", ephemeral=True)

# =========================
# 📊 DASHBOARD
# =========================
@bot.tree.command(name="dashboard")
async def dashboard(interaction):

    c.execute("SELECT COUNT(*) FROM akten")
    akten = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM kennzeichen")
    kz = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM arbeiter_akten")
    worker = c.fetchone()[0]

    embed = discord.Embed(
        title="📡 STASI DASHBOARD",
        color=discord.Color.dark_red()
    )

    embed.add_field(name="📁 Akten", value=akten)
    embed.add_field(name="🚗 Kennzeichen", value=kz)
    embed.add_field(name="👷 Arbeiter Akten", value=worker)

    await interaction.response.send_message(embed=embed)

# =========================
# 🧠 READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("BOT ONLINE | STASI SYSTEM ACTIVE")

# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))

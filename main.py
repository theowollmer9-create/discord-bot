import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# ===== BOT SETUP =====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATABASE =====
conn = sqlite3.connect("bot.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS akten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roblox_user TEXT,
    tat TEXT
)
""")
conn.commit()

# ===== ROLE CHECKS =====
def is_agent(interaction):
    return discord.utils.get(interaction.user.roles, name="⚙️ Agent") is not None

def is_minister(interaction):
    return discord.utils.get(interaction.user.roles, name="👑 Minister für Staatssicherheit") is not None

# ===== VERIFY UI =====
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verifizieren", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="⚙️ Agent")

        if role is None:
            await interaction.response.send_message("❌ Rolle fehlt!", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ Du bist jetzt verifiziert!", ephemeral=True)

# ===== TICKET UI =====
class CloseTicket(discord.ui.View):
    @discord.ui.button(label="❌ Schließen", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class TicketSystem(discord.ui.View):
    @discord.ui.button(label="🎫 Ticket erstellen", style=discord.ButtonStyle.green)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )

        await channel.send("🎫 Ticket erstellt", view=CloseTicket())
        await interaction.response.send_message("Ticket erstellt!", ephemeral=True)

# ===== READY =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(VerifyView())
    bot.add_view(TicketSystem())
    bot.add_view(CloseTicket())
    print(f"Bot online: {bot.user}")

# ===== VERIFY SETUP =====
@bot.tree.command(name="verify_setup")
async def verify_setup(interaction: discord.Interaction):

    if not is_minister(interaction):
        await interaction.response.send_message("❌ Nur Minister darf das!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔐 Verifizierung",
        description="Bitte klicke auf den Button, um dich zu verifizieren.",
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message("✅ Verify Panel erstellt", ephemeral=True)

# ===== TICKET SETUP =====
@bot.tree.command(name="setup_ticket")
async def setup_ticket(interaction: discord.Interaction):

    if not is_minister(interaction):
        await interaction.response.send_message("❌ Nur Minister darf das!", ephemeral=True)
        return

    await interaction.channel.send("🎫 Ticket System", view=TicketSystem())
    await interaction.response.send_message("✅ Ticket Setup fertig", ephemeral=True)

# ===== AKTE ERSTELLEN =====
@bot.tree.command(name="akte_erstellen")
async def akte_erstellen(interaction: discord.Interaction, roblox_user: str, tat: str):

    if not is_agent(interaction):
        await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)
        return

    c.execute("INSERT INTO akten (roblox_user, tat) VALUES (?, ?)", (roblox_user, tat))
    conn.commit()

    case_id = c.lastrowid

    embed = discord.Embed(
        title="📁 Akte erstellt",
        description=f"🆔 {case_id}\n🎮 {roblox_user}\n⚖️ {tat}",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== AKTE ANZEIGEN =====
@bot.tree.command(name="akte_anzeigen")
async def akte_anzeigen(interaction: discord.Interaction, fall_id: int):

    if not is_agent(interaction):
        await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)
        return

    c.execute("SELECT roblox_user, tat FROM akten WHERE id=?", (fall_id,))
    result = c.fetchone()

    if not result:
        await interaction.response.send_message("❌ Nicht gefunden", ephemeral=True)
        return

    roblox_user, tat = result

    embed = discord.Embed(
        title=f"📁 Akte #{fall_id}",
        description=f"🎮 {roblox_user}\n⚖️ {tat}",
        color=discord.Color.dark_blue()
    )

    await interaction.response.send_message(embed=embed)

# ===== AKTE SUCHEN =====
@bot.tree.command(name="akte_suchen")
async def akte_suchen(interaction: discord.Interaction, roblox_user: str):

    if not is_agent(interaction):
        await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)
        return

    c.execute("SELECT id, tat FROM akten WHERE roblox_user LIKE ?", (f"%{roblox_user}%",))
    results = c.fetchall()

    if not results:
        await interaction.response.send_message("❌ Keine Ergebnisse", ephemeral=True)
        return

    text = ""
    for cid, tat in results:
        text += f"🆔 {cid} | ⚖️ {tat}\n"

    embed = discord.Embed(
        title=f"🔍 Suche: {roblox_user}",
        description=text,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(embed=embed)

# ===== AKTE LÖSCHEN =====
@bot.tree.command(name="akte_loeschen")
async def akte_loeschen(interaction: discord.Interaction, fall_id: int):

    if not is_agent(interaction):
        await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)
        return

    c.execute("DELETE FROM akten WHERE id=?", (fall_id,))
    conn.commit()

    await interaction.response.send_message(f"🗑 Akte #{fall_id} gelöscht", ephemeral=True)

# ===== NOTRUF =====
@bot.tree.command(name="notruf")
async def notruf(interaction: discord.Interaction, roblox_user: str, tat: str):

    if not is_agent(interaction):
        await interaction.response.send_message("❌ Keine Rechte", ephemeral=True)
        return

    channel = await interaction.guild.create_text_channel(f"notruf-{roblox_user}")

    embed = discord.Embed(
        title="🚨 NOTRUF",
        description=f"🎮 {roblox_user}\n⚖️ {tat}\n👤 {interaction.user.mention}",
        color=discord.Color.red()
    )

    await channel.send(embed=embed)
    await interaction.response.send_message("🚨 Notruf erstellt", ephemeral=True)

# ===== START =====
import os
bot.run(os.getenv("TOKEN"))

import discord
from discord.ext import commands

class CloseView(discord.ui.View):
    @discord.ui.button(label="❌ Schließen", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ticket")
    async def ticket(self, interaction):

        category = discord.utils.get(interaction.guild.categories, name="🔴 |  TICKETS")

        ch = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category
        )

        await ch.send("🎫 Ticket erstellt", view=CloseView())

        await interaction.response.send_message("✔ erstellt", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))

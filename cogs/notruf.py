import discord
from discord.ext import commands

class Notruf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="notruf")
    async def notruf(self, interaction, user: str, ort: str, tat: str):

        ch = await interaction.guild.create_text_channel(f"notruf-{user}")

        embed = discord.Embed(
            title="🚨 NOTRUF",
            description=f"{user}\n📍 {ort}\n⚖️ {tat}",
            color=discord.Color.red()
        )

        await ch.send(embed=embed)
        await interaction.response.send_message("🚨 erstellt", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Notruf(bot))

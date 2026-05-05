import discord
from discord.ext import commands

SUPPORT = [
"📨・SUPPORT 1","📨・SUPPORT 2","📨・SUPPORT 3","📨・SUPPORT 4","📨・SUPPORT 5",
"📨・SUPPORT 6","📨・SUPPORT 7","📨・SUPPORT 8","📨・SUPPORT 9","📨・SUPPORT 10"
]

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="support")
    async def support(self, interaction):

        for name in SUPPORT:
            ch = discord.utils.get(interaction.guild.text_channels, name=name)

            if ch:
                await ch.send(f"🆘 Support: {interaction.user.mention}")
                return await interaction.response.send_message("✔ gestartet", ephemeral=True)

        await interaction.response.send_message("❌ keiner frei", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Support(bot))

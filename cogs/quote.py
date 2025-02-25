import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__cog_name__} is ready!")

    @app_commands.command(
        name="quote",
        description="Posts a Quote of a User in the Quote Channel it was set to."
    )
    @app_commands.describe(
        text="The Quote of the User",
        user="The User who said the given Quote.",
        color="A custom Color which the Embed of the Quote will have. (Hex Code)"
    )
    async def quote(
        self, interaction: discord.Interaction, text: str, user: str = None, color: str = None
    ):
        usermention: str
        if user is None:
            usermention = "REDACTED"
        else:
            usermention = user

        # Handle color safely
        try:
            embed_color = discord.Color.from_str(color) if color else discord.Color.from_rgb(69, 69, 69)
        except ValueError:
            embed_color = discord.Color.from_rgb(69, 69, 69)  # Default color if invalid

        lines = text.split("\\n")  # Double backslash required for escaping

        # Create embed
        embed = discord.Embed(
            description="\n".join([f"\"{line}\"" for line in lines]),
            color=discord.Color.from_str(color) if color else discord.Color.from_rgb(69, 69, 69),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"- {usermention}")  # Now properly formatted mention

        # Send Embed
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))

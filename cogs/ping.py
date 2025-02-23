import discord
from discord.ext import commands
from discord import app_commands

class Latency(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot : commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__cog_name__} is ready")

    @app_commands.command(name="ping", description="requests a 'Pong!' + Latency in ms.")
    async def send_pong(self, interaction: discord.Interaction):
        bot_latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Latency: {bot_latency:2}ms", ephemeral=True)
        

async def setup(bot):
    await bot.add_cog(Latency(bot))
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import sys

sys.path.insert(1, "os.")
database = sqlite3.connect("leveling.sqlite")
cursor = database.cursor()

class LeaderBoardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(emoji="\U0001F947", label="Server Leaderboard", description="Shows the Server Leaderboard.", value="local"),
            discord.SelectOption(emoji="\U0001F396", label="Global Leaderboard", description="Shows the Global Leaderboard.", value="global")
        ]
        super().__init__(placeholder="Select Leaderboard..", custom_id="leaderboardselect", options=options)

    @staticmethod
    def get_leaderboard(guild: discord.Guild = None) -> list[tuple]:
        """Fetches the leaderboard from the database."""
        if guild:
            # Fetch top 10 players from the guild's leaderboard
            table_name = f"guild_{guild.id}"
            cursor.execute(f"SELECT user_id, exp, level FROM {table_name} ORDER BY level DESC, exp DESC LIMIT 10")
            return cursor.fetchall()
        else:
            # Fetch top 10 players from the global leaderboard
            cursor.execute("SELECT user_id, exp, level FROM global_leaderboard ORDER BY level DESC, exp DESC LIMIT 10")
            return cursor.fetchall()

    async def callback(self, interaction: discord.Interaction):
        leaderboard_members = self.get_leaderboard(interaction.guild if self.values[0] == "local" else None)
        
        if not leaderboard_members:
            return await interaction.response.send_message("No leaderboard data available.", ephemeral=True)
        
        embed = discord.Embed(
            title="🏆 Leaderboard",
            description=f"Showing the **{'Server' if self.values[0] == 'local' else 'Global'}** Leaderboard",
            color=discord.Color.gold()
        )

        for rank, (user_id, exp, level) in enumerate(leaderboard_members, start=1):
            user = interaction.client.get_user(user_id) or f"Unknown User ({user_id})"
            embed.add_field(
                name=f"#{rank} {user}",
                value=f"Level: **{int(level)}** | XP: **{exp}**",
                inline=False
            )

        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        
        await interaction.response.edit_message(embed=embed)

class LeaderBoardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderBoardSelect())



class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__cog_name__} is ready!")

    @app_commands.command(name="leaderboard", description="Displays the leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        """Command to display the leaderboard selection menu."""
        await interaction.response.send_message("Select a leaderboard to view:", view=LeaderBoardView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
import datetime
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

database = sqlite3.connect("leveling.sqlite")
cursor = database.cursor()


class LeaderBoardView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_leaderboard(guild: discord.Guild) -> list[tuple]:
        if guild:
            table_name = f"guild_{guild.id}"
            cursor.execute(
                f"SELECT user_id, exp, level FROM {table_name} ORDER BY level DESC, exp DESC LIMIT 10"
            )
            return cursor.fetchall()
        return []

    @staticmethod
    async def get_leaderboard_embed(
        guild: discord.Guild, interaction: discord.Interaction
    ) -> list[discord.Embed]:
        if not guild:
            return None

        leaderboard_members = LeaderBoardView.get_leaderboard(guild)
        if not leaderboard_members:
            return None

        embeds = []
        large_embed = discord.Embed(
            color=0x454545,
            timestamp=datetime.datetime.now(),
            description="Ranks 4 - 10:",
        ).set_footer(
            text="Last Refresh at: ",
            icon_url=interaction.client.user.avatar.url,
        )

        for rank, (user_id, exp, level) in enumerate(leaderboard_members, start=1):
            try:
                user = interaction.client.get_user(user_id)  # Try to get user from cache first
                if user is None:  # If not found in cache, fetch from API
                    user = await interaction.client.fetch_user(user_id)
            except discord.NotFound:
                user = f"Unknown User ({user_id})"

            if isinstance(user, discord.User):
                username = user.name
                avatar_url = user.avatar.url if user.avatar else None
            else:
                username = str(user)
                avatar_url = None

            if rank <= 3:
                embed = discord.Embed(
                    color=(
                        discord.Color.from_rgb(255, 215, 0)
                        if rank == 1
                        else discord.Color.from_rgb(192, 192, 192)
                        if rank == 2
                        else discord.Color.from_rgb(205, 127, 50)
                    ),
                    timestamp=datetime.datetime.now(),
                    title=username,
                    description=f"Experience Points: {exp}",
                ).set_author(
                    name=f"{rank}. Place | lvl: {int(level)} ({(level-int(level))*100:.0f}%)",
                    icon_url=avatar_url
                ).set_footer(
                    text="Last Refresh at: ",
                    icon_url=interaction.client.user.avatar.url,
                )
                embeds.append(embed)
            else:
                large_embed.add_field(
                    name=f"{rank}. {username} | lvl: {int(level)} ({(level-int(level))*100:.0f}%)",
                    value=f"Experience Points: {exp}",
                    inline=False,
                )

        embeds.append(large_embed)
        return embeds

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.gray, custom_id="refresh")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = await LeaderBoardView.get_leaderboard_embed(interaction.guild, interaction)
        if embeds:
            await interaction.response.edit_message(embeds=embeds, view=LeaderBoardView())
        else:
            await interaction.response.send_message("No leaderboard data available.", ephemeral=True)


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__cog_name__} is ready!")

    @app_commands.command(name="leaderboard", description="Displays the leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        embeds = await LeaderBoardView.get_leaderboard_embed(interaction.guild, interaction)
        if embeds:
            await interaction.response.send_message(embeds=embeds, view=LeaderBoardView(), delete_after=90)
        else:
            await interaction.response.send_message("No leaderboard data available.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))

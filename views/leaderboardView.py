import discord
from discord.ext import commands
from discord import app_commands
import sqlite3


class LeaderBoardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(emoji=":first_place:", label="Server Leaderboard", description="Shows the Server Leaderboard.", value=0),
            discord.SelectOption(emoji=":medal:", label="Guild Leaderboard", description="Shows the Global Leaderboard.", value=1)
        ]
        super().__init__(placeholder="Select Leaderboard..", custom_id="leaderboardselect", options=options)

    @staticmethod
    def get_leaderboard(guild: discord.Guild = None) -> Exception:
        # add sqlite3 code for getting leaderboard
        if not guild:
            #code for global leaderboard
            return 
        #code for server leaderboard
        raise NotImplementedError.add_note("add needed code as described in comment above Exception raise.")

    async def callback(self, interaction: discord.Interaction):
        0

class LeaderBoardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LeaderBoardSelect())



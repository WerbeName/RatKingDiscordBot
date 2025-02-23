import discord
from discord.ext import commands
from discord import app_commands
import sqlite3


class LeaderBoardSelect(discord.ui.Select):
    def __init__(self):
        super().__init__()

    def get_leaderboard() -> Exception:
        # add sqlite3 code for getting leaderboard
        raise NotImplementedError.add_note("add needed code as described in comment above Exception raise.")

class LeaderBoardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.leaderboards: list[discord.SelectOption] = self.get_leaderboard() # add save type to leaderboard (return type of future get_leaderboard method)

    

    @discord.ui.select(placeholder="Select Leaderboard..", custom_id="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        for leaderboard in self.leaderboards:
            0


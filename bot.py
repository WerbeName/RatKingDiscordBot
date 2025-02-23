import re
import subprocess
import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks

class RatKingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")
        
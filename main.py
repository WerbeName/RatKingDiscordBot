import asyncio
import discord
from dotenv import load_dotenv
import os
from bot import RatKingBot

load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = RatKingBot()

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load()
        await bot.start(token)
        

try:
    asyncio.run(main())
except:
    0
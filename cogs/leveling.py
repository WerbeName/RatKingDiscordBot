from discord.ext import commands, tasks
import discord
from discord import app_commands
import math
import random
import sqlite3
import vacefron
import sys


sys.path.insert(1, "os.")
database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS levels(user_id INTEGER, guild_id INTEGER, exp INTEGER, level INTEGER, last_lvl INTEGER)""")

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_loop.start()  # Startet den Loop, wenn das Cog geladen wird

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = {message.author.id} AND guild_id = {message.guild.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl) VALUES ({message.author.id}, {message.guild.id}, 0, 0, 0)")
            database.commit()
        else:
            exp = result[2]
            lvl = result[3]
            last_lvl = result[4]
            
            exp_gained = random.randint(1, 20)
            exp += exp_gained
            lvl = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE levels SET exp = {exp}, level = {lvl} WHERE user_id = {message.author.id} AND guild_id = {message.guild.id}")
            database.commit()
            
            await self.level_up(message, lvl, last_lvl, cursor, database)

    async def level_up(self, message, lvl, last_lvl, cursor, database):
        if int(lvl) > last_lvl:
            await message.channel.send(f"{message.author.mention} has leveled up to level {int(lvl)}!")
            cursor.execute(f"UPDATE levels SET last_lvl = {int(lvl)} WHERE user_id = {message.author.id} AND guild_id = {message.guild.id}")
            database.commit()

    @tasks.loop(minutes=1)
    async def xp_loop(self):
        """Wird jede Minute ausgeführt und gibt XP an alle Benutzer, die im Voice-Channel sind."""
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot:
                        continue  # Bots ignorieren

                    cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = {member.id} AND guild_id = {guild.id}")
                    result = cursor.fetchone()

                    if result is None:
                        cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl) VALUES ({member.id}, {guild.id}, 0, 0, 0)")
                        database.commit()
                    else:
                        exp = result[2]
                        lvl = result[3]
                        last_lvl = result[4]

                        # XP basierend auf der Dauer im Voice-Channel vergeben (1 XP pro Minute)
                        exp_gained = 1
                        exp += exp_gained
                        lvl = 0.1 * (math.sqrt(exp))

                        print(f"User: {member.name}, Exp: {exp}, Level: {lvl}, Last Level: {last_lvl},_______gained: {exp_gained}xp")
                        cursor.execute(f"UPDATE levels SET exp = {exp}, level = {lvl} WHERE user_id = {member.id} AND guild_id = {guild.id}")
                        database.commit()

                        # Level-up prüfen
                        await self.level_up(member, lvl, last_lvl, cursor, database)

    @app_commands.command(name="rank", description="Shows your rank in the server")
    async def rank(self, interaction: discord.Interaction):
        rank = 1
        # Daten aus der DB holen
        descending = "SELECT * FROM levels WHERE guild_id = ? ORDER BY exp DESC"
        cursor.execute(descending, (interaction.guild.id,))
        result = cursor.fetchall()
        for i in range(len(result)):
            if result[i][0] == interaction.user.id:
                break
            else:
                rank += 1
        cursor.execute("SELECT exp, level, last_lvl FROM levels WHERE user_id = ? AND guild_id = ?", (interaction.user.id, interaction.guild.id))
        result = cursor.fetchone()
        if not result:
            await interaction.response.send_message("You have no rank yet!", ephemeral=True)
            return
        level, exp, last_lvl = result[1], result[0], result[2]
        next_lvl_up = ((int(level) + 1) / 0.1) ** 2
        next_lvl_up = int(next_lvl_up)
        
        rank_card = vacefron.Rankcard(
            username=interaction.user.name,
            avatar_url= interaction.user.avatar.url,
            current_xp=exp,
            next_level_xp=next_lvl_up,
            previous_level_xp=0,
            level=int(level),
            rank=rank,
        )

        card = await vacefron.Client().rank_card(rank_card)
        await interaction.response.send_message(card.url)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} ist jetzt online!')

# Setup-Funktion zum Hinzufügen des Cogs
async def setup(bot):
    await bot.add_cog(Leveling(bot))

from discord.ext import commands, tasks
import discord
from discord import app_commands
import math
import random
import sqlite3
import vacefron
import sys

sys.path.insert(1, "os.")
database = sqlite3.connect("leveling.sqlite")  # Datenbank für alle Guilds
cursor = database.cursor()


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_loop.start()  # Startet den Loop, wenn das Cog geladen wird

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        guild_id = message.guild.id
        table_name = f"guild_{guild_id}"  # Dynamische Tabellennamen je Guild

        # Erstelle Tabelle, wenn sie noch nicht existiert
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                user_id INTEGER,
                exp INTEGER,
                level INTEGER,
                last_lvl INTEGER
            )
        """)
        database.commit()

        cursor.execute(f"SELECT user_id, exp, level, last_lvl FROM {table_name} WHERE user_id = {message.author.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO {table_name} (user_id, exp, level, last_lvl) VALUES ({message.author.id}, 0, 0, 0)")
            database.commit()
        else:
            exp = result[1]
            lvl = result[2]
            last_lvl = result[3]
            
            exp_gained = random.randint(1, 20)
            exp += exp_gained
            lvl = 0.1 * (math.sqrt(exp))

            print(f"User: {message.author.name}\n\tCurrent XP: {exp}\n\tCurrent Level: {lvl}\n\tLast Level: {last_lvl}\n\tGained: {exp_gained}xp\n\n")
            cursor.execute(f"UPDATE {table_name} SET exp = {exp}, level = {lvl} WHERE user_id = {message.author.id}")
            database.commit()
            
            await self.level_up(message, lvl, last_lvl, table_name)

    async def level_up(self, message, lvl, last_lvl, table_name):
        user_id = message.author.id

        if int(lvl) > last_lvl:
            await message.channel.send(f"{message.author.mention} has leveled up to level {int(lvl)}!")
            cursor.execute(f"UPDATE {table_name} SET last_lvl = {int(lvl)} WHERE user_id = {message.author.id}")
            database.commit()


    @tasks.loop(minutes=1)
    async def xp_loop(self):
        """Wird jede Minute ausgeführt und gibt XP an alle Benutzer, die im Voice-Channel sind."""
        for guild in self.bot.guilds:
            table_name = f"guild_{guild.id}"
            
            # Erstelle Tabelle, wenn sie noch nicht existiert
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    user_id INTEGER,
                    exp INTEGER,
                    level INTEGER,
                    last_lvl INTEGER
                )
            """)
            database.commit()

            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot:
                        continue  # Bots ignorieren

                    cursor.execute(f"SELECT user_id, exp, level, last_lvl FROM {table_name} WHERE user_id = {member.id}")
                    result = cursor.fetchone()

                    if result is None:
                        cursor.execute(f"INSERT INTO {table_name} (user_id, exp, level, last_lvl) VALUES ({member.id}, 0, 0, 0)")
                        database.commit()
                    else:
                        exp = result[1]
                        lvl = result[2]
                        last_lvl = result[3]

                        # XP basierend auf der Dauer im Voice-Channel vergeben (1 XP pro Minute)
                        exp_gained = 1
                        exp += exp_gained
                        lvl = 0.1 * (math.sqrt(exp))

                        print(f"User: {member.name}\n\tCurrent XP: {exp}\n\tCurrent Level: {lvl}\n\tLast Level: {last_lvl}\n\tGained: {exp_gained}xp\n\n")
                        cursor.execute(f"UPDATE {table_name} SET exp = {exp}, level = {lvl} WHERE user_id = {member.id}")
                        database.commit()

                        # Level-up prüfen
                        await self.level_up(member, lvl, last_lvl, table_name)

    @app_commands.command(name="rank", description="Shows your rank in the server")
    async def rank(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        table_name = f"guild_{guild_id}"

        # Daten aus der DB holen
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY exp DESC")
        result = cursor.fetchall()

        rank = 1
        for i in range(len(result)):
            if result[i][0] == interaction.user.id:
                break
            else:
                rank += 1

        cursor.execute(f"SELECT exp, level, last_lvl FROM {table_name} WHERE user_id = {interaction.user.id}")
        result = cursor.fetchone()
        if not result:
            await interaction.response.send_message("You have no rank yet!", ephemeral=True)
            return
        level, exp, last_lvl = result[1], result[0], result[2]
        next_lvl_up = ((int(level) + 1) / 0.1) ** 2
        next_lvl_up = int(next_lvl_up)
        
        rank_card = vacefron.Rankcard(
            username=interaction.user.name,
            avatar_url=interaction.user.avatar.url,
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
        print(f'{self.__cog_name__} is ready!')

# Setup-Funktion zum Hinzufügen des Cogs
async def setup(bot):
    await bot.add_cog(Leveling(bot))

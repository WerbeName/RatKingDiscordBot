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

            print(f"\nUser: {message.author.name}\nGained XP: {exp_gained}\nCurrent Level: {lvl:.2f}\tCurrent XP: {exp}")

            cursor.execute(f"UPDATE {table_name} SET exp = {exp}, level = {lvl} WHERE user_id = {message.author.id}")
            database.commit()
            
            await self.level_up(message, lvl, last_lvl, table_name)

    async def level_up(self, obj, lvl, last_lvl, table_name):
        guild_id = obj.guild.id
        cursor.execute("SELECT channel_id FROM leveling_channels WHERE guild_id = ?", (guild_id,))
        level_channel = cursor.fetchone()
        
        if isinstance(obj, discord.Message):
            user_id = obj.author.id
            channel = obj.channel if not level_channel else obj.guild.get_channel(level_channel[0])
            mention = obj.author.mention
        elif isinstance(obj, discord.Member):
            user_id = obj.id
            channel = obj.guild.system_channel if not level_channel else obj.guild.get_channel(level_channel[0])
            mention = obj.mention
        else:
            return
        
        if int(lvl) > last_lvl and channel:
            await channel.send(f"{mention} has leveled up to level {int(lvl)}!")
            cursor.execute(f"UPDATE {table_name} SET last_lvl = {int(lvl)} WHERE user_id = {user_id}")
            database.commit()
            self.update_global_leaderboard(user_id, lvl)

    def update_global_leaderboard(self, user_id, lvl):
        """Checks if the user qualifies for the top 10 global leaderboard and updates it."""
        cursor.execute("SELECT COUNT(*) FROM global_leaderboard")
        count = cursor.fetchone()[0]

        # Check if the player is already in the leaderboard
        cursor.execute("SELECT exp FROM global_leaderboard WHERE user_id = ?", (user_id,))
        existing_entry = cursor.fetchone()

        if existing_entry:
            # Update the player's entry if they improved
            cursor.execute("UPDATE global_leaderboard SET level = ? WHERE user_id = ?", (lvl, user_id))
            database.commit()
        else:
            if count < 10:
                # If there are fewer than 10 entries, simply add the player
                cursor.execute("INSERT INTO global_leaderboard (user_id, exp, level) VALUES (?, ?, ?)", (user_id, 0, lvl))
            else:
                # Check if the new level is higher than the lowest-ranked player
                cursor.execute("SELECT user_id, level FROM global_leaderboard ORDER BY level ASC LIMIT 1")
                lowest = cursor.fetchone()

                if lowest and lvl > lowest[1]:  # If user level > lowest level on leaderboard
                    cursor.execute("DELETE FROM global_leaderboard WHERE user_id = ?", (lowest[0],))
                    cursor.execute("INSERT INTO global_leaderboard (user_id, exp, level) VALUES (?, ?, ?)", (user_id, 0, lvl))

            database.commit()

    @tasks.loop(minutes=1)
    async def xp_loop(self):
        """Wird jede Minute ausgeführt und gibt XP an alle Benutzer, die im Voice-Channel sind."""
        print("XP Loop started")
        
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

            users = []  # Liste für Benutzernamen
            xp_gains = []  # Liste für XP-Gewinne
            
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

                        users.append(member.name)
                        xp_gains.append(str(exp_gained))

                        cursor.execute(f"UPDATE {table_name} SET exp = {exp}, level = {lvl} WHERE user_id = {member.id}")
                        database.commit()

                        # Level-up prüfen
                        await self.level_up(member, lvl, last_lvl, table_name)

            if users:
                print(f"\nUsers: {', '.join(users)}")
                print(f"Gained XP: {', '.join(xp_gains)}\n")


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
    
    @app_commands.command(name="setupleveling", description="Set up a channel for level-up messages")
    async def setupleveling(self, interaction: discord.Interaction, channel_name: str, category: discord.CategoryChannel = None):
        guild_id = interaction.guild.id
        cursor.execute("CREATE TABLE IF NOT EXISTS leveling_channels (guild_id INTEGER, channel_id INTEGER)")
        database.commit()
        
        cursor.execute("SELECT channel_id FROM leveling_channels WHERE guild_id = ?", (guild_id,))
        existing_channel = cursor.fetchone()
        
        if existing_channel:
            await interaction.response.send_message("This server already has a leveling channel set up! Use /resetleveling to change it.", ephemeral=True)
            return
        
        # Channel erstellen
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
        new_channel = await interaction.guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        
        cursor.execute("INSERT INTO leveling_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, new_channel.id))
        database.commit()
        
        await interaction.response.send_message(f"Leveling channel has been set to {new_channel.mention}")

    @app_commands.command(name="resetleveling", description="Reset the leveling channel")
    async def resetleveling(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        cursor.execute("SELECT channel_id FROM leveling_channels WHERE guild_id = ?", (guild_id,))
        existing_channel = cursor.fetchone()
        
        if not existing_channel:
            await interaction.response.send_message("No leveling channel is set up for this server.", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(existing_channel[0])
        if channel:
            await channel.delete()
        
        cursor.execute("DELETE FROM leveling_channels WHERE guild_id = ?", (guild_id,))
        database.commit()
        
        await interaction.response.send_message("Leveling channel has been reset and deleted.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__cog_name__} is ready!')

# Setup-Funktion zum Hinzufügen des Cogs
async def setup(bot):
    await bot.add_cog(Leveling(bot))

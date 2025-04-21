from discord.ext import commands
import discord
from discord import app_commands
import sqlite3
from datetime import datetime
import enum
import re

database = sqlite3.connect("leveling.sqlite")  # Datenbank für alle Guilds
cursor = database.cursor()

class ColorEnum(enum.Enum):
    Red = "red"
    Blue = "blue"
    Green = "green"
    Yellow = "yellow"
    Purple = "purple"
    Orange = "orange"
    Pink = "pink"
    Black = "black"
    White = "white"
    Gray = "gray"

color_map = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "yellow": discord.Color.from_rgb(255, 255, 0),
    "purple": discord.Color.purple(),
    "orange": discord.Color.orange(),
    "pink": discord.Color.from_rgb(255, 192, 203),
    "black": discord.Color.default(),
    "white": discord.Color.from_rgb(255, 255, 255),
    "gray": discord.Color.light_grey()
}

class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__cog_name__} is ready!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return  # Verhindern, dass der Bot auf sich selbst reagiert
        # Hole den Zitat-Channel aus der DB
        guild_id = message.guild.id
        cursor.execute("SELECT channel_id FROM quote_channels WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()

        if not result:
            return  # Kein Quote-Channel, keine Reaktion

        channel_id = result[0]
        quote_channel = message.guild.get_channel(channel_id)

        if not quote_channel:
            return  # Wenn der Quote-Channel nicht mehr existiert

        # Zitat-Pattern mit verschiedenen Formaten
        patterns = [
            r'\"([^\"]+)\"\s*von\s*([^\n]+)',  # "Zitat" von Autor
            r'\"([^\"]+)\"\s*-\s*([^\n]+)',  # "Zitat" - Autor
            r'([^\n]+)\s*von\s*([^\n]+)',  # Zitat von Autor
            r'([^\n]+)\s*[:.]\s*([^\n]+)',  # Zitat: Autor oder Zitat. Autor
            r'\"([^\"]+)\"\s*\|\s*([^\n]+)',  # "Zitat" | Autor
            r'\"([^\"]+)\"\s*\(([^)]+)\)',  # "Zitat" (Autor)
            r'\"([^\"]+)\"\s*\n\s*-\s*([^\n]+)',  # Zitat\n– Autor
            r'\'([^\']+)\'\s*von\s*([^\n]+)',  # 'Zitat' von Autor
            r'\'([^\']+)\'\s*-\s*([^\n]+)',  # 'Zitat' - Autor
            r'\'([^\']+)\'\s*\|\s*([^\n]+)',  # 'Zitat' | Autor
            r'\'([^\']+)\'\s*\(([^)]+)\)',  # 'Zitat' (Autor)
            r'([^\n]+)\s*–\s*([^\n]+)',  # Zitat – Autor (ohne Anführungszeichen)
            r'\"([^\"]+)\"(\s*)–(\s*)([^\n]+)',  # "Zitat"– Autor (mit oder ohne Leerzeichen)
            r'\"([^\"]+)\"\s*;\s*([^\n]+)',  # "Zitat"; Autor
            r'([^\n]+)\s*;\s*([^\n]+)',  # Zitat; Autor
            r'\"([^\"]+)\"[:;]\s*([^\n]+)',  # "Zitat": Autor oder "Zitat"; Autor
            r'\"([^\"]+)\"\s*--\s*([^\n]+)',  # "Zitat" -- Autor
            r'\"([^\"]+)\"\s*~\s*([^\n]+)',  # "Zitat" ~ Autor
            r'\"([^\"]+)\"\s*\.\.\.\s*([^\n]+)',  # "Zitat"... Autor
            r'\"([^\"]+)\"\s*~\s*([^\n]+)',  # "Zitat" ~ Autor
            r'\"([^\"]+)\"\s*<\s*([^\n]+)',  # "Zitat" < Autor
            r'\"([^\"]+)\"\s*>\s*([^\n]+)',  # "Zitat" > Autor
            r'\"([^\"]+)\"\s*\*\*\s*([^\n]+)',  # "Zitat" *** Autor
            r'\"([^\"]+)\"\s*\&\s*([^\n]+)',  # "Zitat" & Autor
            r'\"([^\"]+)\"\s*\|\s*\|\s*([^\n]+)',  # "Zitat" || Autor
            r'\"([^\"]+)\"\s*<\s*\|\s*([^\n]+)',  # "Zitat" <| Autor
            r'\"([^\"]+)\"-\s*([^\n]+)',  # "Zitat"- Autor
            r'\"([^\"]+)\"–\s*([^\n]+)',  # "Zitat"– Autor (langes Bindestrich)
            r'\"([^\"]+)\"\s*~\s*([^\n]+)',  # "Zitat"~ Autor
            r'\"([^\"]+)\"\s*\[\s*([^\n]+)\]',  # "Zitat" [Autor]
            r'\"([^\"]+)\"\s*<\s*([^\n]+)>',  # "Zitat" <Autor>
            r'\"([^\"]+)\"_([^\n]+)',  # "Zitat"_Autor (Unterstrich als Trennung)
            r'([^\n]+)\s*\.\.\.\s*([^\n]+)',  # Zitat... Autor
            r'([^\n]+)\s*\?\s*([^\n]+)',  # Zitat? Autor
            r'([^\n]+)\s*\!\s*([^\n]+)',  # Zitat! Autor
            r'\"([^\"]+)\"\s*<\s*([^\n]+)\s*>',  # "Zitat" < Autor >
        ]

        match_found = False

        for pattern in patterns:
            match = re.match(pattern, message.content)
            if match:
                match_found = True
                quote_text = match.group(1)
                author = match.group(2) if match.group(2) else "Unbekannt"
                
                # Formatieren und Senden
                embed_color = discord.Color.from_rgb(69, 69, 69)  # Standardfarbe
                embed = discord.Embed(
                    description=f"„{quote_text}“",
                    color=embed_color,
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"- {author}")

                # Nachricht löschen und die neue Zitat-Nachricht senden
                await message.delete()
                await quote_channel.send(embed=embed)
                return  # Nachricht wurde umgewandelt und gesendet, daher abbrechen

        # Wenn keine Übereinstimmung gefunden wurde, sende eine private Nachricht an den Benutzer
        embed = discord.Embed(
            title="Invalid Quote Format",
            description=f"The quote is not formatted correctly. Your message: \"{message.content}\"\nPlease use the /quotes command to post quotes in the correct format.",
            color=discord.Color.red()
        )
        await message.reply(embed=embed, delete_after=15)
        
        await message.delete(delay=15)

    @app_commands.command(
        name="quote",
        description="Posts a Quote of a User in the Quote Channel it was set to."
    )
    @app_commands.describe(
        text="The Quote of the User",
        user="The User who said the given Quote.",
        color="A custom Color which the Embed of the Quote will have."
    )
    async def quote(
        self, interaction: discord.Interaction, text: str, user: str = None, color: ColorEnum = None
    ):
        guild_id = interaction.guild.id

        # Hole Channel aus der DB
        cursor.execute("SELECT channel_id FROM quote_channels WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("This server does not have a quote channel set up. Use /setupquote first.", ephemeral=True)
            return

        channel_id = result[0]
        quote_channel = interaction.guild.get_channel(channel_id)

        if not quote_channel:
            await interaction.response.send_message("The quote channel no longer exists. Please set it up again using /setupquote.", ephemeral=True)
            return

        usermention = user if user else "REDACTED"

        # Farbe aus Enum
        embed_color = color_map[color.value] if color else discord.Color.from_rgb(69, 69, 69)

        lines = text.split("\\n")

        embed = discord.Embed(
            description="\n".join([f"\"{line}\"" for line in lines]),
            color=embed_color,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"- {usermention}")

        await quote_channel.send(embed=embed)
        await interaction.response.send_message(f"Quote has been posted in {quote_channel.mention}!", ephemeral=True)

    @app_commands.command(name="setupquote", description="Set up a channel for quoting messages")
    async def setupquotes(self, interaction: discord.Interaction, channel_name: str, category: discord.CategoryChannel = None):
        guild_id = interaction.guild.id
        cursor.execute("CREATE TABLE IF NOT EXISTS quote_channels (guild_id INTEGER, channel_id INTEGER)")
        database.commit()

        cursor.execute("SELECT channel_id FROM quote_channels WHERE guild_id = ?", (guild_id,))
        existing_channel = cursor.fetchone()

        if existing_channel:
            await interaction.response.send_message("This server already has a quote channel set up! Use /resetquotes to change it.", ephemeral=True)
            return

        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
        new_channel = await interaction.guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        cursor.execute("INSERT INTO quote_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, new_channel.id))
        database.commit()

        await interaction.response.send_message(f"Quote channel has been set to {new_channel.mention}")

    @app_commands.command(name="resetquotes", description="Reset the quoting channel")
    async def resetquotes(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        cursor.execute("SELECT channel_id FROM quote_channels WHERE guild_id = ?", (guild_id,))
        existing_channel = cursor.fetchone()

        if not existing_channel:
            await interaction.response.send_message("No quote channel is set up for this server.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(existing_channel[0])
        if channel:
            await channel.delete()

        cursor.execute("DELETE FROM quote_channels WHERE guild_id = ?", (guild_id,))
        database.commit()

        await interaction.response.send_message("Quote channel has been reset and deleted.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))

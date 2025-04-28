import discord
from discord.ext import commands, tasks
from discord import app_commands
import yt_dlp
import asyncio
import random

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.loop_song = {}
        self.currently_playing_message = {}
        self.queue_page = {}

        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'noplaylist': False,
            'quiet': True,
        }
        self.ffmpeg_options = {
            'options': '-vn'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

    async def search_youtube(self, query):
        print(f"Suche auf YouTube: {query}")
        info = self.ytdl.extract_info(f"ytsearch:{query}", download=False)
        video = info['entries'][0]
        print(f"Video gefunden: {video['title']}")
        return [(video['title'], video['webpage_url'])]

    async def get_info(self, url):
        print(f"Infos abrufen für URL: {url}")
        info = self.ytdl.extract_info(url, download=False)
        results = []
        if 'entries' in info:
            print(f"Playlist erkannt: {len(info['entries'])} Einträge")
            for entry in info['entries']:
                results.append((entry['title'], entry['webpage_url']))
        else:
            print("Einzelvideo erkannt.")
            results.append((info['title'], info['webpage_url']))
        return results

    async def get_stream_url(self, url):
        print(f"Stream-URL abrufen für: {url}")
        info = self.ytdl.extract_info(url, download=False)
        return info['url']

    async def play_next(self, guild_id):
        print(f"Spiele nächsten Song für Guild {guild_id}")
        if guild_id not in self.queues or not self.queues[guild_id]:
            print("Keine Songs mehr in der Queue, stoppe Musik.")
            await self.stop_music(guild_id)
            return

        if self.loop_song.get(guild_id):
            print("Song wird in Dauerschleife wiederholt.")
            title, url, stream_url = self.queues[guild_id][0]
        else:
            print("Nächster Song wird geladen.")
            title, url, stream_url = self.queues[guild_id][0]

        vc = self.voice_clients[guild_id]
        try:
            print(f"Versuche Stream zu laden: {stream_url}")
            source = await discord.FFmpegOpusAudio.from_probe(stream_url, **self.ffmpeg_options)
        except Exception as e:
            print(f"Fehler beim Erstellen von FFmpegOpusAudio: {e}")
            await self.stop_music(guild_id)
            return

        def after_playing(error):
            if error:
                print(f"Fehler beim Abspielen: {error}")
            # Song erst hier entfernen, wenn nicht Loop
            if not self.loop_song.get(guild_id) and self.queues.get(guild_id):
                self.queues[guild_id].pop(0)
            # Danach nächsten Song starten
            future = asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)
            try:
                future.result()
            except Exception as exc:
                print(f"Fehler im after_playing-Callback: {exc}")

        vc.play(source, after=after_playing)

        await self.update_currently_playing(guild_id, title, url)

    async def stop_music(self, guild_id):
        print(f"Stoppe Musik und verlasse Voice für Guild {guild_id}")
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
        if guild_id in self.queues:
            del self.queues[guild_id]
        if guild_id in self.loop_song:
            del self.loop_song[guild_id]
        if guild_id in self.currently_playing_message:
            try:
                await self.currently_playing_message[guild_id].delete()
            except Exception as e:
                print(f"Fehler beim Löschen der Nachricht: {e}")
            del self.currently_playing_message[guild_id]

    async def update_currently_playing(self, guild_id, title, url):
        print(f"Aktualisiere Currently Playing Nachricht für Guild {guild_id}")
        channel = self.currently_playing_message[guild_id].channel if guild_id in self.currently_playing_message else None
        if channel is None:
            print("Kein Channel gefunden.")
            return

        if guild_id in self.voice_clients:
            # Den nächsten Song herausfinden
            if len(self.queues[guild_id]) > 1:
                next_title, next_url, _ = self.queues[guild_id][1]
                up_next = f"Nächster Song: [{next_title}]({next_url})"
            else:
                up_next = "Keine weiteren Songs"

            embed = discord.Embed(
                title=":musical_note: Currently Playing",
                description=f"[{title}]({url})",
                color=discord.Color.from_rgb(34, 139, 230)  # Blau, aber mehr lebendig
            )

            # Füge den "Up Next" Song als Feld hinzu
            embed.add_field(
                name=":fast_forward: Next Song",
                value=f"[{next_title}]({next_url})" if len(self.queues[guild_id]) > 1 else "Keine weiteren Songs",
                inline=False
            )

            # Lösche die alte Nachricht, falls sie existiert
            if guild_id in self.currently_playing_message:
                try:
                    await self.currently_playing_message[guild_id].delete()
                except Exception as e:
                    print(f"Fehler beim Löschen der Nachricht: {e}")
            
            # Sende eine neue Nachricht
            msg = await channel.send(embed=embed)
            await self.add_reactions(msg)
            self.currently_playing_message[guild_id] = msg


    async def add_reactions(self, message):
        print(f"Füge Reaktionen hinzu zu Nachricht ID {message.id}")
        emojis = ['⏭', '⏯', '🔁', '🔂', '🗑', '🔀']
        for emoji in emojis:
            await message.add_reaction(emoji)

    @app_commands.command(name="play", description="Spiele Musik ab oder füge zur Warteschlange hinzu")
    @app_commands.describe(query="Titel oder YouTube-Link oder Playlist-Link")
    async def play(self, interaction: discord.Interaction, query: str):
        print(f"/play Command empfangen: {query}")
        await interaction.response.defer()

        if not interaction.user.voice or not interaction.user.voice.channel:
            print("User ist nicht in einem Voice-Channel.")
            return await interaction.followup.send("Du musst in einem Voice-Channel sein.")

        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id

        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            print("Bot connected zu Voice-Channel.")
            vc = await voice_channel.connect()
            self.voice_clients[guild_id] = vc
        else:
            print("Bot bereits verbunden.")
            vc = self.voice_clients[guild_id]

        try:
            if query.startswith("http"):
                tracks = await self.get_info(query)
            else:
                tracks = await self.search_youtube(query)
        except Exception as e:
            print(f"Fehler beim Abrufen der Tracks: {e}")
            return await interaction.followup.send(f"Fehler beim Abrufen: {e}")

        if guild_id not in self.queues:
            self.queues[guild_id] = []

        for title, url in tracks:
            stream_url = await self.get_stream_url(url)
            self.queues[guild_id].append((title, url, stream_url))
            print(f"Hinzugefügt: {title}")

        if len(tracks) > 1:
            await interaction.followup.send(f"Playlist mit **{len(tracks)} Liedern** zur Warteschlange hinzugefügt.")
        else:
            await interaction.followup.send(f"'{tracks[0][0]}' wurde zur Warteschlange hinzugefügt.")

        if not vc.is_playing():
            print("Starte Wiedergabe.")
            title, url, stream_url = self.queues[guild_id][0]
            source = await discord.FFmpegOpusAudio.from_probe(stream_url, **self.ffmpeg_options)
            vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
            msg = await interaction.channel.send(embed=discord.Embed(title=":notes: Lade...", color=discord.Color.blue()))
            self.currently_playing_message[guild_id] = msg
            await self.add_reactions(msg)
            await self.update_currently_playing(guild_id, title, url)
        await self.update_currently_playing(guild_id, title, url)

    @app_commands.command(name="queue", description="Zeigt die aktuelle Warteschlange")
    async def queue(self, interaction: discord.Interaction):
        print("/queue Command empfangen")
        guild_id = interaction.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            return await interaction.response.send_message("Die Warteschlange ist leer.")

        if guild_id not in self.queue_page:
            self.queue_page[guild_id] = 0

        start = self.queue_page[guild_id] * 10
        end = start + 10
        queue_page = self.queues[guild_id][start:end]

        embed = discord.Embed(title="Aktuelle Warteschlange", color=discord.Color.green())
        for i, (title, url, _) in enumerate(queue_page, start=start+1):
            embed.add_field(name=f"{i}.", value=f"[{title}]({url})", inline=False)

        if len(self.queues[guild_id]) > end:
            embed.set_footer(text="▶️ Klicke auf den Emoji, um weiter zu blättern.")
        if self.queue_page[guild_id] > 0:
            embed.set_footer(text="⬅️ Klicke auf den Emoji, um zurück zu blättern.")

        msg = await interaction.response.send_message(embed=embed)
        await self.add_reactions(msg)

    @app_commands.command(name="skip", description="Skipt den aktuellen Song")
    async def skip(self, interaction: discord.Interaction):
        print("/skip Command empfangen")
        guild_id = interaction.guild.id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].stop()
            await interaction.response.send_message("Song wurde übersprungen.")
        else:
            await interaction.response.send_message("Momentan läuft nichts.")

    @app_commands.command(name="pause", description="Pausiert die Musik")
    async def pause(self, interaction: discord.Interaction):
        print("/pause Command empfangen")
        guild_id = interaction.guild.id
        if self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].pause()
            await interaction.response.send_message("Musik pausiert.")

    @app_commands.command(name="resume", description="Setzt die Musik fort")
    async def resume(self, interaction: discord.Interaction):
        print("/resume Command empfangen")
        guild_id = interaction.guild.id
        if self.voice_clients[guild_id].is_paused():
            self.voice_clients[guild_id].resume()
            await interaction.response.send_message("Musik fortgesetzt.")

    @app_commands.command(name="loop", description="Schaltet Song-Dauerschleife um")
    async def loop(self, interaction: discord.Interaction):
        print("/loop Command empfangen")
        guild_id = interaction.guild.id
        self.loop_song[guild_id] = not self.loop_song.get(guild_id, False)
        status = "aktiviert" if self.loop_song[guild_id] else "deaktiviert"
        await interaction.response.send_message(f"Dauerschleife {status}.")

    @app_commands.command(name="shuffle", description="Mische die Warteschlange")
    async def shuffle(self, interaction: discord.Interaction):
        print("/shuffle Command empfangen")
        guild_id = interaction.guild.id
        if guild_id in self.queues:
            random.shuffle(self.queues[guild_id])
            await interaction.response.send_message("Warteschlange wurde gemischt.")

    @app_commands.command(name="disconnect", description="Bot verlässt den Voice-Channel")
    async def disconnect(self, interaction: discord.Interaction):
        print("/disconnect Command empfangen")
        guild_id = interaction.guild.id
        await self.stop_music(guild_id)
        await interaction.response.send_message("Bot hat den Voice-Channel verlassen.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__cog_name__} ist bereit!')

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))


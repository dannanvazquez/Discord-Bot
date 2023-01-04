import asyncio

import nextcord
import youtube_dl
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

# Sets youtube_dl formatting options properly.
ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(nextcord.PCMVolumeTransformer):
    # Initialize as singleton
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    # Get the song from a YouTube URL
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    song_queue = []

    def __init__(self, bot):
        self.bot = bot

    # Slash command that joins the user's voice channel.
    @nextcord.slash_command(name="join", description="Joins your voice channel")
    async def join(self, interaction: Interaction):
        if interaction.user.voice:
            await interaction.send("Joining your voice channel!", ephemeral=True)
            return await interaction.user.voice.channel.connect()
        else:
            await interaction.send("You must be in a voice channel for me to join!", ephemeral=True)

    # Plays the next song in queue once a song is finished.
    async def play_next(self, interaction):
        if len(self.song_queue) > 1:
            player = await YTDLSource.from_url(self.song_queue[1][0], loop=self.bot.loop, stream=True)
            interaction.guild.voice_client.play(player, after=lambda e: Music.play_next(self, interaction))
            embed = nextcord.Embed(title = "Now Playing", description = player.title, color = 0x3ccbe8)
            embed.set_footer(text = f"Added by {self.song_queue[1][2]}")
            await self.song_queue[1][1].send(embed=embed)
        else:
            embed = nextcord.Embed(title = "No more songs in queue.", color = 0x3ccbe8)
            await self.song_queue[0][1].send(embed=embed)
            await interaction.guild.voice_client.disconnect()
        del self.song_queue[0]
    
    # Slash command that plays a song by title name or YouTube URL. Without any parameter, it plays the current song in queue if paused.
    @nextcord.slash_command(name="play", description="Plays a youtube video given the title or link. Without a parameter, unpauses the current video!")
    async def play(self, interaction: Interaction, song: str = SlashOption(description="Song title or URL", required=False)):
        """Streams from a URL on YouTube"""
        if song is not None:
            song_listing = [song, interaction.channel, interaction.user]
            self.song_queue.append(song_listing)
            player = await YTDLSource.from_url(song, loop=self.bot.loop, stream=True)
            if len(self.song_queue) == 1:
                interaction.guild.voice_client.play(player, after=lambda e: Music.play_next(self, interaction))
                embed = nextcord.Embed(title = "Now Playing", description = player.title, color = 0x3ccbe8)
                await interaction.send(embed=embed)
            else:
                await interaction.send(embed=nextcord.Embed(title = "Song has been added to the queue!", description = player.title, color = 0x1fab13))
        else:
            if not interaction.voice_client.is_playing() and len(self.song_queue) > 0:
                interaction.voice_client.resume()
                await interaction.send("The player has been resumed")
            else:
                await interaction.send("Specify what song you would like to play by using '/play <song name or url>'", ephemeral=True)

    # Slash command that pauses the current song. If already paused, then it resumes the current song in queue.
    @nextcord.slash_command(name="pause", description="Pauses/resumes the current song that's playing.")
    async def pause(self, interaction: Interaction): 
        """Pauses/resumes the current song"""
        if not interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.pause()
            await interaction.send("The music player is now paused")
        else:
            interaction.guild.voice_client.resume()
            await interaction.send("The music player has been resumed")

    # Slash command that skips the currently playing song.
    @nextcord.slash_command(name="skip", description="Skips the current song that's playing.")
    async def skip(self, interaction: Interaction):
        """Skips the current song"""
        if len(self.song_queue) > 0:
            interaction.guild.voice_client.stop()
            await interaction.send("Skipping the current song!")
        else:
            await interaction.send("Nothing is currently playing.", ephemeral=True)

    # Slash command to stop the bot from playing any more music and leave the voice channel.
    @nextcord.slash_command(name="stop", description="Clears the queue and disconnects from voice channel.")
    async def stop(self, interaction: Interaction):
        """Stops and disconnects the bot from voice"""

        self.song_queue.clear()
        await interaction.guild.voice_client.disconnect()
        await interaction.send(f"Cleared the queue and disconnected!")

    # Makes sure that the user is in a voice channel before executing commands.
    @join.before_invoke
    @play.before_invoke
    @pause.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    async def ensure_voice(interaction: Interaction):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                await interaction.send("You are not connected to a voice channel.", ephemeral=True)
                raise commands.CommandError("Author not connected to a voice channel.")

def setup(bot):
    bot.add_cog(Music(bot))
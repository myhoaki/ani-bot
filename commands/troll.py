import asyncio
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands

log = logging.getLogger("ani")


@commands.command(name="troll")
@commands.guild_only()
async def troll_command(ctx: commands.Context):
    """Play a random MP3 in your current voice channel, then leave."""

    if not isinstance(ctx.author, discord.Member) or not ctx.author.voice:
        await ctx.send("Join a voice channel first, then use `?ani troll`.")
        return

    sound_dir = Path(__file__).resolve().parent.parent / "sounds"
    sound_files = sorted(
        path for path in sound_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".mp3"
    ) if sound_dir.exists() else []

    if not sound_files:
        await ctx.send("No MP3 files found in Ani's `sounds/` folder.")
        return

    voice_client = ctx.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        await ctx.send("oi, one sound at a time.")
        return

    sound_file = random.choice(sound_files)

    try:
        target_channel = ctx.author.voice.channel

        if voice_client is None:
            voice_client = await target_channel.connect()
        elif voice_client.channel != target_channel:
            await voice_client.move_to(target_channel)

        finished = asyncio.Event()
        loop = asyncio.get_running_loop()
        source = discord.FFmpegPCMAudio(str(sound_file))

        voice_client.play(
            source,
            after=lambda error: loop.call_soon_threadsafe(finished.set),
        )
        log.info("Playing troll sound: %s", sound_file.name)
        await ctx.send(f"🔊 Ani is deploying `{sound_file.name}`.")
        await finished.wait()

    except Exception:
        log.exception("Failed to play troll sound")
        await ctx.send(
            "Couldn't play that sound. Check Ani's logs and voice permissions."
        )
    finally:
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect(force=True)

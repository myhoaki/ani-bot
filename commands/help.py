import discord
from discord.ext import commands


async def help_command(ctx: commands.Context):
    embed = discord.Embed(
        title="Ani Bot Commands",
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Voice",
        value="`?ani troll` — play a random sound in your voice channel",
        inline=False,
    )

    embed.add_field(
        name="AI",
        value="`?ani talk <topic>` — ask Ani to start a conversation",
        inline=False,
    )

    await ctx.send(embed=embed)

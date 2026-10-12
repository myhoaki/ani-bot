from discord.ext import commands


async def help_command(ctx: commands.Context):
    await ctx.send(
        "**Ani Bot — Commands**\n"
        "\n"
        "`?ani help` — show this help message\n"
        "`?ani troll` — play a random sound in your current voice channel\n"
        "`?ani talk <topic>` — ask Ani to start a conversation about a topic"
    )

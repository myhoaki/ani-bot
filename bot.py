import os
import logging

import discord
from discord.ext import commands

from conversation import ConversationManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ani")

TOKEN = os.getenv("DISCORD_TOKEN")
KAT_BOT_ID = int(os.getenv("KAT_BOT_ID", "0"))
CONVERSATION_CHANNEL_ID = int(os.getenv("CONVERSATION_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!ani ",
    intents=intents,
    help_command=None,
)

conversation = ConversationManager(
    bot=bot,
    kat_bot_id=KAT_BOT_ID,
    channel_id=CONVERSATION_CHANNEL_ID,
)


@bot.event
async def on_ready():
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)
    conversation.start()


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        if message.author.id == KAT_BOT_ID:
            await conversation.handle_kat_message(message)
        return

    await bot.process_commands(message)


@bot.command()
async def talk(ctx: commands.Context):
    """Manually make Ani start a conversation with Kat."""
    if ctx.channel.id != CONVERSATION_CHANNEL_ID:
        return

    await conversation.start_conversation()


@bot.command()
async def stop(ctx: commands.Context):
    """Stop an active Ani/Kat conversation."""
    if ctx.channel.id != CONVERSATION_CHANNEL_ID:
        return

    conversation.stop()
    await ctx.send("Fine. I'll stop bothering Kat. For now.")


@bot.command()
async def status(ctx: commands.Context):
    """Show Ani's conversation status."""
    if ctx.channel.id != CONVERSATION_CHANNEL_ID:
        return

    state = conversation.status()
    await ctx.send(
        f"Active: `{state['active']}` | "
        f"Turns: `{state['turns']}/{state['max_turns']}`"
    )


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

if not KAT_BOT_ID:
    raise RuntimeError("KAT_BOT_ID is not set")

if not CONVERSATION_CHANNEL_ID:
    raise RuntimeError("CONVERSATION_CHANNEL_ID is not set")

bot.run(TOKEN)

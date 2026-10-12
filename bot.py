from commands.help import help_command
from commands.troll import troll_command
from commands.talk import create_talk_command
import logging

import discord
from discord.ext import commands

from core.conversation import ConversationManager
from core.reactions import maybe_react
from core.stickers import maybe_send_sticker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ani")

from core.config import DISCORD_TOKEN, KAT_BOT_ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    help_command=None,
)

conversation = ConversationManager(
    bot=bot,
    kat_bot_id=KAT_BOT_ID,
)


@bot.event
async def on_ready():
    log.info("Logged in as %s (%s)", bot.user, bot.user.id)


@bot.event
async def on_message(message: discord.Message):
    await maybe_react(
        message,
        bot.user.id if bot.user else 0,
        KAT_BOT_ID,
    )
    await maybe_send_sticker(
        message,
        bot.user.id if bot.user else 0,
        KAT_BOT_ID,
    )

    if message.author.bot:
        if message.author.id == KAT_BOT_ID:
            await conversation.handle_kat_message(message)
        return

    await bot.process_commands(message)


@bot.group(name="ani", invoke_without_command=True)
async def ani(ctx: commands.Context):
    """Ani bot commands."""
    pass


@ani.command(name="help")
async def ani_help(ctx: commands.Context):
    await help_command(ctx)



# Register commands under the ?ani command group.
ani.add_command(troll_command)
ani.add_command(create_talk_command(conversation))

bot.run(DISCORD_TOKEN)

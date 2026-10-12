import random
import re
import time
import discord

CHANNEL_COOLDOWN = 30
USER_COOLDOWN = 60
REACTION_CHANCE = 0.5

last_channel_reaction = {}
last_user_reaction = {}

EMOTES = {
    r"\b(lol|lm(ao|fao)|rofl|hilarious|crying|br(uh|h)|ke(k|kw)|funny|af|based)\b":
        "<:ICANT:1283491796336381972>",
    r"\b(what|huh|excuse me|no way|seriously|wtf|wth)\b|\?{2,}":
        "<:nani:1415655246188904510>",
    r"\b(do(n't|nt)|stop|yikes|uncomfortable|d(ied|ead|ed)|no idea)\b":
        "<:xdx:1559054639117115463>",
    r"\b(gacha|NTE|Ananta|pity|pulls|banner|waifu|must pull|unhinged|cursed|bs|breed|grape|raep|wait)\b":
        "<:giga_mpreg:1512315959279353986>",
    r"\b(joever|never|sadly|faker|wild|mood|jebaited|usd|fail|failed)\b":
        "<:Forte:1559054325387362365>",
}


async def maybe_react(message, own_bot_id, partner_bot_id):
    if message.author.id == own_bot_id:
        return

    # Only react to people or the paired Kat bot, not unrelated bots.
    if message.author.bot and message.author.id != partner_bot_id:
        return

    content = message.content.strip().lower()
    if not content or content.startswith("?"):
        return

    # Find a relevant emote before rolling the low reaction chance.
    candidates = [
        emote for pattern, emote in EMOTES.items()
        if re.search(pattern, content, re.IGNORECASE)
    ]
    if not candidates or random.random() > REACTION_CHANCE:
        return

    now = time.monotonic()
    channel_id = message.channel.id
    user_id = message.author.id

    if now - last_channel_reaction.get(channel_id, 0) < CHANNEL_COOLDOWN:
        return
    if now - last_user_reaction.get(user_id, 0) < USER_COOLDOWN:
        return

    emote = random.choice(candidates)
    try:
        await message.add_reaction(discord.PartialEmoji.from_str(emote))
    except Exception as exc:
        print(f"[Reactions] Failed to react: {exc}", flush=True)
        return

    last_channel_reaction[channel_id] = time.monotonic()
    last_user_reaction[user_id] = time.monotonic()

import random
import re
import time

CHANNEL_COOLDOWN = 30
USER_COOLDOWN = 60
REACTION_CHANCE = 0.5

last_channel_reaction = {}
last_user_reaction = {}

EMOTES = {
    r"\b(lmao|lmfao|rofl|i can.t|ican.t|dead|💀|hilarious|crying)\b":
        "<:ICANT:1283491796336381972>",
    r"\b(what|huh|excuse me|no way|seriously|wtf|wth)\b|\?{2,}":
        "<:nani:1415655246188904510>",
    r"\b(awkward|cringe|embarrassing|yikes|uncomfortable)\b":
        "<:worry_awksmile:1389654049476837406>",
    r"\b(gacha|50.?50|pity|pulls|banner|waifu|must acquire|unhinged|cursed)\b":
        "<:giga_mpreg:1512315959279353986>",
    r"\b(lol|lmao|bruh|bro|wild|insane|ridiculous|skill issue)\b":
        "<:Crunny:1493600039950356620>",
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
        await message.add_reaction(emote)
    except Exception as exc:
        print(f"[Reactions] Failed to react: {exc}", flush=True)
        return

    last_channel_reaction[channel_id] = time.monotonic()
    last_user_reaction[user_id] = time.monotonic()

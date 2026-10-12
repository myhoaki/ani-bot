import random
import re
import time

import discord

STICKER_CHANCE = 0.25
CHANNEL_COOLDOWN = 60
USER_COOLDOWN = 120

STICKERS = [
    {
        "id": 1342013897934372886,
        "keywords": ["yes", "damn", "doro", "Ani", "powerful"],
    },
    {
        "id": 1293582242152710214,
        "keywords": ["waifu", "must pull", "interested", "attention"],
    },
]

last_channel_sticker = {}
last_user_sticker = {}


async def maybe_send_sticker(message, own_bot_id, other_bot_id):
    if not message.guild or not message.content:
        return

    if message.author.id == own_bot_id:
        return

    if message.author.bot and message.author.id != other_bot_id:
        return

    now = time.monotonic()
    channel_id = message.channel.id
    user_id = message.author.id

    if now - last_channel_sticker.get(channel_id, 0) < CHANNEL_COOLDOWN:
        return

    if now - last_user_sticker.get(user_id, 0) < USER_COOLDOWN:
        return

    content = message.content.lower()
    matches = []

    for entry in STICKERS:
        for keyword in entry["keywords"]:
            pattern = r"(?<!\w)" + re.escape(keyword.lower()).replace(
                r"\ ", r"\s+"
            ) + r"(?!\w)"

            if re.search(pattern, content):
                matches.append(entry)
                break

    if not matches or random.random() >= STICKER_CHANCE:
        return

    entry = random.choice(matches)
    sticker = discord.utils.get(message.guild.stickers, id=entry["id"])

    if sticker is None:
        print(
            f"[Stickers] Ani sticker {entry['id']} isn't available "
            f"in server {message.guild.id}"
        )
        return

    try:
        await message.channel.send(stickers=[sticker])
        last_channel_sticker[channel_id] = time.monotonic()
        last_user_sticker[user_id] = time.monotonic()
        print(f"[Stickers] Ani sent sticker {sticker.id}")
    except discord.HTTPException as exc:
        print(f"[Stickers] Ani failed to send sticker: {exc}")

import discord
import asyncio
import os
import random
import re
import time

from discord.ext import tasks

from ai import generate_reply


MIN_TURNS = int(os.getenv("MIN_TURNS", "3"))
MAX_TURNS = int(os.getenv("MAX_TURNS", "8"))
RESPONSE_TIMEOUT = int(os.getenv("KAT_RESPONSE_TIMEOUT", "90"))
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "12"))


class ConversationManager:
    def __init__(self, bot, kat_bot_id: int, channel_id: int):
        self.bot = bot
        self.kat_bot_id = kat_bot_id
        self.channel_id = channel_id

        self.active = False
        self.turns = 0
        self.max_turns = 0
        self.history: list[dict[str, str]] = []
        self.last_started = 0.0
        self._waiting_for_kat = False
        self._timeout_task: asyncio.Task | None = None


    @staticmethod
    def _split_messages(text: str) -> list[str]:
        """Split model output into short, separate Discord messages."""
        messages = [line.strip() for line in text.splitlines() if line.strip()]

        if len(messages) == 1 and len(messages[0]) > 180:
            sentences = re.split(r"(?<=[.!?])\\s+", messages[0])
            if len(sentences) > 1:
                messages = [part.strip() for part in sentences if part.strip()]
            else:
                words = messages[0].split()
                messages = [
                    " ".join(words[i:i + 12])
                    for i in range(0, len(words), 12)
                ]

        return messages[:4]

    async def _send_burst(
        self,
        channel,
        text: str,
        *,
        mention_first: bool = False,
    ):
        messages = self._split_messages(text)
        if not messages:
            messages = ["oi"]

        for index, message in enumerate(messages):
            await self._send_to_kat(
                channel,
                message,
                mention_kat=mention_first and index == 0,
            )
            if index < len(messages) - 1:
                await asyncio.sleep(random.uniform(0.8, 1.6))

    async def start_conversation(self, topic: str):
        if self.active:
            return False

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            return False

        self.active = True
        self.turns = 0
        self.max_turns = random.randint(MIN_TURNS, MAX_TURNS)
        self.history = []
        self.last_started = time.monotonic()

        topic = topic.strip()
        if not topic:
            self.stop()
            return False

        try:
            opener = generate_reply(
                self.history,
                (
                    "Start a casual conversation with Kat about this topic: "
                    f"{topic}\n\n"
                    "IMPORTANT OUTPUT FORMAT:\n"
                    "- Write 2-4 short Discord messages, one message per line.\n"
                    "- Each line will be sent as a separate Discord message.\n"
                    "- Usually 3-12 words per line. Fragments are good.\n"
                    "- No paragraphs, no blank lines, no numbering or bullet points.\n"
                    "- Think out loud, make an observation, add a tangent, or react.\n"
                    "- Do not write an essay or explain the joke.\n"
                    "- Sound like Ani chatting with a friend, not an assistant.\n"
                    "- Sometimes one or two lines are enough; do not pad with filler.\n"
                    "- Do not include a Kat mention; the bot adds it to the first message.\n"
                    "- Do not explain that you were told to start a conversation."
                ),
            )
            await self._send_burst(channel, opener, mention_first=True)
            self._arm_response_timeout()
            return True
        except Exception:
            self.stop()
            raise

    async def handle_kat_message(self, message):
        if not self.active or message.author.id != self.kat_bot_id:
            return

        if message.channel.id != self.channel_id:
            return

        self._cancel_timeout()
        self._waiting_for_kat = False
        self.history.append({"role": "user", "text": f"Kat: {message.content}"})
        self.history = self.history[-HISTORY_LIMIT:]
        self.turns += 1

        if self.turns >= self.max_turns:
            self.stop()
            return

        try:
            reply = generate_reply(
                self.history,
                (
                    "Continue the ongoing casual Discord conversation with Kat.\n\n"
                    "IMPORTANT OUTPUT FORMAT:\n"
                    "- Write 1-3 short Discord messages, one message per line.\n"
                    "- Each line will be sent as a separate Discord message.\n"
                    "- Usually 2-10 words per line. Fragments and reactions are good.\n"
                    "- No paragraphs, no blank lines, no numbering or bullet points.\n"
                    "- React to Kat's actual message, tease him, or continue a shared joke.\n"
                    "- Ani can think out loud, change direction, or mention a friend.\n"
                    "- Statements and emotes are often better than questions.\n"
                    "- Do not force a punchline or keep the conversation going artificially.\n"
                    "- Never write a polished monologue or explain the joke."
                ),
            )
            await self._send_burst(message.channel, reply)

            if self.turns >= self.max_turns:
                self.stop()
            else:
                self._arm_response_timeout()
        except Exception as exc:
            print(f"Ani conversation error: {exc}")
            self.stop()

    async def _send_to_kat(self, channel, text: str, *, mention_kat: bool = False):
        kat_mention = f"<@{self.kat_bot_id}>"

        text = re.sub(
            rf"<@!?{self.kat_bot_id}>",
            "",
            text,
        ).strip()

        if mention_kat:
            text = re.sub(r"(?i)@kat(?:\s+bot)?\b", "", text).strip()
            text = f"{kat_mention} {text}"[:1990]
            allowed_mentions = discord.AllowedMentions(
                users=[discord.Object(id=self.kat_bot_id)]
            )
        else:
            text = re.sub(r"(?i)@kat(?:\s+bot)?\b", "Kat", text)
            text = text[:1900]
            allowed_mentions = discord.AllowedMentions.none()

        text = text.strip()
        self.history.append({"role": "model", "text": f"Ani: {text}"})
        self.history = self.history[-HISTORY_LIMIT:]
        self._waiting_for_kat = True

        await channel.send(text, allowed_mentions=allowed_mentions)

    def _arm_response_timeout(self):
        self._cancel_timeout()
        self._timeout_task = asyncio.create_task(self._expire_if_kat_is_silent())

    def _cancel_timeout(self):
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
        self._timeout_task = None

    async def _expire_if_kat_is_silent(self):
        try:
            await asyncio.sleep(RESPONSE_TIMEOUT)
            if self.active and self._waiting_for_kat:
                print("Kat did not reply before the conversation timeout.")
                self.stop()
        except asyncio.CancelledError:
            pass

    def stop(self):
        self._cancel_timeout()
        self.active = False
        self._waiting_for_kat = False
        self.history.clear()

    def status(self):
        return {
            "active": self.active,
            "turns": self.turns,
            "max_turns": self.max_turns,
        }

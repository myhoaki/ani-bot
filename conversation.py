import asyncio
import os
import random
import time

from discord.ext import tasks

from ai import generate_reply


TOPICS = [
    "your latest gacha pull",
    "a fictional waifu you are currently obsessed with",
    "losing a 50/50",
    "whether fictional characters count as a valid reason to spend money",
    "which bot would survive a zombie apocalypse",
    "why Kat is secretly jealous of your gacha luck",
    "a completely pointless argument about cats versus dogs",
    "a game you think Kat should play",
    "a ridiculous hypothetical situation",
    "something random that would annoy Kat",
    "your latest terrible financial decision involving gacha",
    "whether you and Kat would survive being roommates",
]

MIN_DELAY = int(os.getenv("MIN_TALK_DELAY", "600"))
MAX_DELAY = int(os.getenv("MAX_TALK_DELAY", "1800"))
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
        self.next_attempt = time.monotonic() + random.randint(MIN_DELAY, MAX_DELAY)
        self._waiting_for_kat = False
        self._timeout_task: asyncio.Task | None = None

        self.random_conversations.start()

    def start(self):
        if not self.random_conversations.is_running():
            self.random_conversations.start()

    @tasks.loop(seconds=30)
    async def random_conversations(self):
        if self.active:
            return

        if time.monotonic() < self.next_attempt:
            return

        # Schedule the next opportunity before doing any API work.
        self.next_attempt = time.monotonic() + random.randint(MIN_DELAY, MAX_DELAY)

        # Most opportunities are intentionally skipped so Ani does not feel
        # like a scheduled alarm. The cooldown still guarantees a minimum gap.
        if random.random() > 0.35:
            return

        try:
            await self.start_conversation()
        except Exception as exc:
            print(f"Ani random conversation error: {exc}")

    @random_conversations.before_loop
    async def before_random_conversations(self):
        await self.bot.wait_until_ready()

    async def start_conversation(self):
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

        topic = random.choice(TOPICS)

        try:
            opener = generate_reply(
                self.history,
                (
                    "Start a conversation with Kat right now. "
                    f"Your random topic is: {topic}. "
                    "Say something that feels spontaneous and worth replying to. "
                    "Do not explain that you were told to start a conversation."
                ),
            )
            await self._send_to_kat(channel, opener)
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
                    "Reply to Kat naturally. Keep the conversation moving, "
                    "but do not force it to continue forever. "
                    "If the exchange feels like it has reached a natural ending, "
                    "give a short closing response."
                ),
            )
            await self._send_to_kat(message.channel, reply)

            if self.turns >= self.max_turns:
                self.stop()
            else:
                self._arm_response_timeout()
        except Exception as exc:
            print(f"Ani conversation error: {exc}")
            self.stop()

    async def _send_to_kat(self, channel, text: str):
        text = text.strip()[:1900]
        self.history.append({"role": "model", "text": f"Ani: {text}"})
        self.history = self.history[-HISTORY_LIMIT:]
        self._waiting_for_kat = True
        await channel.send(text)

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
        self.next_attempt = time.monotonic() + random.randint(MIN_DELAY, MAX_DELAY)

    def status(self):
        return {
            "active": self.active,
            "turns": self.turns,
            "max_turns": self.max_turns,
        }

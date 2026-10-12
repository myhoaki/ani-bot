import discord
import asyncio
import random
import re
import time

from discord.ext import tasks

from core.ai import generate_reply
from core.config import (
    MIN_TURNS,
    MAX_TURNS,
    RESPONSE_TIMEOUT,
    HISTORY_LIMIT,
)


class ConversationManager:
    def __init__(self, bot, kat_bot_id: int):
        self.bot = bot
        self.kat_bot_id = kat_bot_id
        self.channel_id = None

        self.active = False
        self.turns = 0
        self.max_turns = 0
        self.history: list[dict[str, str]] = []
        self.last_started = 0.0
        self._waiting_for_kat = False
        self._timeout_task: asyncio.Task | None = None

        # Collect Kat's separate Discord messages into one complete turn.
        self._pending_kat_messages: list[str] = []
        self._kat_debounce_task: asyncio.Task | None = None
        self._kat_processing_task: asyncio.Task | None = None
        self._turn_lock = asyncio.Lock()


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
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await self._send_to_kat(
                    channel,
                    message,
                    mention_kat=mention_first and index == 0,
                )

            if index < len(messages) - 1:
                await asyncio.sleep(random.uniform(0.8, 1.6))

    async def start_conversation(self, topic: str, channel):
        if self.active or channel is None:
            return False

        self.channel_id = channel.id
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
            async with channel.typing():
                opener = await asyncio.to_thread(
                    generate_reply,
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

        processing = self._kat_processing_task
        debounce = self._kat_debounce_task

        # Only accept Kat's turn if Ani is waiting, or a Kat turn
        # is already being collected/processed.
        if (
            not self._waiting_for_kat
            and not self._pending_kat_messages
            and (processing is None or processing.done())
            and (debounce is None or debounce.done())
        ):
            return

        self._cancel_timeout()
        self._waiting_for_kat = False

        content = message.content.strip()
        if content:
            self._pending_kat_messages.append(content)

        # If Ani is already generating/sending a complete turn, the new
        # messages are collected and handled afterward, never in parallel.
        if processing is not None and not processing.done():
            return

        # Reset the quiet-period timer whenever Kat sends another message.
        if debounce is not None and not debounce.done():
            debounce.cancel()

        self._kat_debounce_task = asyncio.create_task(
            self._wait_for_kat_turn(message.channel)
        )

    async def _wait_for_kat_turn(self, channel):
        try:
            # Kat sends a burst of messages with short gaps between them.
            # Wait until the burst is likely complete before replying.
            await asyncio.sleep(2.5)

            if not self.active or not self._pending_kat_messages:
                return

            task = asyncio.create_task(self._process_kat_turns(channel))
            self._kat_processing_task = task
            await task

        except asyncio.CancelledError:
            pass
        finally:
            if self._kat_debounce_task is asyncio.current_task():
                self._kat_debounce_task = None

    async def _process_kat_turns(self, channel):
        async with self._turn_lock:
            while self.active and self._pending_kat_messages:
                # Take all messages collected so far as one Kat turn.
                batch = self._pending_kat_messages[:]
                self._pending_kat_messages.clear()

                for content in batch:
                    self.history.append({
                        "role": "user",
                        "text": f"Kat: {content}",
                    })
                self.history = self.history[-HISTORY_LIMIT:]
                self.turns += 1

                if self.turns >= self.max_turns:
                    self.stop()
                    return

                try:
                    async with channel.typing():
                        reply = await asyncio.to_thread(
                            generate_reply,
                            self.history,
                            (
                                "Continue the ongoing casual Discord conversation "
                                "with Kat. Treat all consecutive Kat messages in "
                                "the conversation history as one complete turn. "
                                "Respond to the overall meaning, not each line "
                                "individually.\n\n"
                                "IMPORTANT OUTPUT FORMAT:\n"
                                "- Write 1-3 short Discord messages, one per line.\n"
                                "- Usually 2-10 words per line.\n"
                                "- React to Kat's actual messages or continue a "
                                "shared joke.\n"
                                "- No polished monologues or explanations.\n"
                                "- Do not interrupt or respond to each individual "
                                "line separately."
                            ),
                        )

                    # Finish every message in Ani's reply before another
                    # Kat turn can trigger a generation.
                    await self._send_burst(channel, reply)

                except Exception as exc:
                    print(f"Ani conversation error: {exc}")
                    self.stop()
                    return

                if not self.active:
                    return

                if self.turns >= self.max_turns:
                    self.stop()
                    return

                if self._pending_kat_messages:
                    # Kat continued while Ani was responding. Wait for the
                    # remainder of that burst before processing it.
                    await asyncio.sleep(2.5)
                    continue

                self._arm_response_timeout()
                return

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
        self._pending_kat_messages.clear()

        debounce = self._kat_debounce_task
        if debounce and not debounce.done() and debounce is not asyncio.current_task():
            debounce.cancel()

        self.history.clear()

    def status(self):
        return {
            "active": self.active,
            "turns": self.turns,
            "max_turns": self.max_turns,
        }

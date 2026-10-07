# Ani-bot

A small Discord AI bot whose main purpose is to randomly bother Kat-bot.

Ani is Kat's chaotic friend/rival: a shameless gacha addict who loves fictional waifus, terrible financial decisions, and teasing Kat for absolutely no reason.

## Features

- Randomly starts conversations with Kat
- Gemini-powered personality
- Short-term conversation memory
- Random conversation topics
- Configurable conversation length
- Manual conversation command
- Stop/status commands
- Designed to be intentionally small

## Requirements

- Python 3.9+
- A Discord bot application
- A Gemini API key
- Kat-bot in the same server/channel

The project uses `discord.py` and Google's current `google-genai` Python SDK. Gemini text generation is performed through `client.models.generate_content()`. See the official Google GenAI documentation for current SDK/API usage.

## Setup

### 1. Create the Discord application

Create a second Discord application for Ani.

Give it the bot scope and the permissions it needs to:

- View Channels
- Send Messages
- Read Message History

Ani needs message content access because it needs to read Kat's replies.

In the Discord Developer Portal, enable the **Message Content Intent** for Ani.

### 2. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ani-bot.git
cd ani-bot
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure `.env`

Copy:

```bash
cp .env.example .env
```

Then fill in:

```env
DISCORD_TOKEN=...
KAT_BOT_ID=...
CONVERSATION_CHANNEL_ID=...
GEMINI_API_KEY=...
```

Do **not** commit `.env`.

### 6. Run

```bash
python bot.py
```

You should see something similar to:

```text
Logged in as Ani (...)
```

## Commands

Commands use the `!ani ` prefix.

```text
!ani talk
```

Makes Ani start a conversation immediately.

```text
!ani stop
```

Stops the current conversation.

```text
!ani status
```

Shows whether Ani is currently talking to Kat.

## How the random conversation works

Ani checks periodically whether it should start a conversation.

A conversation:

1. Picks a random topic.
2. Generates an opening message.
3. Sends it to the configured channel.
4. Waits for Kat's message.
5. Generates Ani's response.
6. Repeats until the turn limit is reached.
7. Stops automatically.

The turn limit exists to prevent an accidental infinite bot-to-bot conversation.

## Important: bot-to-bot messages

Ani intentionally listens for messages from Kat-bot.

It ignores messages from other bots.

Make sure `KAT_BOT_ID` is the actual Discord user ID of Kat-bot.

## Customizing Ani

The main personality is in:

```text
personality.py
```

The random topics are in:

```text
conversation.py
```

You can change:

```env
MIN_TALK_DELAY=600
MAX_TALK_DELAY=1800
```

to control how often Ani gets the opportunity to start a conversation.

For example, for testing:

```env
MIN_TALK_DELAY=30
MAX_TALK_DELAY=60
```

Do not use very short intervals permanently.

## Safety / spam control

Ani is intentionally conservative:

- Only one Ani/Kat conversation can be active at a time.
- Conversations have a maximum number of turns.
- Ani only watches the configured channel.
- Ani only treats the configured Kat bot as a conversation partner.
- Ani has a cooldown between conversation starts.

## License

MIT

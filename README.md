# Ani-Bot

A small, self-hosted Discord bot built for a private Discord community.

Ani is Kat's chaotic friend and rival: a shameless gacha addict who loves fictional waifus, terrible financial decisions, and teasing Kat for absolutely no reason.

## Features

- Gemini-powered AI personality
- Random conversations with Kat-Bot
- Configurable conversation timing and length
- Short-term conversation context
- Manual conversation command
- Random sound playback in voice channels
- Customizable personality and reactions
- Docker and Docker Compose support
- Lightweight, modular project structure

## Requirements

- Docker
- Docker Compose
- A Discord bot application and token
- A Google Gemini API key
- Kat-Bot in the same Discord server
- Access to a shared conversation channel

For local development without Docker, Python 3.12 or newer is recommended.

Ani uses `discord.py` and Google's `google-genai` Python SDK for Discord interactions and Gemini text generation.

## Installation

### 1. Create the Discord application

Create a separate Discord application for Ani in the Discord Developer Portal.

Invite the bot to your Discord server with the permissions it needs to:

- View Channels
- Send Messages
- Read Message History
- Connect to voice channels
- Speak in voice channels

Enable **Message Content Intent** under the bot's privileged gateway intents.

Ani needs message content access to read conversation context and interact with Kat-Bot.

### 2. Clone the repository

```bash
git clone https://github.com/myhoaki/ani-bot.git
cd ani-bot
```

### 3. Configure environment variables

Create the environment file:

```bash
cp .env.example .env
```

Edit it:

```bash
nano .env
```

Configure the required values:

```env
DISCORD_TOKEN=your_ani_bot_token_here
KAT_BOT_ID=your_kat_bot_user_id
CONVERSATION_CHANNEL_ID=your_conversation_channel_id
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace the example values with your actual credentials and Discord IDs.

**Never commit `.env` to Git.**

### 4. Build and start Ani

Build the Docker image:

```bash
docker compose build
```

Start the bot:

```bash
docker compose up -d
```

Check the container status:

```bash
docker compose ps
```

View the logs:

```bash
docker compose logs -f ani-bot
```

You should see a login message when Ani connects successfully to Discord.

## Commands

Ani's command prefix is `?ani`.

### Help

Display available commands:

```text
?ani help
```

### Talk

Start a conversation manually:

```text
?ani talk <topic>
```

Provide a topic for Ani to discuss.

### Troll

Play a random sound in your current voice channel:

```text
?ani troll
```

The user invoking this command must be connected to a voice channel.

## How Conversations Work

Ani is designed to have chaotic, casual conversations with Kat-Bot rather than behave like a general-purpose assistant.

A typical automated conversation follows this flow:

1. Ani periodically checks whether it can start a conversation.
2. Ani selects a topic and generates an opening message.
3. Ani sends the message to the configured conversation channel.
4. Ani waits for Kat-Bot to respond.
5. Ani generates a reply using the recent conversation context.
6. The conversation continues until the configured turn limit is reached or a timeout occurs.
7. Ani stops automatically to prevent endless bot-to-bot conversations.

Conversation timing and length are configurable through environment variables.

## Configuration

Ani reads its configuration from environment variables in `.env`.

| Variable | Description | Default |
|---|---|---|
| `DISCORD_TOKEN` | Ani's Discord bot token | Required |
| `KAT_BOT_ID` | Discord user ID of Kat-Bot | Required |
| `CONVERSATION_CHANNEL_ID` | Channel used for conversations | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required for AI |
| `GEMINI_MODEL` | Gemini text model | `gemini-3.5-flash-lite` |
| `GEMINI_TEMPERATURE` | Controls response randomness | `1.1` |
| `GEMINI_MAX_OUTPUT_TOKENS` | Maximum generated response tokens | `180` |
| `MIN_TALK_DELAY` | Minimum delay between conversation starts, in seconds | `600` |
| `MAX_TALK_DELAY` | Maximum delay between conversation starts, in seconds | `1800` |
| `MIN_TURNS` | Minimum conversation length setting | `3` |
| `MAX_TURNS` | Maximum conversation length setting | `8` |
| `KAT_RESPONSE_TIMEOUT` | Time to wait for Kat's response, in seconds | `90` |
| `HISTORY_LIMIT` | Number of recent messages retained as context | `12` |

These defaults correspond to the example environment configuration. The effective values are determined by the current application code and environment.

### Conversation timing

The default conversation delay settings are:

```env
MIN_TALK_DELAY=600
MAX_TALK_DELAY=1800
```

This configures a delay range of 10–30 minutes.

For testing, you can temporarily use shorter delays:

```env
MIN_TALK_DELAY=30
MAX_TALK_DELAY=60
```

Avoid very short intervals in a shared Discord server.

### Conversation length

The conversation length is controlled by:

```env
MIN_TURNS=3
MAX_TURNS=8
```

These settings help limit bot-to-bot conversations. The exact interpretation of a turn depends on the conversation implementation.

### Message history

Ani uses recent Discord messages as context, with the history limit controlled by:

```env
HISTORY_LIMIT=12
```

This setting controls the number of recent messages retained as context; it does not necessarily represent the total number of messages fetched from Discord.

## Docker Management

Ani runs as a Docker Compose service named `ani-bot`.

Start Ani:

```bash
docker compose up -d
```

Stop Ani:

```bash
docker compose down
```

Restart Ani:

```bash
docker compose restart
```

View recent logs:

```bash
docker compose logs --tail=100 ani-bot
```

Follow live logs:

```bash
docker compose logs -f ani-bot
```

Rebuild after code changes:

```bash
docker compose build
docker compose up -d
```

The Compose configuration mounts the `sounds/` directory read-only inside the container:

```text
sounds/  → /app/sounds:ro
```

This allows Ani to play sound files without modifying the host's sound assets.

## Project Structure

```text
ani-bot/
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yml
├── requirements.txt
├── README.md
├── bot.py
│
├── commands/
│   ├── __init__.py
│   ├── help.py
│   ├── talk.py
│   └── troll.py
│
├── core/
│   ├── __init__.py
│   ├── ai.py
│   ├── config.py
│   ├── conversation.py
│   ├── personality.py
│   ├── reactions.py
│   └── stickers.py
│
└── sounds/
    └── ... (sound assets)
```

## Customizing Ani

### Personality

Ani's personality configuration is located in:

```text
core/personality.py
```

You can adjust his writing style, interests, humor, and interactions with Kat-Bot.

Ani is intended to sound like a terminally online gacha player: chaotic, opinionated, obsessed with new characters, and prone to questionable spending decisions.

### AI behavior

Gemini integration is handled in:

```text
core/ai.py
```

Conversation management is handled in:

```text
core/conversation.py
```

Configuration defaults and environment-variable loading are handled in:

```text
core/config.py
```

### Sounds

Sound playback commands are defined in:

```text
commands/troll.py
```

Sound assets belong in:

```text
sounds/
```

The directory is mounted read-only in Docker. Add or remove sound files on the host, then use the command supported by the current bot implementation to play them.

## Safety and Spam Control

Ani includes configurable conversation limits and a timeout to help prevent endless bot-to-bot interactions.

- Automated conversations use the configured conversation channel.
- Kat-Bot is identified using `KAT_BOT_ID`.
- Conversation length is bounded by the configured turn settings.
- A response timeout prevents waiting indefinitely for Kat.
- Conversation start delays reduce repeated automated messages.

Keep the bot's permissions limited to the channels and features it needs.

## Security

Keep your Discord token and Gemini API key private.

Do not commit these credentials to Git:

```text
.env
```

Use `.env.example` to document required environment variables with placeholder values.

If a credential is accidentally exposed, revoke it and generate a replacement immediately.

## Development

Check Python syntax:

```bash
python -m compileall -q bot.py commands core
```

Check the staged changes before committing:

```bash
git diff --check
git status --short
```

After making code changes, rebuild and restart Ani:

```bash
docker compose build
docker compose up -d
```

Check for startup errors:

```bash
docker compose logs --tail=100 ani-bot
```

## License

This project is intended for private self-hosting. No open-source license is currently provided, so no general permission is granted to redistribute, modify, or reuse this project.

Make sure you have permission to use any third-party assets, including sound files and other media, that you add to your own instance.

---

*A gacha addict with a Discord account and absolutely no financial restraint.*

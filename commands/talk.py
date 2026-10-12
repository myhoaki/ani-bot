from discord.ext import commands


def create_talk_command(conversation):
    @commands.command(name="talk")
    async def talk_command(ctx: commands.Context, *, topics: str):
        """Make Ani start a conversation about your chosen topic."""

        topics = topics.strip()
        if not topics:
            await ctx.send(
                "Give me a topic, you fcking memer. "
                "Example: `?ani talk gacha games`"
            )
            return

        started = await conversation.start_conversation(
            topic=topics,
            channel=ctx.channel,
        )
        if not started:
            await ctx.send("I'm already talking to Kat. Let us cook.")

    return talk_command

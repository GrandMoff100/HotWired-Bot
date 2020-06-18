import random

from discord import Color, Embed
from discord.ext.commands import Bot, Cog, Context, command
from .utils import constants


class Games(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @command()
    async def roll(self, ctx: Context, min_limit: int = 1, max_limit: int = 10) -> None:
        """Roll a random number."""
        if max_limit - min_limit > 2:
            number = random.randint(min_limit, max_limit)
            embed = Embed(title="Random Roll", color=Color.blue(), description=f"The random number is: {number}",)
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Random Roll", color=Color.red(), description="Please specify numbers with difference of **at least 2**",)
            await ctx.send(embed=embed)

    @command(aliases=["8ball"])
    async def ball8(self, ctx: Context, *, question: str) -> None:
        """Play 8ball."""
        reply_type = random.randint(1, 3)

        if reply_type == 1:
            answer = random.choice(constants.POSITIVE_REPLIES)
        elif reply_type == 2:
            answer = random.choice(constants.NEGATIVE_REPLIES)
        elif reply_type == 3:
            answer = random.choice(constants.ERROR_REPLIES)

        embed = Embed(title="Magic 8-ball", color=Color.blurple(),)
        embed.add_field(name="Question", value=question)
        embed.add_field(name="Answer", value=answer)


def setup(bot: Bot) -> None:
    bot.add_cog(Games(bot))

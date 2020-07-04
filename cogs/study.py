import re
import textwrap
import typing as t

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext.commands import Bot, Cog, Context, command
from discord import Embed, Color

from utils.mathscrape import get_math_results
from utils.wolframscrape import get_wolfram_data

from .urbandict_utils.urbandictpages import UrbanDictionaryPages


class Study(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @command()
    async def calc(self, ctx: Context, *, equation: str) -> None:
        """Calculate an equation"""
        res = get_math_results(equation)

        if res.lower() == "invalid equation":
            emb = discord.Embed(title="ERROR!", description="❌ Invalid Equation Specified, Please Recheck the Equation", color=discord.Color.red())
            emb.set_footer(text=f"Invoked by {str(ctx.message.author)}")

            await ctx.send(embed=emb)

        else:
            embed = discord.Embed(title="Equation Results")
            embed.add_field(name="**❯❯ Question**", value=equation, inline=False)
            embed.add_field(name="**❯❯ Result**", value=res, inline=False)
            embed.set_footer(text=f"Invoked by {str(ctx.message.author)}")

            await ctx.send(embed=embed)

    @command(aliases=["wq", "wolframquestion", "wquestion"])
    async def ask_question(self, ctx: Context, conversation_mode: str = "true", *, question: str) -> None:
        """Ask the answer of an question"""
        data = get_wolfram_data(question, conversation_mode)

        embed = discord.Embed(title="Question Results")
        embed.add_field(name="**❯❯ Question**", value=question, inline=False)
        embed.add_field(name="**❯❯ Result**", value=data, inline=False)
        embed.set_footer(text=f"Invoked by {str(ctx.message.author)}")

        await ctx.send(embed=embed)

    @command(aliases=["dict"])
    async def urban(self, ctx: Context, *, word: str) -> None:
        """Searches urban dictionary."""
        url = "http://api.urbandictionary.com/v0/define"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"term": word}) as resp:
                if resp.status != 200:
                    await ctx.send(f"An error occurred: {resp.status} {resp.reason}.")
                    embed = discord.Embed(
                        title="Response Error Occured!",
                        description=textwrap.dedent(
                            f"""
                            Status Code: {resp.status}
                            Reason: {resp.reason}
                            """
                        ),
                        color=discord.Color.red(),
                    )
                    await ctx.send(embed=embed)
                    return

                js = await resp.json()
                data = js.get("list", [])
                if not data:
                    embed = discord.Embed(description="No results found, sorry.", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

        pages = UrbanDictionaryPages(ctx, data)
        await pages.paginate()

    async def _get_soup_object(self, url: str) -> t.Union[None, BeautifulSoup]:
        try:
            async with self.session.request("GET", url) as response:
                return BeautifulSoup(await response.text(), "html.parser")
        except Exception:
            return None

    @command()
    async def antonym(self, ctx: Context, *, word: str) -> None:
        """Displays antonyms for a given word."""
        search_msg = await ctx.send("Searching...")
        search_term = word.split(" ", 1)[0]
        result = await self._antonym(ctx, search_term)
        if not result:
            return await search_msg.edit(content="This word is not in the dictionary.")

        result_text = "*, *".join(result)
        await search_msg.edit(content=f"Antonyms for **{search_term}**: *{result_text}*")

    async def _antonym(self, ctx: Context, word: str) -> list:
        data = await self._get_soup_object(f"http://www.thesaurus.com/browse/{word}")
        if not data:
            return await ctx.send("Error fetching data.")
        section = data.find_all("ul", {"class": "css-1ytlws2 et6tpn80"})
        try:
            section[1]
        except IndexError:
            return
        spans = section[1].findAll("li")
        antonyms = [span.text for span in spans[:50]]
        return antonyms

    @command()
    async def define(self, ctx: Context, *, word: str) -> None:
        """Displays definitions of a given word."""
        search_msg = await ctx.send("Searching...")
        search_term = word.split(" ", 1)[0]
        result = await self._definition(ctx, search_term)
        str_buffer = ""
        if not result:
            return await search_msg.edit(content="This word is not in the dictionary.")
        for key in result:
            str_buffer += f"\n**{key}**: \n"
            counter = 1
            j = False
            for val in result[key]:
                if val.startswith("("):
                    str_buffer += f"{str(counter)}. *{val})* "
                    counter += 1
                    j = True
                else:
                    if j:
                        str_buffer += f"{val}\n"
                        j = False
                    else:
                        str_buffer += f"{str(counter)}. {val}\n"
                        counter += 1
        await search_msg.edit(content=str_buffer)

    async def _definition(self, ctx: Context, word: str) -> dict:
        data = await self._get_soup_object(f"http://wordnetweb.princeton.edu/perl/webwn?s={word}")
        if not data:
            return await ctx.send("Error fetching data.")
        types = data.findAll("h3")
        lists = data.findAll("ul")
        out = {}
        if not lists:
            return
        for a in types:
            reg = str(lists[types.index(a)])
            meanings = []
            for x in re.findall(r">\s\((.*?)\)\s<", reg):
                if "often followed by" in x:
                    pass
                elif len(x) > 5 or " " in str(x):
                    meanings.append(x)
            name = a.text
            out[name] = meanings
        return out

    async def _synonym(self, ctx: Context, word: str) -> list:
        data = await self._get_soup_object(f"http://www.thesaurus.com/browse/{word}")
        if not data:
            return await ctx.send("Error fetching data.")
        section = data.find_all("ul", {"class": "css-1ytlws2 et6tpn80"})
        try:
            section[1]
        except IndexError:
            return
        spans = section[0].findAll("li")
        synonyms = [span.text for span in spans[:50]]
        return synonyms

    @command()
    async def synonym(self, ctx: Context, *, word: str) -> None:
        """Displays synonyms for a given word."""
        search_msg = await ctx.send("Searching...")
        search_term = word.split(" ", 1)[0]
        result = await self._synonym(ctx, search_term)
        if not result:
            return await search_msg.edit(content="This word is not in the dictionary.")

        result_text = "*, *".join(result)
        await search_msg.edit(content=f"Synonyms for **{search_term}**: *{result_text}*")

    base_url = "https://en.wikipedia.org/w/api.php"
    headers = {"user-agent": "HotWired-Bot"}
    footer_icon = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Wikimedia-logo.png"
        "/600px-Wikimedia-logo.png"
    )

    @command(aliases=["wiki"])
    async def wikipedia(self, ctx: Context, *, query: str) -> None:
        """Get information from Wikipedia."""
        payload = {}
        payload["action"] = "query"
        payload["titles"] = query.replace(" ", "_")
        payload["format"] = "json"
        payload["formatversion"] = "2"  # Cleaner json results
        payload["prop"] = "extracts"  # Include extract in returned results
        payload["exintro"] = "1"  # Only return summary paragraph(s) before main content
        payload["redirects"] = "1"  # Follow redirects
        payload["explaintext"] = "1"  # Make sure it's plaintext (not HTML)

        conn = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(
                self.base_url, params=payload, headers=self.headers
            ) as res:
                result = await res.json()

        try:
            # Get the last page. Usually this is the only page.
            for page in result["query"]["pages"]:
                title = page["title"]
                description = page["extract"].strip().replace("\n", "\n\n")
                url = "https://en.wikipedia.org/wiki/{}".format(title.replace(" ", "_"))

            if len(description) > 1500:
                description = description[:1500].strip()
                description += "... [(read more)]({})".format(url)

            embed = discord.Embed(
                title=f"Wikipedia: {title}",
                description=u"\u2063\n{}\n\u2063".format(description),
                color=discord.Color.blue(),
                url=url
            )
            embed.set_footer(
                text="Wikipedia", icon_url=self.footer_icon
            )
            await ctx.send(embed=embed)

        except KeyError:
            await ctx.send(
                embed=Embed(
                    description=f"I'm sorry, I couldn't find \"{query}\" on Wikipedia",
                    color=Color.red()
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=Embed(
                    description=f"I'm not allowed to do embeds here!\n{url}",
                    color=Color.gold()
                )
            )


def setup(bot: Bot) -> None:
    bot.add_cog(Study(bot))

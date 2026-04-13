#✅ Fixed + improved version (drop-in)
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import string   # ✅ you forgot this

intents = discord.Intents.default()
intents.guilds = True
intents.reactions = True

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL = int(os.getenv("CHANNEL_ID"))

bot = commands.Bot(command_prefix="!", intents=intents)


def stripped(text):
    text = text.replace("\n", "")
    for punct in string.punctuation:
        text = text.replace(punct, "")
    text = text.replace(" ", "")
    return text.lower()


def find_title(bookname, writer):
    query = bookname.replace(" ", "+")
    url = f"https://www.goodreads.com/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    page = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(page.text, "html.parser")

    rows = soup.find_all("tr")

    for row in rows:
        title = row.find("a", class_="bookTitle")
        author = row.find("a", class_="authorName")

        if title and author:
            if (
                stripped(title.text) == stripped(bookname)
                and stripped(author.text) == stripped(writer)
            ):
                return title["href"]

    return None

def open_page(bookname, writer):
    link = find_title(bookname, writer)

    if not link:
        return None

    url = f"https://www.goodreads.com{link}"
    headers = {"User-Agent": "Mozilla/5.0"}

    page = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(page.text, "html.parser")

    # TITLE
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown"

    # AUTHOR
    author_tag = soup.find("span", class_="ContributorLink__name")
    author = author_tag.text.strip() if author_tag else "Unknown"

    # RATING
    rating_tag = soup.find("div", class_="RatingStatistics__rating")
    rating = rating_tag.text.strip() if rating_tag else "N/A"

    # COVER
    cover_tag = soup.find("img", class_="ResponsiveImage")
    cover = cover_tag["src"] if cover_tag else None

    # 🔥 DESCRIPTION (new)
    desc = None

    # Try modern Goodreads layout
    desc_tag = soup.find("span", class_="Formatted")
    if desc_tag:
        desc = desc_tag.text.strip()

    # Fallback (older layout)
    if not desc:
        desc_tag = soup.find("div", id="description")
        if desc_tag:
            spans = desc_tag.find_all("span")
            if spans:
                desc = spans[-1].text.strip()

    # Final fallback
    if not desc:
        desc = "No description available."

    # Limit length (Discord embeds have limits)
    desc = desc[:400] + "..." if len(desc) > 400 else desc

    return {
        "title": title,
        "author": author,
        "url": url,
        "cover": cover,
        "rating": rating,
        "desc": desc,   # ✅ now included
    }

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()


# ✅ UPDATED COMMAND
@bot.tree.command(name="suggest", description="Suggest a book")
@app_commands.describe(
    book="Name of the book",
    author="Name of the author"
)
async def suggest(interaction: discord.Interaction, book: str, author: str):

    await interaction.response.defer(ephemeral=True)

    data = open_page(book, author)

    if not data:
        await interaction.followup.send("Couldn't find this book on Goodreads")
        return

    embed = discord.Embed(
        title=data["title"],
        url=data["url"],
        description=(
            f"Suggested by {interaction.user.mention}\n"
            f"**{data['author']}**\n"
            f"⭐ *Rating:* {data['rating']}"
        ),
        color=0x6B5B95
    )

    if data["cover"]:
        embed.set_thumbnail(url=data["cover"])

    channel = bot.get_channel(CHANNEL)
    msg = await channel.send(embed=embed)

    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await interaction.followup.send("Suggestion added!", ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)

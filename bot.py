DISCORD_TOKEN = "ODMwNjY2MTYyNTk2NDc5MDM2.GdZmn2.9gZ25aSiF521-UKuaQQIVktBeiNFF58k77l-k4"
SUGGESTION_CHANNEL_ID = 1234567890

import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.guilds = True
intents.reactions = True

load_dotenv()
client = discord.Client(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
SUGGESTION_CHANNEL_ID = int(os.getenv("SUGGESTION_CHANNEL_ID"))

bot = command.Bot(command_prefix="/", intents=intents)

def search_gr(bookname):
    query = f"{book_name} site:goodreads.com"
    url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    headers = {"User-Agent":"Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    link = None
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and "goodreads.com/book" in href:
           link = href.split("&")[0].replace("/url?q=", "")
           break

    if not link:
        return None

    gr_page = requests.get(link, headers=headers)
    gr_soup = BeautifulSoup(gr_page.text, "html.parser") 

    title = gr_soup.find("h1", {"id": "bookTitle"})
    title = title.get_text(stripe=True) if title else book_name

    cover = gr_soup.find("img", {"id": "coverImage"})
    cover = cover["src"] if cover else None

    rating = gr_soup.find("span", itemprop="ratingValue")
    rating = rating.get_text(strip=True) if rating else "?"

    return {
        "title": title,
        "url": link,
        "cover": cover,
        "rating": rating
    }

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

@bot.tree.command(name="suggest", description="Suggest a book")
@app_commands.describe(book="Name of the book")
async def suggest(interaction: discord.Interaction, book:str):
    await interaction.response.defer(ephemeral=True)

    data = search_gr(book)
    if not data:
        await interaction.followup.send("Couldn't find this book on Goodreads")
        return
    
    embed = discord.Embed(
        title = data["title"],
        url = data["url"],
        description = f"Suggested by {interaction.user.mention}\n :star: Rating: {data["rating"]}",
        color = 0x6B5B95
    )
    if data["cover"]:
        embed.set_thumbnail(url=data["cover"])

    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    msg = await channel.send(embed=embed)

    await msg.add_reaction(":thumbsup:")
    await msg.add_reaction(":thumbsdown:")

    await interaction.followup.send("Suggestion added!", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)

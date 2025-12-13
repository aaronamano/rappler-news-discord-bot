# bot.py
import os
import asyncio
import feedparser
import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Choose a Rappler RSS feed (change as needed)
RAPPLER_FEED_URL = "https://www.rappler.com/feed"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Keep track of IDs/links already posted to avoid duplicates
posted_ids = set()

async def fetch_and_parse_feed():
    """Fetch Rappler RSS and return new entries not yet posted."""
    feed = feedparser.parse(RAPPLER_FEED_URL)
    new_items = []

    for entry in feed.entries:
        # Prefer a stable identifier; fall back to link
        entry_id = getattr(entry, "id", None) or entry.link
        if entry_id not in posted_ids:
            posted_ids.add(entry_id)
            new_items.append(entry)

    return list(reversed(new_items))  # oldest first

@tasks.loop(hour=1)  # adjust frequency as needed
async def poll_rappler_feed():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check CHANNEL_ID.")
        return

    try:
        new_entries = await fetch_and_parse_feed()
    except Exception as e:
        print(f"Error fetching/parsing feed: {e}")
        return

    for entry in new_entries:
        link = entry.link

        # Keep messages short to avoid clutter
        content = f"{link}"
        await channel.send(content)
        await asyncio.sleep(10)  # small delay to avoid rate limits

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    if not poll_rappler_feed.is_running():
        poll_rappler_feed.start()

if __name__ == "__main__":
    if not DISCORD_TOKEN or CHANNEL_ID == 0:
        raise SystemExit("Set DISCORD_TOKEN and CHANNEL_ID in your environment or .env file.")
    client.run(DISCORD_TOKEN)

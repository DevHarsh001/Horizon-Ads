# This python file will automatically generate bals.txt,log.txt and serverinfo.json files to keep track of progress
# Requires Discord Module !!
# Paste Your Own Token in ln 176, col 10
# Credit :- Horizon Digitals
# Use of ai is done to comment things.

import discord
import logging
import json
import os
from discord.ext import commands, tasks
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Define bot prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# File paths
SERVER_INFO_FILE = "serverinfo.json"
BALANCE_FILE = "bals.json"

# Load JSON data
def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as file:
        return json.load(file)

# Save JSON data
def save_json(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Load stored data
server_data = load_json(SERVER_INFO_FILE)
balances = load_json(BALANCE_FILE)

# Create embed
def create_embed(message):
    embed = discord.Embed(description=message, color=discord.Color.blue())
    embed.set_footer(text="Horizon Digitals")
    return embed

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    logging.info(f"Bot started as {bot.user}")
    await fetch_all_server_data()  # Fetch data instantly
    update_server_info.start()  # Continue updating every 3 minutes

# Fetch all server data instantly
async def fetch_all_server_data():
    global server_data
    for guild in bot.guilds:
        total_members = guild.member_count
        avg_online_members = sum(1 for m in guild.members if m.status != discord.Status.offline) / max(1, total_members)
        total_messages = server_data.get(str(guild.id), {}).get("total_messages", 0)
        messages_last_24h = server_data.get(str(guild.id), {}).get("messages_last_24h", 0)
        server_owner = guild.owner.name
        invite_link = "N/A"

        if guild.me.guild_permissions.create_instant_invite:
            try:
                invite = await guild.text_channels[0].create_invite(max_age=0, max_uses=0)
                invite_link = invite.url
            except:
                pass

        server_data[str(guild.id)] = {
            "name": guild.name,
            "total_members": total_members,
            "avg_online_members": round(avg_online_members, 2),
            "total_messages": total_messages,
            "messages_last_24h": messages_last_24h,
            "server_owner": server_owner,
            "server_link": invite_link,
            "ignored_channels": server_data.get(str(guild.id), {}).get("ignored_channels", [])
        }

    save_json(SERVER_INFO_FILE, server_data)
    logging.info("Server data updated instantly.")

# Update server info every 3 minutes
@tasks.loop(minutes=3)
async def update_server_info():
    await fetch_all_server_data()

# Send message to all servers
@bot.command()
async def send(ctx, code: str, *, message: str):
    if code != "9292":
        await ctx.send("Invalid code.")
        return

    embed = create_embed(message)
    
    for guild in bot.guilds:
        sent = False  

        for channel in guild.text_channels:
            ignored_channels = server_data.get(str(guild.id), {}).get("ignored_channels", [])
            if channel.id in ignored_channels:
                continue  
            
            try:
                await channel.send(embed=embed)
                sent = True
                logging.info(f"Sent message to {channel.name} in {guild.name}: {message}")
                break  # Send to only one channel per server
            except Exception as e:
                logging.warning(f"Could not send to {channel.name} in {guild.name}: {e}")

        if sent:
            owner_id = str(guild.owner.id)
            balances[owner_id] = balances.get(owner_id, 0) + 0.01

    save_json(BALANCE_FILE, balances)
    logging.info("Message sent to all servers.")
    await ctx.send("Message sent successfully.")

# Remove default help command
bot.remove_command("help")

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help",
        description="This bot sends advertisements in your Discord server, allowing you to earn free Bitcoin, Litecoin, or redeem codes to increase your balance.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# Check balance
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    balance = balances.get(user_id, 0)
    await ctx.send(f"Your balance is: ${balance:.2f}")
    logging.info(f"User {ctx.author} checked balance: ${balance:.2f}")

# Ignore a channel (max 5 per server)
@bot.command()
async def ignorechannel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)
    
    if guild_id not in server_data:
        server_data[guild_id] = {"ignored_channels": []}

    if channel.id in server_data[guild_id]["ignored_channels"]:
        await ctx.send(f"{channel.name} is already ignored.")
        return

    if len(server_data[guild_id]["ignored_channels"]) >= 5:
        await ctx.send("You can only ignore up to 5 channels.")
        return

    server_data[guild_id]["ignored_channels"].append(channel.id)
    save_json(SERVER_INFO_FILE, server_data)
    logging.info(f"Channel {channel.name} ignored in {ctx.guild.name}")
    await ctx.send(f"Ignoring channel: {channel.name}")

# Unignore a channel
@bot.command()
async def unignorechannel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)

    if guild_id in server_data and channel.id in server_data[guild_id]["ignored_channels"]:
        server_data[guild_id]["ignored_channels"].remove(channel.id)
        save_json(SERVER_INFO_FILE, server_data)
        logging.info(f"Channel {channel.name} unignored in {ctx.guild.name}")
        await ctx.send(f"Unignored channel: {channel.name}")
    else:
        await ctx.send(f"{channel.name} is not ignored.")

bot.run('TOKEN')

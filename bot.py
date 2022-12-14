import os

from dotenv import load_dotenv

import nextcord
from nextcord.ext import commands
from nextcord import Interaction

# Load data from .env and check if the variables are empty
load_dotenv()
bot_token=os.getenv("BOT_TOKEN")
command_prefix=os.getenv("PREFIX")
owner_id=os.getenv("OWNER_ID")

if bot_token == "":
    print("No bot token has been provided. Shutting down...")
    print("Go into the \".env\" file and paste your bot's token after \"BOT_TOKEN=\"")
    exit()

if command_prefix == "":
    print("No command prefix has been provided. It is recommended that you provide one. Slash commands can be still be used.")
    print("Go into the \".env\" file and paste your desired command prefix after \"PREFIX=\"")

if owner_id == "":
    print("No Discord owner ID has been provided. It is recommended that you provide one to get bot updates straight to your DMs.")
    print("Go into the \".env\" file and paste your desired command prefix after \"OWNER_ID=\"")

# Enable all intents and start configuring the bot
intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix, description="Simple Discord bot", intents=intents, case_insensitive=True)

# Tell the console when bot is ready, as well as the owner through Discord DMs
@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    if owner_id != "":
        user = await bot.fetch_user(owner_id)
        await user.send(f"{bot.user} has logged in.")

# Welcome new members to the server through the system messages channel
@bot.event
async def on_member_join(ctx):
    if ctx.guild.system_channel:
        await ctx.guild.system_channel.send(f"Welcome to the server, {ctx.author.mention}!")

# Send farewells to members leaving the server through the system messages channel
@bot.event
async def on_member_remove(ctx):
    if ctx.guild.system_channel:
        await ctx.guild.system_channel.send(f"Goodbye, {ctx.author.mention}.")

# Simple slash command to make sure the bot is responding.
@bot.slash_command(name="ping", description="Responds with pong")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!")

# Load cog files
for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:len(file) - 3]}")
        print(f"Loaded {file[:len(file) - 3]} cog!")

# Bot is good to start running!
bot.run(bot_token)

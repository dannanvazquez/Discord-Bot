import datetime
import os
import sys

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

owner_id=os.getenv("OWNER_ID")

class BotOwner(commands.Cog):
    # Initialize this bot class as the singleton
    def __init__(self, bot):
            self.bot = bot

    # Reload command reloads all cog extenions
    @nextcord.slash_command(name="reload", description="Reloads the bot's cog extensions")
    async def reload(self, ctx):
        print("Cogs are being reloaded.")
        embed = nextcord.Embed(title="Cogs have been reloaded", description="", color=0xff00c8, timestamp=datetime.datetime.now())
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                self.bot.reload_extension(f"cogs.{file[:len(file) - 3]}")
                embed.description += f"{file[:len(file) - 3]}\n"
                print(f"{file[:len(file) - 3]} is reloaded.")
        user = await self.bot.fetch_user(os.getenv("OWNER_ID"))
        await ctx.send(embed=embed, ephemeral=True)

    # Restart command fully stops the bot and restarts the script.
    @nextcord.slash_command(name="restart", description="Restarts the bot completely from terminal")
    async def restart(self, interaction: Interaction):
        user = await self.bot.fetch_user(os.getenv("OWNER_ID"))
        await interaction.send(f"{self.bot.user} is now restarting.", ephemeral=True)
        print("The bot has been requested to restart by owner")
        os.execv(sys.executable, ['python3'] + sys.argv) # Script must be able to be ran with python3

    # Before running the commands in this cog, make sure that the sender is a bot owner as listed in .env
    @reload.before_invoke
    @restart.before_invoke
    async def check_owner(interaction: Interaction):
        if str(interaction.user.id) != owner_id:
            await interaction.send("Only the owner of this bot has permission to run this command", ephemeral=True)
            raise commands.CommandError(f"{interaction.user} tried running a BotOwner command when they are not the owner of this bot.")

# Sets up the cog
def setup(bot):
    bot.add_cog(BotOwner(bot))
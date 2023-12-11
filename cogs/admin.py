import pytz
import re

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

from datetime import datetime, timedelta

class Admin(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    # Slash command to stop the bot from playing any more music and leave the voice channel.
    @nextcord.slash_command(name="purgesince", description="Ban members who have recently joined, use format: 1s, 1m, 1h, or 1d")
    async def purgesince(self, interaction: Interaction, time: str = SlashOption(description="Time to purge for", required=True)):
        time_list = re.split('(\d+)', time)
        if time_list[2] == "s":
            time_since = datetime.now() - timedelta(seconds=int(time_list[1]))
        elif time_list[2] == "m":
            time_since = datetime.now() - timedelta(minutes=int(time_list[1]))
        elif time_list[2] == "h":
            time_since = datetime.now() - timedelta(hours=int(time_list[1]))
        elif time_list[2] == "d":
            time_since = datetime.now() - timedelta(days=int(time_list[1]))
        else:
            await interaction.send("Incorrect time format! Use: 1s, 1m, 1h, or 1d", ephemeral=True)
            raise commands.CommandError(f"Author used incorrect time format: {time}")
        
        purged_users = []
        for user in interaction.guild.members:
            if user.joined_at > pytz.UTC.localize(time_since):
                try:
                    await user.ban()
                    purged_users.append(user)
                except:
                    print(f"Tried to ban {user.name} during purgesince but failed to.")
        
        if len(purged_users) == 0:
            await interaction.send("No current member has joined since then!", ephemeral=True)
        else:
            embed = nextcord.Embed(title=f"Members that have joined {time} ago have been purged", description="", color=0xff0000)
            for user in purged_users:
                embed.description += f"{user.mention}\n"
            await interaction.response.send_message(embed = embed, ephemeral=False)
    
    #@purgesince.before_invoke
    #async def check_admin(interaction: Interaction):
    #    if not interaction.author.guild_permissions.administrator:
    #        await interaction.send("Only an admin of the server has permission to run this command", ephemeral=True)
    #        raise commands.CommandError("Author is not an admin of this server.")#

def setup(bot):
    bot.add_cog(Admin(bot))
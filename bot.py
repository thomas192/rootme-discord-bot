import asyncio
import os
import discord
from datetime import datetime
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
from rootme import get_user_data, get_new_flags, retrieve_challenge
from utils import load_from_json, write_to_json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

init_cpt = 0  # Prevents initialization from happening more than once
channel = None  # Channel the bot sends notifications to


# Creates a flag alert embed
def create_embed(username, title, difficulty, section, date, img_url) -> discord.Embed:
    description = f"  |  `{username}` flagged **{title}**\n" \
                  f"  |  difficulty: *{difficulty}*\n" \
                  f"  |  section: *{section}*\n" \
                  f"  |  date: *{date}*"
    embed = discord.Embed(title="☠️      **FLAG ALERT**      ☠️",
                          description=description)
    embed.set_thumbnail(url=img_url)
    return embed


@bot.command(name='init')
async def init(ctx):
    global channel
    global init_cpt
    if init_cpt < 1:
        channel = discord.utils.get(ctx.guild.channels, name='flgged')
        check_for_new_flags.start()
        init_cpt += 1
        await channel.send('Initialization done')
    else:
        await channel.send('I cannot be initialized more than once')


@bot.command(name='bind')
async def bind(ctx, rootme_id: str):
    print('bind()')
    discord_id = str(ctx.author.id)
    # Load dict
    u_dict = load_from_json('users.json')
    # Check if rootme_id is not already set for another user
    for user in u_dict:
        if rootme_id == u_dict[user]['rootme_id']:
            await ctx.send(f'HTB id {rootme_id} is already set for another user')
            return
    # If discord_id is already set
    if discord_id in u_dict:
        await ctx.send(f"You are already bound")
        return
    # If discord_id is not set
    else:
        # Retrieve user data
        get_user_data_non_blocking = asyncio.to_thread(get_user_data, rootme_id)
        data = await get_user_data_non_blocking
        if type(data) == dict:    # If error, data type will be list
            # Save user data
            write_to_json(f'profiles/{rootme_id}.json', data)
            # Add user to dict
            u_dict[discord_id] = {'rootme_id': rootme_id, 'avatar_url': ctx.message.author.avatar.url}
            # Update dict
            write_to_json('users.json', u_dict)
            await ctx.send(f"Your discord id is now bound to RootMe id {rootme_id}")
        else:
            await ctx.send(f"This is not a valid RootMe id")


@bot.command(name='purge')
async def purge(ctx):
    print('purge()')
    discord_id = str(ctx.author.id)
    # Load dict
    u_dict = load_from_json('users.json')
    # If id is already set
    if discord_id in u_dict:
        purged_id = u_dict[discord_id]['rootme_id']
        u_dict.pop(discord_id)  # Remove entry
        await ctx.send(f"Your discord id is no longer bound to RootMe id {purged_id}")
    # If id is not set
    else:
        await ctx.send("Your discord id is not bound to any RootMe id")
        return
    # Update dict
    write_to_json('users.json', u_dict)


@tasks.loop(minutes=10)
async def check_for_new_flags():
    print('check_for_new_flags()')
    print(datetime.now())
    # Load dict
    u_dict = load_from_json('users.json')
    # Iterate over each user
    for user in u_dict:
        rootme_id = u_dict[user]['rootme_id']
        # Retrieve list of new flags for user
        get_new_flags_non_blocking = asyncio.to_thread(get_new_flags, rootme_id)
        new_flags = await get_new_flags_non_blocking
        if new_flags:
            # Retrieve user info
            rootme_profile = load_from_json(f'profiles/{rootme_id}.json')
            # For each flag
            for flag in new_flags:
                # Retrieve challenge info
                retrieve_challenge_non_blocking = asyncio.to_thread(retrieve_challenge, flag['id_challenge'])
                chall = (await retrieve_challenge_non_blocking)[0]
                # Send embed
                embed = create_embed(username=rootme_profile['nom'],
                                     title=chall['titre'],
                                     difficulty=chall['difficulte'],
                                     section=chall['rubrique'],
                                     date=flag['date'],
                                     img_url=u_dict[user]['avatar_url'])
                await channel.send(embed=embed)


bot.run(TOKEN)

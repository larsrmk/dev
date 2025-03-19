import discord
from discord.ext import commands
from discord import app_commands

import asyncio
import pytz # Zeitzone
import datetime # aktuelle Zeit

import os
from dotenv import load_dotenv

#print(discord.__file__)


intents = discord.Intents.all()
prefix = "py "
intents.voice_states = True
activity = discord.CustomActivity("/py") # Status

timezone = pytz.timezone('Europe/Berlin') #Zeitzone Berlin Deutschland

bot = commands.Bot(
    intents = intents, 
    debug_guilds = ['debug_guildes'],
    command_prefix = prefix,
    activity = activity,
    )

# Test Command für py Prefix
@bot.command()
async def greet(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# Slash-Command für die Hilfe
@bot.tree.command(name="py", description="Displays all possible Bot commands")
@app_commands.choices(required_role=[
    app_commands.Choice(name="Member", value="Member"),
    app_commands.Choice(name="Moderator", value="Moderator")
])
async def py(interaction: discord.Interaction, required_role: str):
    if required_role == "Member":
        embed = discord.Embed(title="Member commands for Python", color=discord.Color.blurple())
        embed.add_field(name="/link", value="Share a link in a channel", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif required_role == "Moderator":
        embed = discord.Embed(title="Mod commands for Python", color=discord.Color.blurple())
        embed.add_field(name="/important", value="Send an important message to a specific channel", inline=False)
        embed.add_field(name="/stop", value="Shuts down the bot", inline=False)
        embed.add_field(name="/userinfo", value="Provides information about a user", inline=False)
        embed.add_field(name="/warn", value="Sends a private message to a user", inline=False)
        embed.add_field(name="/clear", value="Delete a certain number of messages", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Konsolenausgabe, dass der Bot sich erfolgreich mit Discord verbunden hat
@bot.event
async def on_ready():
    # Synchronisieren der Slash-Commands
    try:
        await bot.tree.sync()  # Synchronisiere Slash-Commands
        print(f"Successfully synced {len(await bot.tree.fetch_commands())} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f'{bot.user.name} has connected to Discord!')
    # await bot.change_presence(activity=discord.Activity(name="zu!", type=discord.ActivityType.watching, status=discord.Status.online)) # Status

# Sendet ein Embed in einen Channel, wenn ein User dem Server beitritt
@bot.event
async def on_member_join(user):
    await user.edit(nick = user.display_name) # Ändert den Server-Anzeigenamen zum Globalen-Anzeigenamen

    role_id = 1205972715425628210  # ID der Rolle, die einem neuen Mitglied gegeben werden soll
    role = user.guild.get_role(role_id)
    await user.add_roles(role)

    mod_channel_id = 1214199306064498700 # ID des Mod-Channels
    mod_channel = bot.get_channel(mod_channel_id)

    # Erstellen des join-Embeds für den Mod-Channel
    embed_join_mod = discord.Embed(title = "User has joined the Server", color = discord.Color.green())
    embed_join_mod.add_field(name = "User name", value = user.mention,  inline = False)
    embed_join_mod.add_field(name = "Display name has been changed", value = user.display_name, inline = False)
    embed_join_mod.add_field(name = "Role has been assigned", value = role.name, inline = False)
    embed_join_mod.add_field(name="Date", value=user.joined_at.astimezone(timezone).strftime("%d.%m.%Y %H:%M:%S"))
    embed_join_mod.set_thumbnail(url = user.display_avatar)

    await mod_channel.send(embed = embed_join_mod) # Senden des join-Embeds in den Mod-Channel

    welcome_channel_id = 1183512266591703080 # ID des Willkommens-Channel
    welcome_cannel = bot.get_channel(welcome_channel_id)

    # Erstellen des Embeds für den Willkommens-Channel
    embed_join_welcome = discord.Embed(title = "User has joined the Server", color = discord.Color.green())
    embed_join_welcome.add_field(name = "User name", value = user.mention,  inline = False)
    embed_join_welcome.add_field(name = "Date", value = user.joined_at.astimezone(timezone).strftime("%d.%m.%Y %H:%M:%S"))
    embed_join_welcome.set_thumbnail(url = user.display_avatar)

    await welcome_cannel.send(embed = embed_join_welcome) # Senden des join-Embeds in den Willkommens-Channel

# Sendet ein Embed in einen Channel, wenn ein User den Server verlässt
@bot.event
async def on_member_remove(user):
    current = datetime.datetime.now(timezone).strftime("%d.%m.%Y %H:%M:%S") # aktuelle Uhrzeit

    mod_channel_id = 1214199306064498700 # ID des Mod-Channel
    mod_cannel = bot.get_channel(mod_channel_id)

    # Erstellen des leaf-Embeds für den Mod-Channel
    embed_leaf_mod = discord.Embed(title = "User has left the Server", color = discord.Color.red())
    embed_leaf_mod.add_field(name = "User name", value = user.mention,  inline = False)
    embed_leaf_mod.add_field(name = "Date", value = current)
    embed_leaf_mod.set_thumbnail(url = user.display_avatar)

    await mod_cannel.send(embed = embed_leaf_mod) # Senden des leaf-Embeds in den Mod-Channel

    welcome_channel_id = 1183512266591703080 # ID des Willkommens-Channel
    welcome_cannel = bot.get_channel(welcome_channel_id)

    # Erstellen des leaf-Embeds für den Willkommens-Channel
    embed_leaf_welcome = discord.Embed(title = "User has left the Server", color = discord.Color.red())
    embed_leaf_welcome.add_field(name = "User name", value = user.mention,  inline = False)
    embed_leaf_welcome.add_field(name = "Date", value = current)
    embed_leaf_welcome.set_thumbnail(url = user.display_avatar)

    await welcome_cannel.send(embed = embed_leaf_welcome) # Senden des leaf-Embeds in den Willkommens-Channel
    
# @bot.event
# async def on_message(msg):
#     if msg.author.bot: # Auf Nachrichten, die der Bot schreibt, antwortet er nicht selber
#         return
#     await msg.channel.send("Stop writing") # Bot antwortet auf jede geschrieben Nachricht
#     print(msg.channel) # Bot gibt in Konsole aus, in welchem Channel eine Nachricht gescheiben wurde

# Create temp-channels
@bot.event 
async def on_voice_state_update(user, before, after):
    category_id = 1197671296251744386  # ID der Kategorie
    trigger_channel_id = 1197671353227149363  #  ID des Voice Channels

    if after.channel and after.channel.id == trigger_channel_id:
        category = bot.get_channel(category_id)
        user = user

        # Name des Kanals
        channel_name = f"{user.display_name}s Channel"

        # moved den user in den temporären Kanal
        new_channel = await category.create_voice_channel(channel_name)
        await user.move_to(new_channel)
        
        # überprüfen ob der Channel noch existiert und ob sich noch jemand im Channel befindet
        while new_channel.members:
            await asyncio.sleep(5)
            
        await new_channel.delete()

# @bot.event
# async def on_message_delete(msg):
#     channel_id = 1214199306064498700
#     channel = bot.get_channel(channel_id)
#     delete_message = await channel.send(f"A message from {msg.author.display_name} in {msg.channel.name} has been deleted.") # Schreib, wenn eine Nachricht gelöscht wurde
#     await asyncio.sleep(10)  
#     await delete_message.delete() # Endlosschleife


# Jeder User kann die Commands ausführen (Rolle Member notwendig)
        
id_mod_role = 856169573149179935 # ID Rolle Moderator
id_member_role = 1205972715425628210 # ID Rolle Member
    
# Slash-Command für Link-Buttons
@bot.tree.command(name="link", description="Share a link in a channel")
async def link(interaction: discord.Interaction, button_name: str, url: str):
    role = discord.utils.get(interaction.guild.roles, id=id_member_role)

    if role and role in interaction.user.roles:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=button_name, url=url, style=discord.ButtonStyle.link))

        await interaction.response.send_message(view=view)
    else:
        await interaction.response.send_message("You do not have the required role to execute this command.", ephemeral=True)
    

# Nur user mit einer bestimmten Rolle können diese Commands ausführen (Rolle Moderator notwendig)

# Slash-Command für wichtige Nachrichten
@bot.tree.command(name="important", description="Send an important message to a specific channel")
async def important(interaction: discord.Interaction, receiver: discord.Role, title_text: str, fields: int):
    role = discord.utils.get(interaction.guild.roles, id=id_mod_role)

    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("You do not have the required role to execute this command.", ephemeral=True)
        return

    embed = discord.Embed(title=title_text, color=discord.Color.from_rgb(0, 224, 210))
    
    await interaction.response.send_message("I will now collect the fields for the embed. Please send them in the format 'name | value'.", ephemeral=True)

    for i in range(fields):
        await interaction.followup.send(f"Enter embed-field {i + 1} in the format 'name | value'.", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            message = await bot.wait_for("message", check=check, timeout=60)
            field_input = message.content
            title, value = field_input.split('|', 1)
            embed.add_field(name=title.strip(), value=value.strip(), inline=False)
            await message.delete()
        except Exception:
            await interaction.followup.send("Timeout or incorrect format. Canceling operation.", ephemeral=True)
            return

    channel = bot.get_channel(announcement_id)
    if not channel:
        await interaction.followup.send("Error: Announcement channel not found.", ephemeral=True)
        return

    if bot_id:
        bot_user = bot.get_user(bot_id)
        if bot_user:
            embed.set_thumbnail(url=bot_user.display_avatar.url)

    await channel.send(receiver.mention)
    await channel.send(embed=embed)
    await interaction.followup.send("Message has been sent.", ephemeral=True)

# 🛑 Stop-Befehl
@bot.tree.command(name="stop", description="Shuts down the bot")
async def stop(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, id=id_mod_role)

    if role and role in interaction.user.roles:
        await interaction.response.send_message(f'{bot.user.name} has disconnected!', ephemeral=True)
        print(f'{bot.user.name} has disconnected!')
        await bot.close()
    else:
        await interaction.response.send_message("You do not have the required role to execute this command.", ephemeral=True)

# ℹ️ Benutzerinfo-Befehl
@bot.tree.command(name="userinfo", description="Provides information about a user")
async def userinfo(interaction: discord.Interaction, user: discord.Member):
    role = discord.utils.get(interaction.guild.roles, id=id_mod_role)

    if role and role in interaction.user.roles:
        embed = discord.Embed(title="User Information", color=discord.Color.blue())
        embed.add_field(name="Global Name", value=user.global_name, inline=False)
        embed.add_field(name="Display Name", value=user.display_name, inline=False)
        embed.add_field(name="User Name", value=user.name, inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Discord User since", value=user.created_at.astimezone(timezone).strftime("%d.%m.%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Server on", value=user.joined_at.astimezone(timezone).strftime("%d.%m.%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Status", value=user.status, inline=False)
        embed.set_thumbnail(url=user.display_avatar)
        embed.set_footer(text="For more information, please ask a mod.")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You do not have the required role to execute this command.", ephemeral=True)

# ⚠️ Warn-Befehl
@bot.tree.command(name="warn", description="Sends a private message to a user")
async def warn(interaction: discord.Interaction, user: discord.User, message: str):
    role = discord.utils.get(interaction.guild.roles, id=id_mod_role)

    if role and role in interaction.user.roles:
        try:
            await user.send(f"**Warning from a Moderator:** {message}")
            embed = discord.Embed(title="Warning", color=discord.Color.dark_red())
            embed.add_field(name=f"Message to {user.display_name} has been sent:", value=message, inline=False)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't send the message to this user. They may have DMs disabled.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have the required role to execute this command.", ephemeral=True)

# 🗑️ Nachrichten löschen
@bot.tree.command(name="clear", description="Delete a certain number of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Please specify a valid number of messages to delete.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"{len(deleted)} messages have been deleted.", ephemeral=True)

# Alle User die eine bestimmte Rolle haben und alle User die eine höhergestellte Rolle haben, können diesen Command ausführen
# @bot.slash_command()
# async def clear1(ctx, amount: int):
#     role = discord.utils.get(ctx.guild.roles, id=1205972715425628210)
#     user_roles = ctx.author.roles
#     if any(role >= r for r in user_roles):
#         await ctx.channel.purge(limit=amount)
#         await ctx.respond(f'{amount} Nachrichten wurden gelöscht', ephemeral=True)
#     else:
#         await ctx.respond("Du hast nicht die erforderliche Rolle oder eine höhere Rolle, um diesen Befehl auszuführen.", ephemeral=True)

load_dotenv()
bot.run(os.getenv('Token'))
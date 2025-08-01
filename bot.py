from aiohttp import web
import os
import asyncio
import discord
import io
from discord import app_commands
from discord.ext import commands

QUEUE_CHANNEL_ID = 1393980221744746629
STICKY_CHANNEL_ID = 1388479728813604904
TICKET_CATEGORY_ID = 1388814135072133182
TICKET_SYSTEM_CHANNEL_ID = 1388480143781265430
TICKET_PING_ROLES = [1386344144594796726, 1386343809604128819]
TT_PING_ROLE = 1399807437061623899
STATUS_UPDATER_USER_ID = 1323644430015528993
COMMAND_ALLOWED_ROLE = 1386344144594796726
TRANSCRIPT_LOG_CHANNEL_ID = 1388814132085657710  # Add with other constants

EMBED_COLOR = discord.Color(0xFFFFFF)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def has_command_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, id=COMMAND_ALLOWED_ROLE)
        if role:
            return True
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

class PayButton(discord.ui.Button):
    def __init__(self, label: str, emoji: discord.PartialEmoji, link_title: str, link_url: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, emoji=emoji)
        self.link_title = link_title
        self.link_url = link_url

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=EMBED_COLOR)
        embed.set_author(name="⸍⸍⁺ ﹒ pwunii")
        embed.description = f"**{self.link_title}:** {self.link_url}"
        await interaction.response.send_message(embed=embed, ephemeral=False)


class PayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PayButton(
            label="Design",
            emoji=discord.PartialEmoji.from_str("<a:0001_p3paws:1394630751978389608>"),
            link_title="<a:0001_p3paws:1394630751978389608> design payment link",
            link_url="https://www.roblox.com/catalog/10962846684"
        ))
        self.add_item(PayButton(
            label="Edit",
            emoji=discord.PartialEmoji.from_str("<a:0001_p3paws:1394630751978389608>"),
            link_title="<a:0001_p3paws:1394630751978389608> edit payment link",
            link_url="https://www.roblox.com/catalog/10962853862/Police-Outfit"
        ))
        self.add_item(PayButton(
            label="Outfits",
            emoji=discord.PartialEmoji.from_str("<a:0001_p3paws:1394630751978389608>"),
            link_title="<a:0001_p3paws:1394630751978389608> outfits payment link",
            link_url="https://www.roblox.com/catalog/10962843555"
        ))
        self.add_item(PayButton(
            label="Server Setup",
            emoji=discord.PartialEmoji.from_str("<a:0001_p3paws:1394630751978389608>"),
            link_title="<a:0001_p3paws:1394630751978389608> server setup link",
            link_url="https://www.roblox.com/catalog/10962855641"
        ))


@bot.tree.command(name="pay", description="Show payment options")
@has_command_role()
async def pay(interaction: discord.Interaction):
    embed = discord.Embed(color=EMBED_COLOR)
    embed.set_author(name="⸍⸍⁺ ﹒ pwunii")
    embed.description = (
        "<a:022:1394479848910749840> ; **payment** <a:001:1394478860728406178>\n"
        "-# send a ss once you’ve bought"
    )
    view = PayView()
    await interaction.response.send_message(embed=embed, view=view)

class QueueStatusDropdown(discord.ui.Select):
    def __init__(self, message: discord.Message):
        options = [
            discord.SelectOption(label="noted", description="Set status to noted", default=True),
            discord.SelectOption(label="processing", description="Set status to processing", emoji="<a:1pinkloading:1394478409727610992>"),
            discord.SelectOption(label="completed", description="Set status to completed", emoji="<:05_yes:1393150237714939997>"),
        ]
        super().__init__(placeholder="Change process status...", min_values=1, max_values=1, options=options)
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != STATUS_UPDATER_USER_ID:
            await interaction.response.send_message("You are not allowed to change the status.", ephemeral=True)
            return

        selected = self.values[0]

        embed = self.message.embeds[0]
        lines = embed.description.splitlines()

        if selected == "noted":
            new_process = "・process : noted"
        elif selected == "processing":
            new_process = "・process : processing <a:1pinkloading:1394478409727610992>"
        elif selected == "completed":
            new_process = "・process : completed <:05_yes:1393150237714939997>"
        else:
            new_process = "・process : noted"

        for i, line in enumerate(lines):
            if line.startswith("・process :"):
                lines[i] = new_process
                break

        embed.description = "\n".join(lines)
        await self.message.edit(embed=embed)
        await interaction.response.send_message(f"Process status updated to **{selected}**.", ephemeral=True)


class QueueView(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__(timeout=None)
        self.add_item(QueueStatusDropdown(message))


@bot.tree.command(name="q", description="Add order to the queue")
@has_command_role()
@app_commands.describe(order="Your order description")
async def q(interaction: discord.Interaction, order: str):
    queue_channel = bot.get_channel(QUEUE_CHANNEL_ID)
    if not queue_channel:
        await interaction.response.send_message("Queue channel not found.", ephemeral=True)
        return

    embed = discord.Embed(color=EMBED_COLOR)
    embed.description = (
        "◞ ◟ 𑁬　　﹒　　❛　　<a:001:1394478860728406178>  　　　𓂂\n"
        f"・ticket : {interaction.channel.mention}\n"
        f"・order : {order}\n"
        f"・process : noted"
    )

    msg = await queue_channel.send(embed=embed)
    view = QueueView(msg)
    await msg.edit(view=view)

    await interaction.response.send_message("Order added to the queue.", ephemeral=True)

class EditModal(discord.ui.Modal, title="Edit Ticket Form"):
    how_many_edits = discord.ui.TextInput(label="How many edits?", style=discord.TextStyle.short)
    want_sparkles = discord.ui.TextInput(label="Do you want sparkles?", style=discord.TextStyle.short)
    payment_method = discord.ui.TextInput(label="Payment method", style=discord.TextStyle.short)
    group_link = discord.ui.TextInput(label="Group link", style=discord.TextStyle.short)
    providing_pngs = discord.ui.TextInput(label="Are you providing PNGs?", style=discord.TextStyle.short)

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "edit", self, self.user)

class DesignModal(discord.ui.Modal, title="Design Ticket Form"):
    amount_of_designs = discord.ui.TextInput(label="Amount of designs?", style=discord.TextStyle.short)
    inspo_or_freestyle = discord.ui.TextInput(label="Do you have inspo or should I freestyle?", style=discord.TextStyle.short)
    payment_method = discord.ui.TextInput(label="Payment method", style=discord.TextStyle.short)
    anything_else = discord.ui.TextInput(label="Anything else you'd like to tell me?", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "design", self, self.user)

class ServerSetupModal(discord.ui.Modal, title="Server Setup Ticket Form"):
    what_want = discord.ui.TextInput(label="What do you want in your server setup?", style=discord.TextStyle.paragraph)
    theme = discord.ui.TextInput(label="Theme?", style=discord.TextStyle.short)
    payment_method = discord.ui.TextInput(label="Payment method?", style=discord.TextStyle.short)
    anything_else = discord.ui.TextInput(label="Anything else you'd like to tell me?", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "server setup", self, self.user)

class OutfitMakingModal(discord.ui.Modal, title="Outfit Making Ticket Form"):
    group_link_items = discord.ui.TextInput(label="Group link / items you want me to include", style=discord.TextStyle.paragraph)
    style = discord.ui.TextInput(label="Style?", style=discord.TextStyle.short)
    amount_of_fits = discord.ui.TextInput(label="Amount of fits?", style=discord.TextStyle.short)
    sng_or_cac_form = discord.ui.TextInput(label="PNG or CAC form?", style=discord.TextStyle.short)

    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket_channel(interaction, "outfit making", self, self.user)

async def create_ticket_channel(interaction: discord.Interaction, ticket_type: str, modal, user: discord.User):
    guild = interaction.guild
    category = guild.get_channel(TICKET_CATEGORY_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for role_id in TICKET_PING_ROLES:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel_name = f"ticket-{user.name.lower()}-{ticket_type.replace(' ', '-')}"
    ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

    embed = discord.Embed(color=EMBED_COLOR)
    embed.set_author(name="⸍⸍⁺ ﹒ pwunii")

    for child in modal.children:
        embed.add_field(name=child.label, value=child.value or "N/A", inline=False)

    ping_text = " ".join(f"<@&{r}>" for r in TICKET_PING_ROLES) + f" {user.mention}"

    await ticket_channel.send(content=ping_text, embed=embed)
    await interaction.response.send_message(f"ticket created: {ticket_channel.mention}", ephemeral=True)

class TicketDropdown(discord.ui.Select):
    def __init__(self, bot):
        options = [
            discord.SelectOption(label="edit"),
            discord.SelectOption(label="design"),
            discord.SelectOption(label="server setup"),
            discord.SelectOption(label="outfit making"),
        ]
        super().__init__(placeholder="click to open a ticket", min_values=1, max_values=1, options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        modal = None
        if choice == "edit":
            modal = EditModal(self.bot, interaction.user)
        elif choice == "design":
            modal = DesignModal(self.bot, interaction.user)
        elif choice == "server setup":
            modal = ServerSetupModal(self.bot, interaction.user)
        elif choice == "outfit making":
            modal = OutfitMakingModal(self.bot, interaction.user)
        if modal:
            await interaction.response.send_modal(modal)

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown(bot))

@bot.tree.command(name="ticket", description="Send ticket system embed with dropdown")
@has_command_role()
async def ticketsystem(interaction: discord.Interaction):
    embed = discord.Embed(color=EMBED_COLOR)
    embed.description = (
        "open a ticket! \n"
        "　　　　　　　　　　♡　𓈒⠀⠀tickets　　˒　　ˑ\n\n"
        "　　　🌺 　　　　ꜛ 　　⸜♡⸝⠀⠀　　　　claim perks \n"
        "　　　　　☆　　 ˶ 　　　order　\n"
        "　　　　　　　　　　ミ　◟　　⠀𓏴⠀　　other\n\n"
        "　　　　　　◜　　dont make a troll ticket　◞　　　　𓇯"
    )
    view = TicketView(bot)

    target_channel = bot.get_channel(TICKET_SYSTEM_CHANNEL_ID)
    if not target_channel:
        await interaction.response.send_message("Ticket system channel not found.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    await target_channel.send(embed=embed, view=view)

    await interaction.followup.send("Ticket system embed sent.", ephemeral=True)

@bot.tree.command(name="tt", description="Announce a new tiktok")
@has_command_role()
@app_commands.describe(link="TikTok link to announce")
async def tt(interaction: discord.Interaction, link: str):
    TT_PING = f"<@&{TT_PING_ROLE}>"
    msg = (
        f"⠀>﹏<｡)⠀⠀⠀❛⠀⠀⠀[new tiktok]({link})⠀⠀⠀⠀𓈒⠀⠀⠀⠀OO%⠀⠀⠀⠀𓏵⠀⠀⠀{TT_PING}⠀⠀⠀⠀𐙚"
    )
    await interaction.response.send_message(msg, ephemeral=False, allowed_mentions=discord.AllowedMentions(roles=True))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != STICKY_CHANNEL_ID:
        return

    async for msg in message.channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            if "<:1pinkcrown:1394478939870597252>  : vouch layout" in msg.embeds[0].description:
                try:
                    await msg.delete()
                except:
                    pass

    embed = discord.Embed(color=EMBED_COLOR)
    embed.description = (
        "<:1pinkcrown:1394478939870597252>  : vouch layout\n"
        "<:8blackarrow:1394480860098465895> vouch @₍^.  ̫.^₎ [order]"
    )
    await message.channel.send(embed=embed)

@bot.tree.command(name="close", description="Close the ticket and save a transcript")
@has_command_role()
async def close(interaction: discord.Interaction):
    channel = interaction.channel

    if not isinstance(channel, discord.TextChannel) or not channel.name.startswith("ticket-"):
        await interaction.response.send_message("This command can only be used in ticket channels.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    transcript = io.StringIO()
    async for msg in channel.history(oldest_first=True, limit=None):
        time = msg.created_at.strftime("%Y-%m-%d %H:%M")
        author = f"{msg.author} ({msg.author.id})"
        content = msg.content or ""
        transcript.write(f"[{time}] {author}: {content}\n")
        for attachment in msg.attachments:
            transcript.write(f"[{time}] {author} attached: {attachment.url}\n")

    transcript.seek(0)
    file = discord.File(transcript, filename=f"{channel.name}_transcript.txt")

    log_channel = bot.get_channel(TRANSCRIPT_LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"Transcript from {channel.mention} (closed by {interaction.user.mention})", file=file)

    await channel.delete()

async def handle(request):
    return web.Response(text="Bot is running")

port = int(os.getenv("PORT", 8080))
app = web.Application()
app.add_routes([web.get('/', handle)])

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server running on port {port}")

    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())

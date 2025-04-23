import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime
from mvc_checker import get_new_appointments, TYPE_CODES, MVC_LOCATION_CODES
from config import DISCORD_TOKEN, CHECK_INTERVAL_SECONDS

intents = discord.Intents.default()
intents.message_content = False  # Explicitly false unless message reading is needed
subscriptions = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mvc_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MVCBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        self.loop.create_task(self.notify_users_loop())
        logger.info("✅ Slash commands synced and background task started")

    async def notify_users_loop(self):
        await self.wait_until_ready()
        seen_urls = set()
        while not self.is_closed():
            try:
                for user_id, prefs in subscriptions.items():
                    found = {}
                    config_info = {}
                    for t, l in prefs:
                        type_code = TYPE_CODES[t]
                        loc_code = MVC_LOCATION_CODES[t][l]
                        config_info.setdefault((t, type_code), []).append((l, loc_code))

                    found = get_new_appointments(config_info, seen_urls)
                    if not found:
                        continue

                    user = await self.fetch_user(user_id)
                    grouped = {}
                    for url, data in found.items():
                        key = (data["type"], data["location"])
                        grouped.setdefault(key, []).append((data["date"], data["time"], url))
                        seen_urls.add(url)

                    for (appt_type, location), values in grouped.items():
                        values.sort(key=lambda x: (x[0], x[1]))
                        embed = discord.Embed(
                            title=f"{appt_type} @ {location}",
                            description=f"📅 Appointments found: {len(values)}",
                            color=0x2ecc71
                        )

                        current_date = None
                        for i, (date, time, url) in enumerate(values):
                            if not url.startswith("https://"):
                                logger.warning(f"⚠️ Invalid URL skipped: {url}")
                                continue
                            prefix = "🟢 EARLIEST AVAILABLE" if i == 0 else ""
                            if current_date != date:
                                current_date = date
                                embed.add_field(name=f"📅 {date}", value="\u200b", inline=False)
                            embed.add_field(
                                name=f"{prefix} 🕒 {time}" if prefix else f"🕒 {time}",
                                value=f"[Book Slot]({url})",
                                inline=False
                            )

                        embed.set_footer(text="NJ MVC Appointment Bot")
                        embed.timestamp = discord.utils.utcnow()

                        try:
                            dm_channel = user.dm_channel or await user.create_dm()
                            messages_to_delete = []
                            async for msg in dm_channel.history(limit=50):
                                if msg.author == self.user:
                                    messages_to_delete.append(msg)
                            new_message = await user.send(embed=embed)
                            for msg in messages_to_delete:
                                if msg.id != new_message.id:
                                    try:
                                        await msg.delete()
                                    except Exception:
                                        pass
                        except discord.Forbidden:
                            logger.warning(f"❌ Cannot DM user {user_id}")
            except Exception as e:
                logger.exception(f"❌ Error in notify loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

bot = MVCBot()

# ---- Slash Commands ----
@bot.tree.command(name="subscribe", description="Subscribe using dropdown menus")
async def subscribe(interaction: discord.Interaction):
    view = SubscriptionView(user_id=interaction.user.id)
    await interaction.response.send_message("Please choose an appointment type:", view=view, ephemeral=True)

@bot.tree.command(name="my_subscriptions", description="View your current subscriptions")
async def my_subscriptions(interaction: discord.Interaction):
    user_id = interaction.user.id
    subs = subscriptions.get(user_id)
    if not subs:
        await interaction.response.send_message("📭 You have no subscriptions.", ephemeral=True)
        return
    msg = "\n".join(f"- {t} @ {l}" for t, l in subs)
    await interaction.response.send_message(f"📌 Your subscriptions:\n{msg}", ephemeral=True)

@bot.tree.command(name="unsubscribe", description="Unsubscribe using a dropdown menu")
async def unsubscribe(interaction: discord.Interaction):
    user_id = interaction.user.id
    subs = subscriptions.get(user_id)

    if not subs:
        await interaction.response.send_message("📭 You have no subscriptions to remove.", ephemeral=True)
        return

    view = UnsubscribeView(user_id, list(subs))
    await interaction.response.send_message("Choose subscriptions to remove:", view=view, ephemeral=True)

@bot.tree.command(name="clear_all", description="Clear all your subscriptions")
async def clear_all(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in subscriptions:
        subscriptions[user_id].clear()
        await interaction.response.send_message("🧹 All your subscriptions have been cleared.", ephemeral=True)
    else:
        await interaction.response.send_message("You had no subscriptions to clear.", ephemeral=True)


from discord.ui import View, Select, Button

class SubscriptionView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.selected_type = None
        self.selected_location = None

        # Type Dropdown
        self.add_item(AppointmentTypeDropdown(self))

class AppointmentTypeDropdown(Select):
    def __init__(self, parent):
        self.parent = parent
        options = [discord.SelectOption(label=t) for t in TYPE_CODES]
        super().__init__(placeholder="Choose an appointment type", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.parent.selected_type = self.values[0]
        self.parent.clear_items()
        self.parent.add_item(AppointmentLocationDropdown(self.parent))
        await interaction.response.edit_message(content=f"🔍 Selected type: `{self.values[0]}`\nNow pick a location:", view=self.parent)

class AppointmentLocationDropdown(Select):
    def __init__(self, parent):
        self.parent = parent
        all_locs = MVC_LOCATION_CODES.get(parent.selected_type, {})
        self.all_locations = list(all_locs.keys())  # Full list (up to 24 real + 1 SELECT ALL)

        # Only include SELECT ALL if <= 24 real items
        show_select_all = len(self.all_locations) <= 24
        options = (
            [discord.SelectOption(label="🌐 SELECT ALL LOCATIONS", value="__ALL__")] if show_select_all else []
        ) + [discord.SelectOption(label=l) for l in self.all_locations[:25]]

        super().__init__(
            placeholder="Choose one or more locations",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: discord.Interaction):
        if "__ALL__" in self.values:
            # Remove the __ALL__ and manually select everything else
            self.parent.selected_location = self.all_locations
        else:
            self.parent.selected_location = [v for v in self.values if v != "__ALL__"]

        self.parent.clear_items()
        self.parent.add_item(ConfirmButton(self.parent))

        locs = ', '.join(f"`{loc}`" for loc in self.parent.selected_location)
        await interaction.response.edit_message(
            content=f"✅ `{self.parent.selected_type}` at {locs} selected.\nClick confirm to subscribe.",
            view=self.parent
        )



class ConfirmButton(Button):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(label="Confirm", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        for loc in self.parent.selected_location:
            subscriptions.setdefault(user_id, set()).add((self.parent.selected_type, loc))

        loc_list = ', '.join(f"**{loc}**" for loc in self.parent.selected_location)
        embed = discord.Embed(
            title="✅ Subscription Confirmed!",
            description=f"You’ll be alerted for:\n\n**{self.parent.selected_type}** at {loc_list}",
            color=0x2ecc71
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)
class UnsubscribeView(discord.ui.View):
    def __init__(self, user_id, subs):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.all_subs = subs
        self.selected = []
        self.dropdown = UnsubscribeDropdown(self, subs)
        self.confirm_button = UnsubscribeConfirmButton(self)
        self.refresh_view()

    def refresh_view(self):
        self.clear_items()
        self.dropdown = UnsubscribeDropdown(self, self.all_subs)
        self.add_item(self.dropdown)
        self.add_item(self.confirm_button)

class UnsubscribeDropdown(discord.ui.Select):
    def __init__(self, parent, subs):
        self.parent = parent
        self.sub_map = [(t, l) for t, l in subs]
        options = [discord.SelectOption(label="🌐 SELECT ALL", value="__ALL__")] + [
            discord.SelectOption(label=f"{t} @ {l}", value=f"{t}|{l}") for t, l in self.sub_map
        ]
        super().__init__(
            placeholder="Select subscriptions to remove",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: discord.Interaction):
        if "__ALL__" in self.values:
            self.parent.selected = self.sub_map
        else:
            self.parent.selected = [val.split("|") for val in self.values if val != "__ALL__"]

        await interaction.response.edit_message(
            content="✅ Subscriptions selected. Click confirm to remove them.",
            view=self.parent
        )

class UnsubscribeConfirmButton(discord.ui.Button):
    def __init__(self, parent):
        super().__init__(label="Confirm Unsubscribe", style=discord.ButtonStyle.danger)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        user_id = self.parent.user_id
        for t, l in self.parent.selected:
            subscriptions[user_id].discard((t, l))

        if not subscriptions[user_id]:
            subscriptions.pop(user_id)
            await interaction.response.edit_message(
                content="🧹 All your subscriptions have been removed.",
                view=None
            )
        else:
            self.parent.all_subs = list(subscriptions[user_id])
            self.parent.refresh_view()
            await interaction.response.edit_message(
                content="🧹 Selected subscriptions removed. Remaining shown below:",
                view=self.parent
            )


# ---- Run Bot ----
bot.run(DISCORD_TOKEN)

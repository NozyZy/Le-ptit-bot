import copy
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
log = logging.getLogger(__name__)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

POKEMON_DATA_FILE = "data/pokemon_starters.json"

BASE_HP = 15
HP_PER_LEVEL = 1.3

CRIT_CHANCE = 0.06
CRIT_MULTIPLIER = 1.5
DODGE_CHANCE = 0.25
DODGE_TIMEOUT = 3.0

XP_MIN, XP_MAX = 15, 55

COMBAT_COOLDOWN = 60 * 5 if os.getenv("RUN_MODE") == "PROD" else 0
XP_COOLDOWN = 60 if os.getenv("RUN_MODE") == "PROD" else 0

TYPE_MULTIPLIER = {
    ("🔥", "🌿"): 1.25,
    ("🌿", "💧"): 1.25,
    ("💧", "🔥"): 1.25,
    ("🌿", "🔥"): 0.8,
    ("💧", "🌿"): 0.8,
    ("🔥", "💧"): 0.8,
}

COLORS = {
    "🔥": 0xE72324,
    "🌿": 0x3DA224,
    "💧": 0x2481EF,
}

POKEMON_ENTRY_DEFAULTS = {
    "starter": None,
    "pokemon": None,
    "level": 1,
    "xp": 0,
    "last_time": 0,
    "HP": BASE_HP,
    "type": None,
    "wins": 0,
    "losses": 0,
    "begin_date": None,
    "does_not_evolve": False,
}


@dataclass
class PokemonEntry:
    starter: Optional[str] = None
    pokemon: Optional[str] = None
    level: int = 1
    xp: int = 0
    last_time: float = 0
    HP: int = BASE_HP
    type: Optional[str] = None
    wins: int = 0
    losses: int = 0
    begin_date: Optional[str] = None
    does_not_evolve: bool = False


def is_owner(interaction: discord.Interaction, user_id: str) -> bool:
    return str(interaction.user.id) == user_id


def xp_to_next_level(level: int) -> int:
    return level * 50


def health_bar(current: int, max_hp: int, size: int = 10) -> str:
    ratio = current / max_hp if max_hp else 0
    filled = min(max(int(ratio * size), 1 if ratio > 0 else 0), size)
    empty = size - filled
    color = "🟥" if ratio < 0.15 else "🟨" if ratio < 0.5 else "🟩"
    return f"{color * filled}{'⬜' * empty} {int(ratio * 100)}%"


def power_emoji_for_level(level: int) -> str:
    for max_level, emoji in POWER_EMOJIS:
        if level <= max_level:
            return emoji
    return POWER_EMOJIS[-1][1]


def ensure_hp_field(entry: dict) -> None:
    entry.setdefault("HP", 0)


def get_pokemon_entry(data: dict, guild_id: str, user_id: str):
    return data.get(guild_id, {}).get(user_id)


def save_pokemon_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(POKEMON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_pokemon_data() -> dict:
    os.makedirs("data", exist_ok=True)
    try:
        with open(POKEMON_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def fetch_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


def pokemon_artwork_url(pokemon_id: int) -> str:
    return (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/"
        f"official-artwork/{pokemon_id}.png"
    )


def compute_damage(attacker: dict, defender: dict) -> tuple[int, bool]:
    base = (attacker["level"] ** 0.75) * 1.3
    rng = random.uniform(0.8, 1.5)

    mult = TYPE_MULTIPLIER.get((attacker["type"], defender["type"]), 1.0)
    crit = random.random() < CRIT_CHANCE

    if crit:
        mult *= CRIT_MULTIPLIER

    return max(1, round(base * rng * mult)), crit


def compute_max_hp(entry: dict) -> int:
    ensure_hp_field(entry)
    return BASE_HP + int(entry["level"] * HP_PER_LEVEL)


class PokemonStarterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pokemon_data = load_pokemon_data()

    async def level_up(self, entry: dict, user: discord.Member) -> Optional[str]:
        leveled = False

        while entry["xp"] >= xp_to_next_level(entry["level"]) and entry["level"] < 100:
            entry["xp"] -= xp_to_next_level(entry["level"])
            entry["level"] += 1
            entry["HP"] += random.randint(0, 3)
            leveled = True

        if not leveled:
            return None

        lvl = entry["level"]

        if lvl == 100:
            return f"🔥 LEVEL 100 {user.mention} {entry['pokemon']}"
        if lvl in (50, 75, 90):
            return f"🆙 {entry['pokemon']} atteint niveau {lvl}"

        return f"🆙 {entry['pokemon']} level {lvl}"

    async def evolve(self, entry: dict, user: discord.Member, channel: discord.TextChannel) -> None:
        chain = STARTER_CHAINS.get(entry["pokemon"].lower())
        if not chain:
            return

        for i, (name, evo_level, *_) in enumerate(chain):
            if (
                name.lower() == entry["pokemon"].lower()
                and evo_level
                and entry["level"] >= evo_level
            ):
                if entry["does_not_evolve"]:
                    return

                old = entry["pokemon"]
                nxt = chain[i + 1][0]
                entry["pokemon"] = nxt

                await channel.send(f"{old} → {nxt}")
                break

    @app_commands.command(name="choose_starter")
    async def choose_starter(self, interaction: discord.Interaction, choix: str | None = None):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        entry = get_pokemon_entry(self.pokemon_data, guild_id, user_id)

        if entry:
            await interaction.response.send_message("Déjà un starter", ephemeral=True)
            return

        self.pokemon_data.setdefault(guild_id, {})[user_id] = copy.deepcopy(POKEMON_ENTRY_DEFAULTS)
        e = self.pokemon_data[guild_id][user_id]

        e["starter"] = choix
        e["pokemon"] = choix

        save_pokemon_data(self.pokemon_data)

        await interaction.response.send_message(f"{choix} choisi")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        entry = get_pokemon_entry(
            self.pokemon_data,
            str(message.guild.id),
            str(message.author.id),
        )
        if not entry:
            return

        now = time.time()
        if entry.get("last_time", 0) + XP_COOLDOWN > now:
            return

        entry["xp"] += random.randint(XP_MIN, XP_MAX)

        msg = await self.level_up(entry, message.author)
        if msg:
            await message.reply(msg)

        entry["last_time"] = now
        save_pokemon_data(self.pokemon_data)


async def setup(bot):
    await bot.add_cog(PokemonStarterCog(bot))
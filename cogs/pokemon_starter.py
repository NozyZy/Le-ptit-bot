import asyncio
import datetime
import io
import json
import logging
import os
import random
import time
import urllib.parse

# Third-party imports
import discord
import numpy as np
import requests
from PIL import Image
from discord import app_commands
from discord.ext import commands

# Local application imports
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()

# Disable debug logs from urllib3 and requests
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


# ── Pokémon starter system ────────────────────────────────────────────────────
# Each starter: list of (name, evo_level) tuples. evo_level=None = final form.
def _to_poke_tuple(entry: list) -> tuple[str | int | None, ...]:
    return tuple(entry)  # type: ignore[return-value]


with open("database/pokemon/starters.json", "r", encoding="utf-8") as _f:
    _raw = json.load(_f)

STARTERS: dict[str, list[list[tuple[str | int | None, ...]]]] = {
    gen: [[_to_poke_tuple(entry) for entry in chain] for chain in chains]
    for gen, chains in _raw.items()
}

# Flat lookup: starter_name → full evolution chain
STARTER_CHAINS: dict[str, list] = {}
STARTER_BASE_NAMES: list[str] = []
for gen_chains in STARTERS.values():
    for chain in gen_chains:
        base = str(chain[0][0])
        STARTER_BASE_NAMES.append(base)
        for form, *_ in chain:
            STARTER_CHAINS[str(form).lower()] = chain

POKEMON_DATA_FILE = "data/pokemon_starters.json"

POWER_EMOJIS: list[tuple[int, str]] = [
    (1, "🌱"),
    (4, "🐣"),
    (8, "🗡️"),
    (12, "🛡️"),
    (16, "⚔️"),
    (20, "🏹"),
    (24, "⚡"),
    (28, "⭐"),
    (32, "🌟"),
    (36, "💎"),
    (40, "🔮"),
    (44, "⚜️"),
    (49, "👑"),
    (54, "🔥🔥"),
    (59, "⚡🔥"),
    (64, "🌟🔥"),
    (69, "🔥✨"),
    (74, "🔥🔥✨"),
    (79, "🔥🔥🔥"),
    (84, "💥🔥"),
    (89, "💥✨"),
    (94, "💥💥"),
    (97, "✨💥✨"),
    (99, "💥👑💥"),
    (100, "🔥💥👑💥🔥"),
]

POKEMON_TYPES = ["🌿", "🔥", "💧"]

TYPE_MULTIPLIER = {
    ("🔥", "🌿"): 1.4,
    ("🌿", "💧"): 1.4,
    ("💧", "🔥"): 1.4,

    ("🌿", "🔥"): 0.6,
    ("💧", "🌿"): 0.6,
    ("🔥", "💧"): 0.6,
}

COLORS = {
    "🔥": 0xE72324,
    "🌿": 0x3DA224,
    "💧": 0x2481EF
}

COMBAT_COOLDOWN = 60 * 5
XP_COOLDOWN = 60

CRIT_CHANCE = 0.07
CRIT_MULTIPLIER = 1.5

XP_MIN, XP_MAX = 15, 55

DEFAULT = {
    "HP": 15,
    "wins": 0,
    "losses": 0,
    "last_combat": 0
}

POKEMON_DATA_FILE = "data/pokemon_starters.json"


def pokepedia_url(name: str) -> str:
    # remplace espaces par underscore + encode safe URL
    formatted = name.replace(" ", "_")
    return f"https://www.pokepedia.fr/{urllib.parse.quote(formatted)}"


def load_pokemon_data() -> dict:
    os.makedirs("data", exist_ok=True)
    try:
        with open(POKEMON_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_pokemon_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(POKEMON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def xp_to_next_level(level: int) -> int:
    """XP needed to go from `level` to `level + 1`."""
    return level * 50

def get_pokemon_id_from_entry(entry: dict) -> int | None:
    chain = STARTER_CHAINS.get(entry["pokemon"].lower())
    if not chain:
        return None

    for i, (name, *_) in enumerate(chain):
        if name.lower() == entry["pokemon"].lower():
            if len(chain[i]) > 2:
                return chain[i][2]
    return None

def get_pokemon_entry(data: dict, guild_id: str, user_id: str) -> dict | None:
    return data.get(guild_id, {}).get(user_id)

def pokemon_artwork_url(pokemon_id: int) -> str:
    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"

def make_silhouette(image_bytes: bytes, color: tuple) -> io.BytesIO:
    """Return a BytesIO PNG where every non-transparent pixel is replaced by `color`."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    r, g, b, a = img.split()
    colored = Image.new("RGBA", img.size, color + (255,))
    colored.putalpha(a)
    buf = io.BytesIO()
    colored.save(buf, format="PNG")
    buf.seek(0)
    return buf

def detect_facing_direction(img: Image.Image) -> str:
    """
    Détecte la direction du sprite en analysant la densité de pixels
    sur les bords gauche et droite (zone du visage souvent plus détaillée).
    """

    img = img.convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]

    if np.sum(alpha) == 0:
        return "right"

    height, width = alpha.shape

    # zones verticales des bords (focus sur "visage probable")
    edge_width = max(5, width // 6)

    left_region = alpha[:, :edge_width]
    right_region = alpha[:, width - edge_width:]

    # score = nombre de pixels non transparents (densité de détails)
    left_score = np.sum(left_region > 0)
    right_score = np.sum(right_region > 0)

    # debug optionnel:
    # print(left_score, right_score)

    # si plus de détails à gauche → sprite regarde probablement à gauche
    if left_score > right_score:
        return "left"
    else:
        return "right"

def generate_versus_image(p1: dict, p2: dict) -> io.BytesIO:
    base_size = (300, 300)

    def fetch_pokemon_image(pokemon_id: int) -> Image.Image:
        url = pokemon_artwork_url(pokemon_id)
        logger.debug(f"Fetching Pokémon artwork ID={pokemon_id} → {url}")

        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        return img.resize(base_size)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot/1.0)"
    }

    vs_url = "https://upload.wikimedia.org/wikipedia/commons/7/70/Street_Fighter_VS_logo.png"

    resp = requests.get(vs_url, headers=headers, timeout=5)
    resp.raise_for_status()

    vs_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    vs_img = vs_img.resize((220, 220))

    p1_id = get_pokemon_id_from_entry(p1)
    p2_id = get_pokemon_id_from_entry(p2)

    if not p1_id or not p2_id:
        raise ValueError("Impossible de générer l'image VS (IDs manquants)")

    img1 = fetch_pokemon_image(p1_id)
    img2 = fetch_pokemon_image(p2_id)

    dir1 = detect_facing_direction(img1)
    dir2 = detect_facing_direction(img2)

    if dir1 == "left":
        img1 = img1.transpose(Image.FLIP_LEFT_RIGHT)

    if dir2 == "right":
        img2 = img2.transpose(Image.FLIP_LEFT_RIGHT)

    # ───── canvas plus large pour respiration visuelle ─────
    final = Image.new("RGBA", (900, 380), (18, 18, 22, 255))

    # ───── positions "combat stance" ─────
    p1_pos = (40, 40)
    p2_pos = (560, 30)
    vs_pos = (340, 80)

    # ───── SHADOW propre (alpha-safe) ─────
    vs_alpha = vs_img.split()[3]

    shadow = Image.new("RGBA", vs_img.size, (0, 0, 0, 120))
    shadow.putalpha(vs_alpha)

    # ───── paste ordre important ─────
    final.paste(img1, p1_pos, img1)

    # shadow légèrement décalé
    final.paste(shadow, (vs_pos[0] + 6, vs_pos[1] + 6), shadow)

    final.paste(vs_img, vs_pos, vs_img)
    final.paste(img2, p2_pos, img2)

    buf = io.BytesIO()
    final.save(buf, format="PNG")
    buf.seek(0)
    return buf

def power_emoji_for_level(level: int) -> str:
    for max_level, emoji in POWER_EMOJIS:
        if level <= max_level:
            return emoji
    return POWER_EMOJIS[-1][1]

def compute_damage(attacker: dict, defender: dict) -> tuple[int, bool]:
    damage_base = attacker["level"] * 0.55 * random.uniform(0.85, 1.35)

    multiplier = TYPE_MULTIPLIER.get(
        (attacker["type"], defender["type"]),
        1.0
    )

    crit = random.random() < CRIT_CHANCE
    if crit:
        multiplier *= CRIT_MULTIPLIER

    dmg = round(damage_base * multiplier)
    return max(1, dmg), crit

def health_bar(current: int, max_hp: int, size: int = 10) -> str:
    ratio = current / max_hp if max_hp > 0 else 0

    filled = int(ratio * size)

    if ratio <= 0:
        return "⬜" * size + " 0%"

    if ratio < 0.15:
        color = "🟥"
    elif ratio < 0.5:
        color = "🟨"
    else:
        color = "🟩"

    empty = "⬜"

    if filled == 0:
        filled = 1

    filled = min(filled, size)

    bar = color * filled + empty * (size - filled)

    return f"{bar} {int(ratio * 100)}%"


class DeleteStarterView(discord.ui.View):
    def __init__(self, cog, guild_id, user_id, entry):
        super().__init__(timeout=30)
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.entry = entry

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, _):
        self.cog.pokemon_data[self.guild_id].pop(self.user_id)
        save_pokemon_data(self.cog.pokemon_data)

        logger.info(
            f"{interaction.user.name} - {interaction.guild.name} - "
            f"A supprimé son starter {self.entry['pokemon']}"
        )

        await interaction.response.edit_message(
            content=f"🗑️ **{self.entry['pokemon']}** a été supprimé. "
                    f"Tu peux choisir un nouveau starter avec `/choose_starter`.",
            view=None
        )

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(
            content=f"Suppression annulée. **{self.entry['pokemon']}** est en sécurité.",
            view=None
        )


class CombatAcceptView(discord.ui.View):
    def __init__(self, adversary: discord.Member) -> None:
        super().__init__(timeout=60)
        self.accepted = False
        self.adversary = adversary

    @discord.ui.button(label="⚔️ Accepter", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if self.adversary.bot:
            self.accepted = True
            self.stop()
            await interaction.message.edit(
                content="⚔️ Combat accepté !",
                view=None
            )
            return

        if interaction.user.id != self.adversary.id:
            await interaction.response.send_message("Tu n'es pas l'adversaire ciblé !", ephemeral=True)
            return

        self.accepted = True
        self.stop()
        await interaction.message.edit(
            content="⚔️ Combat accepté !",
            view=None
        )

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.adversary.id:
            await interaction.response.send_message("Tu n'es pas l'adversaire ciblé !", ephemeral=True)
            return

        self.accepted = False
        self.stop()
        await interaction.response.edit_message(content="Combat refusé.", view=None)


class PokemonStarterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pokemon_data = load_pokemon_data()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user = message.author
        user_id = str(user.id)

        entry = get_pokemon_entry(self.pokemon_data, guild_id, user_id)
        if not entry:
            return

        entry.setdefault("last_time", DEFAULT.get("last_time"))
        now = time.time()
        if entry.get("last_time", 0) + XP_COOLDOWN > now:
            return

        xp_gain = random.randint(XP_MIN, XP_MAX)
        entry["xp"] += xp_gain

        lvl_message = await self.level_up(entry, user)

        if lvl_message and len(lvl_message):
            await message.reply(lvl_message)

        await self.evolve(entry, user, message.channel)

        entry["last_time"] = now
        save_pokemon_data(self.pokemon_data)

    # ───────── AUTOCOMPLETE ─────────
    async def starter_autocomplete(self, interaction, current: str):
        starters = [
            str(chain[0][0])
            for chains in STARTERS.values()
            for chain in chains
        ]
        current = current.lower()
        return [
            app_commands.Choice(name=s, value=s)
            for s in starters
            if current in s.lower()
        ][:25]

    # ───────── XP & LEVEL UP ─────────
    async def level_up(self, entry: dict, user: discord.Member) -> str | None:
        message = None
        leveled_up = False

        entry.setdefault("HP", DEFAULT.get("HP") + round(1.5 * entry["level"]))

        while entry["xp"] >= xp_to_next_level(entry["level"]) and entry["level"] < 100:
            entry["xp"] -= xp_to_next_level(entry["level"])
            entry["level"] += 1
            entry["HP"] += random.randint(0, 3)
            leveled_up = True

        if not leveled_up:
            return message

        lvl = entry["level"]
        logger.info(f"{user.name} - {entry['pokemon']} - Est passé level {entry['level']}")

        # ───────── messages EXACTS restaurés ─────────
        if lvl == 50:
            message = (
                f"🆙 Le **{entry['pokemon']}** de **{user.name}** "
                f"a atteint le niveau **50** !"
            )

        elif lvl == 75:
            message = (
                f"🆙 Le **{entry['pokemon']}** de **{user.name}** "
                f"devient très puissant (niveau **75**) !"
            )

        elif lvl == 90:
            message = (
                f"🆙 Le **{entry['pokemon']}** de **{user.name}** "
                f"frôle le légendaire !\n## Niveau 90 atteint"
            )

        elif lvl == 100:
            message = (
                "@everyone\n"
                "# 🔥 NIVEAU 100 ATTEINT 🔥\n"
                f"Le **{entry['pokemon']}** de **{user.name}** "
                f"a atteint le niveau **100** !"
            )

        else:
            message = (
                f"🆙 Le **{entry['pokemon']}** de **{user.name}** est passé niveau **{lvl}** !"
            )

        return message

    async def evolve(self, entry: dict, user: discord.Member, channel: discord.TextChannel) -> str | None:
        message = None

        chain = STARTER_CHAINS.get(entry["pokemon"].lower())
        if not chain:
            return message

        for i, (name, evo_level, *_) in enumerate(chain):
            if (
                    name.lower() == entry["pokemon"].lower()
                    and evo_level is not None
                    and entry["level"] >= evo_level
            ):
                old_name = entry["pokemon"]
                next_name = chain[i + 1][0]
                entry["pokemon"] = next_name
                entry.setdefault("HP", DEFAULT.get("HP") + round(1.5 * entry["level"]))
                entry["HP"] += random.randint(5, 10)

                old_id = chain[i][2] if len(chain[i]) > 2 else None
                new_id = chain[i + 1][2] if len(chain[i + 1]) > 2 else None

                message = f"🎉 **{user.mention} {old_name} a évolué en {next_name} !**"
                logger.info(f"{user.name} - {channel.guild.name} - {old_name} a évolué en {next_name}")

                # ───── ANIMATION RESTAURÉE ─────
                old_bytes = None
                if old_id:
                    try:
                        old_bytes = requests.get(
                            pokemon_artwork_url(old_id),
                            timeout=5
                        ).content
                    except Exception:
                        pass

                caption = f"Quoi ?! **{old_name}** de {user.mention} se transforme..."

                if old_bytes:
                    msg = await channel.send(
                        caption,
                        file=discord.File(io.BytesIO(old_bytes), filename="poke.png")
                    )
                else:
                    msg = await channel.send(caption)

                if old_bytes:
                    for color in [(0, 0, 0), (255, 255, 255), (0, 0, 0), (255, 255, 255)]:
                        await asyncio.sleep(0.6)
                        await msg.delete()
                        msg = await channel.send(
                            caption,
                            file=discord.File(
                                make_silhouette(old_bytes, color),
                                filename="poke.png"
                            )
                        )
                else:
                    await asyncio.sleep(4)

                await asyncio.sleep(0.8)
                await msg.delete()

                final_caption = f"🎉 {user.mention} **{old_name}** a évolué en **{next_name}** !"

                if new_id:
                    try:
                        new_bytes = requests.get(
                            pokemon_artwork_url(new_id),
                            timeout=5
                        ).content
                        await channel.send(
                            final_caption,
                            file=discord.File(io.BytesIO(new_bytes), filename="poke_new.png")
                        )
                    except Exception:
                        await channel.send(final_caption)
                else:
                    await channel.send(final_caption)

                break

        return message

    # ───────── /choose_starter ─────────
    @app_commands.command(name="choose_starter", description="Choisir ou afficher ton starter Pokémon")
    @app_commands.describe(choix="Nom du Pokémon starter")
    @app_commands.autocomplete(choix=starter_autocomplete)
    async def choose_starter(self, interaction: discord.Interaction, choix: str | None = None):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        entry = get_pokemon_entry(self.pokemon_data, guild_id, user_id)

        # ───── Affichage ─────
        if choix is None:
            if entry:
                chain = STARTER_CHAINS.get(entry["pokemon"].lower(), [])
                cur_idx = next(
                    (i for i, (n, *_) in enumerate(chain) if n.lower() == entry["pokemon"].lower()),
                    -1
                )

                xp_needed = xp_to_next_level(entry["level"])
                bar_filled = int(entry["xp"] / xp_needed * 10)
                bar = "█" * bar_filled + "░" * (10 - bar_filled)

                if cur_idx >= 0 and chain[cur_idx][1] is not None:
                    next_name = chain[cur_idx + 1][0]
                    next_level = chain[cur_idx][1]
                    next_evo = f"Prochaine évolution : **{next_name}** au niveau {next_level}"
                else:
                    next_evo = "Forme finale atteinte !"

                poke_id = chain[cur_idx][2] if cur_idx >= 0 and len(chain[cur_idx]) > 2 else None
                power = power_emoji_for_level(entry["level"])

                embed = discord.Embed(
                    title=f"{entry['pokemon']} {power}",
                    description=(
                        f"Starter d'origine : {entry['starter']}\n"
                        f"Niveau : **{entry['level']}** | XP : {entry['xp']}/{xp_needed} [{bar}]\n"
                        f"{next_evo}"
                    ),
                    color=discord.Color.green()
                )

                if poke_id:
                    embed.set_thumbnail(url=pokemon_artwork_url(poke_id))

                embed.set_footer(text="Utilise /starter pour plus de détails.")
                await interaction.response.send_message(embed=embed)
                return

            lines = ["**Choisis ton starter ! Utilise `/choose_starter <nom>`**\n"]

            all_chains = [chain for chains in STARTERS.values() for chain in chains]
            all_names = [chain[0][0] for chain in all_chains]

            max_len = max(len(name) for name in all_names)

            for gen, chains in STARTERS.items():
                row_parts = []

                for i, chain in enumerate(chains):
                    name = chain[0][0]
                    url = pokepedia_url(name)
                    emoji = POKEMON_TYPES[i % 3]

                    padded = name.ljust(max_len)

                    row_parts.append(f"[{emoji} {padded}](<{url}>)")

                row = "   ".join(row_parts)

                lines.append(f"**{gen}** : {row}")

            await interaction.response.send_message("\n".join(lines))
            return

        # ───── Choix ─────
        if entry:
            await interaction.response.send_message(
                f"Tu as déjà **{entry['pokemon']}** !",
                ephemeral=True
            )
            return

        choix_clean = choix.strip().lower()
        found_chain = None
        starter_type = None

        for gen in STARTERS.values():
            for i, chain in enumerate(gen):
                if str(chain[0][0]).strip().lower() == choix_clean:
                    found_chain = chain
                    starter_type = POKEMON_TYPES[i]
                    break
            if found_chain:
                break

        if not found_chain:
            await interaction.response.send_message(
                f"**{choix}** n'est pas un starter valide.",
                ephemeral=True
            )
            return

        self.pokemon_data.setdefault(guild_id, {})[user_id] = {
            "starter": found_chain[0][0],
            "pokemon": found_chain[0][0],
            "level": 1,
            "xp": 0,
            "last_time": DEFAULT.get("last_time"),
            "HP": DEFAULT.get("HP"),
            "type": starter_type,
            "wins": DEFAULT.get("wins"),
            "losses": DEFAULT.get("wins"),
            "begin_date": datetime.datetime.now().replace(microsecond=0).isoformat()
        }

        save_pokemon_data(self.pokemon_data)

        poke_id = found_chain[0][2] if len(found_chain[0]) > 2 else None
        name = str(found_chain[0][0])

        embed = discord.Embed(
            title=f"🎉 {name}",
            description=f"{interaction.user.mention} a choisi **{name}** comme starter !",
            color=discord.Color.gold()
        )
        logger.info(
            f"{interaction.user.name} - {interaction.guild.name} - "
            f"A choisi son starter : {name}"
        )

        if poke_id:
            embed.set_image(url=pokemon_artwork_url(int(poke_id)))

        await interaction.response.send_message(embed=embed)

    # ───────── /delete_starter ─────────
    @app_commands.command(name="delete_starter", description="Supprimer ton starter Pokémon")
    async def delete_starter(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        entry = get_pokemon_entry(self.pokemon_data, guild_id, user_id)

        if not entry:
            await interaction.response.send_message(
                "Tu n'as pas de Pokémon à supprimer.",
                ephemeral=True
            )
            return

        view = DeleteStarterView(self, guild_id, user_id, entry)

        await interaction.response.send_message(
            f"⚠️ Tu es sur le point de supprimer **{entry['pokemon']}** "
            f"(niv. {entry['level']}).",
            view=view,
            ephemeral=True
        )

    # ───────── /starter ─────────
    @app_commands.command(
        name="starter",
        description="Afficher les détails de ton starter ou de celui d’un autre joueur"
    )
    @app_commands.describe(joueur="Joueur dont tu veux voir le starter")
    async def starter(
            self,
            interaction: discord.Interaction,
            joueur: discord.Member | None = None
    ):
        guild_id = str(interaction.guild.id)

        target = joueur or interaction.user
        user_id = str(target.id)

        entry = get_pokemon_entry(self.pokemon_data, guild_id, user_id)

        if not entry:
            if joueur is None:
                await interaction.response.send_message(
                    "Tu n'as pas encore de starter. Utilise `/choose_start <nom>`",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"**{target.display_name}** n'a pas encore de starter.",
                    ephemeral=True
                )
            return

        entry.setdefault("HP", DEFAULT.get("HP") + round(1.5 * entry["level"]))

        chain = STARTER_CHAINS.get(entry["pokemon"].lower(), [])
        xp_needed = xp_to_next_level(entry["level"])

        bar_filled = int(entry["xp"] / xp_needed * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        cur_idx = next(
            (i for i, (n, *_) in enumerate(chain) if n.lower() == entry["pokemon"].lower()),
            -1
        )

        poke_id = chain[cur_idx][2] if cur_idx >= 0 and len(chain[cur_idx]) > 2 else None
        power = power_emoji_for_level(entry["level"])

        evo_line = ""
        for name, evo_level, *_ in chain:
            marker = "▶ " if name.lower() == entry["pokemon"].lower() else "    "
            evo_line += (
                    f"\n{marker}**{name}**"
                    + (f" *(évolue niv. {evo_level})*" if evo_level else " *(forme finale)*")
            )

        embed = discord.Embed(
            title=f"{entry['pokemon']} — Niv. {entry['level']} — {power}",
            description=(
                f"Starter d'origine : {entry['starter']}\n"
                f"XP : {entry['xp']}/{xp_needed} [{bar}]\n"
                f"HP : {entry['HP']}\n"
                f"\n**Chaîne d'évolution :**{evo_line}"
            ),
            color=COLORS.get(entry["type"])
        )

        if poke_id:
            embed.set_image(url=pokemon_artwork_url(poke_id))

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="combat", description="Lancer un combat Pokémon")
    @app_commands.describe(adversaire="Joueur à défier")
    async def combat(self, interaction: discord.Interaction, adversaire: discord.Member):
        guild_id = str(interaction.guild.id)

        if adversaire.id == interaction.user.id:
            await interaction.response.send_message("Tu ne peux pas te battre contre toi-même, crétin.", ephemeral=True)
            return

        p1 = get_pokemon_entry(self.pokemon_data, guild_id, str(interaction.user.id))
        p2 = get_pokemon_entry(self.pokemon_data, guild_id, str(adversaire.id))

        if not p1:
            await interaction.response.send_message("Tu n'as même pas de starter, de quoi tu me parles ??",
                                                    ephemeral=True)
            return

        if not p2:
            await interaction.response.send_message(
                f"Choisi quelqu'un d'autre, {adversaire.mention} n'a pas de starter.", ephemeral=True)
            return

        now = int(time.time())

        last = p1.get("last_combat", 0)
        if now - last < COMBAT_COOLDOWN:
            remaining = COMBAT_COOLDOWN - (now - last)
            await interaction.response.send_message(
                f"⏳ Tu dois encore attendre **{remaining // 60} min {remaining % 60}s** avant un nouveau combat.",
                ephemeral=True
            )
            return

        view = CombatAcceptView(adversaire)

        await interaction.response.send_message(
            f"{adversaire.mention}, **{interaction.user.display_name}** te défie en combat Pokémon ! ⚔️\n-# Tu as 60 secondes pour accepter",
            view=view
        )
        logger.info(f"{interaction.guild.name} - {interaction.user.name} a demandé un combat à {adversaire.name}")

        await view.wait()

        if not view.accepted:
            await interaction.followup.send("Combat annulé !")
            return

        p1.setdefault("last_combat", now)
        p2.setdefault("last_combat", now)

        p1["last_combat"] = now
        p2["last_combat"] = now

        # Création du thread de combat
        thread = await interaction.channel.create_thread(
            name=f"⚔️ Combat — {interaction.user.display_name} vs {adversaire.display_name}",
            type=discord.ChannelType.public_thread,
            auto_archive_duration=60
        )

        await thread.send(
            f"## ⚔️ **Combat Pokémon**\n"
            f"{interaction.user.mention} vs {adversaire.mention}"
        )
        logger.info(f"{interaction.guild.name} - ⚔️ {interaction.user.name} vs {adversaire.name}")

        await self.start_combat(
            interaction=interaction,
            user1=interaction.user,
            user2=adversaire,
            p1=p1,
            p2=p2,
            thread=thread
        )

    async def start_combat(
            self,
            interaction: discord.Interaction,
            user1: discord.Member,
            user2: discord.Member,
            p1: dict,
            p2: dict,
            thread: discord.Thread
    ):
        max_hp1 = hp1 = p1["HP"]
        max_hp2 = hp2 = p2["HP"]

        for p in (p1, p2):
            p.setdefault("wins", DEFAULT.get("wins"))
            p.setdefault("losses", DEFAULT.get("losses"))

        # Qui commence
        if p1["level"] > p2["level"]:
            turn = 1
        elif p2["level"] > p1["level"]:
            turn = 2
        else:
            turn = random.choice([1, 2])

        embed = discord.Embed(
            title="⚔️ Combat Pokémon",
            description=(
                f"**{user1.display_name}** vs **{user2.display_name}**\n\n"
                f"{p1['type']} {p1['pokemon']} (Niv. {p1['level']}) — HP {p1['HP']} {p1['type']}\n"
                f"{p2['type']} {p2['pokemon']} (Niv. {p2['level']}) — HP {p2['HP']} {p2['type']}"
            ),
            color=discord.Color.red()
        )

        vs_image = generate_versus_image(p1, p2)
        vs_file = discord.File(
            vs_image,
            filename="vs.png"
        )
        embed.set_image(url="attachment://vs.png")

        await thread.send(embed=embed, file=vs_file)

        await asyncio.sleep(3)

        while hp1 > 0 and hp2 > 0:
            attacker, defender = (p1, p2) if turn == 1 else (p2, p1)
            atk_user, def_user = (user1, user2) if turn == 1 else (user2, user1)

            dmg, crit = compute_damage(attacker, defender)

            # ───── appliquer dégâts AVANT affichage ─────
            if turn == 1:
                hp2 -= dmg
                hp2 = max(0, hp2)
            else:
                hp1 -= dmg
                hp1 = max(0, hp1)

            # ───── barres de vie ─────
            bar1 = health_bar(hp1, p1["HP"])
            bar2 = health_bar(hp2, p2["HP"])

            def format_pokemon_label(pokemon_name: str, trainer: discord.Member) -> str:
                return f"{pokemon_name} de {trainer.display_name}"

            atk_label = format_pokemon_label(attacker["pokemon"], atk_user)
            def_label_1 = format_pokemon_label(p1["pokemon"], user1)
            def_label_2 = format_pokemon_label(p2["pokemon"], user2)

            msg = f"## 💥 **{atk_label}** inflige **{dmg} dégâts**"

            if crit:
                msg += "\n# ⚡ **COUP CRITIQUE !**"

            msg += (
                f"\n\n❤️ **{def_label_1}** : {hp1}/{max_hp1}HP HP\n{bar1}"
                f"\n\n❤️ **{def_label_2}** : {hp2}/{max_hp2}HP HP\n{bar2}"
            )

            await thread.send(msg)

            turn = 2 if turn == 1 else 1
            await asyncio.sleep(3)

        winner, loser, winner_user, loser_user = (p1, p2, user1, user2) if hp1 > 0 else (p2, p1, user2, user1)

        # ───── XP gain ─────
        base_xp = loser["level"] * 10
        bonus = random.randint(-5, 5)
        xp_gain = max(5, base_xp + bonus)

        winner["xp"] += xp_gain

        winner["wins"] += 1
        loser["losses"] += 1

        save_pokemon_data(self.pokemon_data)

        win_message = (
            f"🏆 **Combat terminé !**\n"
            f"🎉 Victoire du **{winner['pokemon']}** (+{xp_gain} XP) de {winner_user.mention}"
        )

        await interaction.followup.send(win_message)

        logger.info(
            f"{interaction.guild.name} - 🏆 🎉 Victoire du {winner['pokemon']} de {winner_user.name} face à {loser_user.name}")

        # ───── Level up ─────
        message = await self.level_up(winner, winner_user)

        if message and len(message):
            await thread.send(message)

        await self.evolve(winner, winner_user, interaction.channel)

        save_pokemon_data(self.pokemon_data)

        await thread.send(win_message)
        await thread.send(
            f"🔒 Le combat est terminé. Ce thread sera archivé automatiquement dans {COMBAT_COOLDOWN / 60}min.")
        await asyncio.sleep(COMBAT_COOLDOWN)
        await thread.edit(archived=True, locked=True)

    @app_commands.command(name="combatstats", description="Statistiques de combat de ton starter")
    @app_commands.describe(joueur="Voir les stats d’un autre joueur")
    async def combatstats(
            self,
            interaction: discord.Interaction,
            joueur: discord.Member | None = None
    ):
        guild_id = str(interaction.guild.id)
        target = joueur or interaction.user

        entry = get_pokemon_entry(self.pokemon_data, guild_id, str(target.id))
        if not entry:
            await interaction.response.send_message("Ce joueur n'a pas de starter.", ephemeral=True)
            return

        wins = entry.get("wins", 0)
        losses = entry.get("losses", 0)
        total = wins + losses
        ratio = (wins / total * 100) if total else 0

        embed = discord.Embed(
            title=f"📊 Stats de combat — {entry['pokemon']} {power_emoji_for_level(entry['level'])}",
            description=(
                f"🏆 Victoires : **{wins}**\n"
                f"💀 Défaites : **{losses}**\n"
                f"📈 Ratio victoire : **{ratio:.1f}%**\n"
                "\n"
                f"Niveau : {entry['level']} {power_emoji_for_level(entry['level'])}\n"
            ),
            color=discord.Color.purple()
        )

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PokemonStarterCog(bot))

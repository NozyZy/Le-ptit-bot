import io
import json
import logging
import os

# Third-party imports
import discord
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


# Load Pokémon data
def load_pokemon_data() -> dict:
    os.makedirs("data", exist_ok=True)
    try:
        with open(POKEMON_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Save Pokémon data
def save_pokemon_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(POKEMON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# calculate XP needed to level up
def xp_to_next_level(level: int) -> int:
    """XP needed to go from `level` to `level + 1`."""
    return level * 50


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


def power_emoji_for_level(level: int) -> str:
    for max_level, emoji in POWER_EMOJIS:
        if level <= max_level:
            return emoji
    return POWER_EMOJIS[-1][1]


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


class PokemonStarterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pokemon_data = bot.pokemon_data

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
            for gen, chains in STARTERS.items():
                names = " · ".join(chain[0][0] for chain in chains)
                lines.append(f"**{gen}** : {names}")

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

        for chain in (c for chains in STARTERS.values() for c in chains):
            if str(chain[0][0]).lower() == choix_clean:
                found_chain = chain
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

    # ───────── /deletestarter ─────────
    @app_commands.command(name="deletestarter", description="Supprimer ton starter Pokémon")
    async def deletestarter(self, interaction: discord.Interaction):
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

        # Par défaut → soi-même
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
                f"\n**Chaîne d'évolution :**{evo_line}"
            ),
            color=discord.Color.blue()
        )

        if poke_id:
            embed.set_image(url=pokemon_artwork_url(poke_id))

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PokemonStarterCog(bot))

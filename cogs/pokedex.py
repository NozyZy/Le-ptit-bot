import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.pokemon_starter import STARTER_CHAINS, pokepedia_url
from pokedex_logic import (
    BADGES,
    BADGES_BY_ID,
    RARITY_EMOJIS,
    CATEGORIES,
    SPECIES,
    TOTAL_BADGES,
    TOTAL_SPECIES,
    RollResult,
    caught_ids,
    get_entry,
    load_pokedex_data,
    register_daily,
    save_pokedex_data
)

logger = logging.getLogger(__name__)

POKEDEX_PAGE_SIZE = 20
POKEDEX_COLUMN_SIZE = 10

BADGE_PAGE_MAX_CHARS = 3900
PAGINATION_TIMEOUT = 120

RARITY_SCORES = {
    "bronze": 1,
    "silver": 2,
    "gold": 3,
    "diamond": 4,
    "legend": 5,
}
LEADERBOARD_PAGE_SIZE = 20

FILTER_CHOICES = [
    app_commands.Choice(name="Tous", value="all"),
    app_commands.Choice(name="Capturés", value="caught"),
    app_commands.Choice(name="Manquants", value="missing"),
    app_commands.Choice(name="Shiny", value="shiny"),
]


def format_date(iso_date: str) -> str:
    return datetime.date.fromisoformat(iso_date).strftime("%d/%m/%Y")


def dex_line(pid: int, entry: dict) -> str:
    caught = entry["caught"].get(str(pid))
    if not caught:
        return f"`#{pid:04d}` ???"
    return f"`#{pid:04d}` [{SPECIES[pid]['name']}{' ✨' if caught['shiny'] else ''}]({pokepedia_url(SPECIES[pid]['name'])})"


def badge_line(badge, entry: dict, caught: set[int]) -> str:
    earned = entry["badges"].get(badge.id)
    if earned:
        return f"{badge.emoji} **{badge.name}** — {badge.description} · {format_date(earned)}"
    if badge.secret:
        return "🔒 ??? — Badge secret"
    progress = ""
    if badge.progress:
        done, target = badge.progress(entry, caught)
        progress = f" ({done}/{target})"
    return f"🔒 {badge.name} — {badge.description}{progress}"


class PagedView(discord.ui.View):
    def __init__(self, author_id: int, pages: list[discord.Embed], start: int = 0):
        super().__init__(timeout=PAGINATION_TIMEOUT)
        self.author_id = author_id
        self.pages = pages
        self.index = start
        self.message: discord.InteractionMessage | None = None
        self.update_buttons()

    def update_buttons(self):
        self.first.disabled = self.previous.disabled = self.index == 0
        self.next.disabled = self.last.disabled = self.index == len(self.pages) - 1

    async def show(self, interaction: discord.Interaction, index: int):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Pas touche, lance ta propre commande", ephemeral=True)
            return
        self.index = index
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, _):
        await self.show(interaction, min(0, self.index - 10))

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, _):
        await self.show(interaction, self.index - 1)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, _):
        await self.show(interaction, self.index + 1)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, _):
        await self.show(interaction, min(len(self.pages) - 1, self.index + 10))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass


async def send_pages(interaction: discord.Interaction, pages: list[discord.Embed], start: int = 0):
    if len(pages) == 1:
        await interaction.response.send_message(embed=pages[0])
        return
    view = PagedView(interaction.user.id, pages, start)
    await interaction.response.send_message(embed=pages[start], view=view)
    view.message = await interaction.original_response()


class PokedexCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_pokedex_data()

    def starter_ids(self, guild_id: int, user_id: int) -> set[int]:
        starter_cog = self.bot.get_cog("PokemonStarterCog")
        if not starter_cog:
            return set()
        starter = starter_cog.pokemon_data.get(str(guild_id), {}).get(str(user_id))
        if not starter or not starter.get("pokemon"):
            return set()
        chain = STARTER_CHAINS.get(starter["pokemon"].lower(), [])
        return {form[2] for form in chain if len(form) > 2}

    def register(self, user: discord.abc.User, guild: discord.Guild, pokemon_id: int, shiny: bool,
                 today: datetime.date) -> RollResult | None:
        """Called by the daily Pokémon handler of bot.py, only for the player's own roll."""
        result = register_daily(
            self.data, str(user.id), pokemon_id, shiny, today,
            starter_ids=self.starter_ids(guild.id, user.id),
            is_guild_member=lambda uid: guild.get_member(int(uid)) is not None,
        )
        if result is not None:
            save_pokedex_data(self.data)
        for badge in result.new_badges if result else []:
            logger.info(f"{user.name} - {guild.name} - Badge débloqué : {badge.name}")
        return result

    # ───────── /pokedex ─────────
    @app_commands.command(name="pokedex", description="Affiche les Pokémon du jour que tu as capturés")
    @app_commands.describe(membre="Le Pokédex de qui ?", filtre="Quels Pokémon afficher")
    @app_commands.choices(filtre=FILTER_CHOICES)
    async def pokedex(self, interaction: discord.Interaction, membre: discord.Member | None = None,
                      filtre: app_commands.Choice[str] | None = None):
        member = membre or interaction.user
        mode = filtre.value if filtre else "all"
        entry = get_entry({}, "") if str(member.id) not in self.data else get_entry(self.data, str(member.id))
        caught = caught_ids(entry)
        shinies = {pid for pid in caught if entry["caught"][str(pid)]["shiny"]}
        color = discord.Color.ash_theme()

        ids = sorted(SPECIES)
        if mode == "caught":
            ids = sorted(caught)
            color = discord.Color.green()
        elif mode == "missing":
            ids = [pid for pid in ids if pid not in caught]
            color = discord.Color.red()
        elif mode == "shiny":
            ids = sorted(shinies)
            color = discord.Color.gold()

        header = (
            f"**{len(caught)}/{TOTAL_SPECIES}** ({len(caught) / TOTAL_SPECIES * 100:.1f} %)"
            f" · ✨ {len(shinies)} · 🏅 {len(entry['badges'])}/{TOTAL_BADGES}"
        ).replace(".", ",")
        title = f"Pokédex de {member.display_name}"
        if filtre and mode != "all":
            title += f" — {filtre.name}"

        pages = []
        chunks = [ids[i:i + POKEDEX_PAGE_SIZE] for i in range(0, len(ids), POKEDEX_PAGE_SIZE)] or [[]]
        for number, chunk in enumerate(chunks, start=1):
            embed = discord.Embed(title=title, description=header, color=color)
            embed.set_thumbnail(url=member.display_avatar.url)
            if not chunk:
                embed.add_field(name="​", value="Rien ici… pour l'instant. Écris `pokémon` pour tirer ton Pokémon du jour !")
            for start in range(0, len(chunk), POKEDEX_COLUMN_SIZE):
                column = chunk[start:start + POKEDEX_COLUMN_SIZE]
                embed.add_field(name="​", value="\n".join(dex_line(pid, entry) for pid in column), inline=True)
            embed.set_footer(text=f"Page {number}/{len(chunks)}")
            pages.append(embed)

        await send_pages(interaction, pages)

    # ───────── /badges ─────────
    @app_commands.command(name="badges", description="Affiche les badges du Pokédex")
    @app_commands.describe(membre="Les badges de qui ?", categorie="Catégorie à ouvrir")
    @app_commands.choices(categorie=[app_commands.Choice(name=c, value=c) for c in CATEGORIES])
    async def badges(self, interaction: discord.Interaction, membre: discord.Member | None = None,
                     categorie: app_commands.Choice[str] | None = None):
        member = membre or interaction.user
        entry = get_entry({}, "") if str(member.id) not in self.data else get_entry(self.data, str(member.id))
        caught = caught_ids(entry)
        header = f"🏅 **{len(entry['badges'])}/{TOTAL_BADGES}** badges"

        pages = []
        start = 0
        for category in CATEGORIES:
            if categorie and category == categorie.value:
                start = len(pages)
            lines = [badge_line(b, entry, caught) for b in BADGES if b.category == category]
            # Long categories (Régions) are split to fit in an embed
            chunk: list[str] = []
            chunks = []
            for line in lines:
                if chunk and len("\n".join(chunk + [line])) > BADGE_PAGE_MAX_CHARS:
                    chunks.append(chunk)
                    chunk = []
                chunk.append(line)
            chunks.append(chunk)
            for part, chunk in enumerate(chunks, start=1):
                suffix = f" ({part}/{len(chunks)})" if len(chunks) > 1 else ""
                earned = sum(1 for b in BADGES if b.category == category and b.id in entry["badges"])
                total = sum(1 for b in BADGES if b.category == category)
                embed = discord.Embed(
                    title=f"Badges de {member.display_name} — {category}{suffix}",
                    description=f"{header} · {category} : {earned}/{total}\n\n" + "\n".join(chunk),
                    color=discord.Color.gold(),
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                pages.append(embed)
        for number, embed in enumerate(pages, start=1):
            embed.set_footer(text=f"Page {number}/{len(pages)} · 🥉 🥈 🥇 💎 🌟 du plus courant au plus rare")

        await send_pages(interaction, pages, start)

    @app_commands.command(
        name="badge_leaderboard",
        description="Classement des dresseurs par badges"
    )
    async def badge_leaderboard(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "Cette commande doit être utilisée dans un serveur.",
                ephemeral=True,
            )
            return

        leaderboard = []

        # Score only members of this Discord server.
        for member in guild.members:
            if member.bot:
                continue

            entry = get_entry(self.data, str(member.id))
            earned_badges = entry["badges"]

            rarity_counts = {rarity: 0 for rarity in RARITY_SCORES}
            score = 0

            for badge_id in earned_badges:
                badge = BADGES_BY_ID.get(badge_id)
                if badge is None:
                    continue

                rarity = badge.rarity
                points = RARITY_SCORES.get(rarity, 0)

                score += points
                if rarity in rarity_counts:
                    rarity_counts[rarity] += 1

            if score > 0:
                leaderboard.append({
                    "member": member,
                    "score": score,
                    "rarity_counts": rarity_counts,
                    "total_badges": sum(rarity_counts.values()),
                })

        # Highest score first; break ties by total number of badges.
        leaderboard.sort(
            key=lambda item: (item["score"], item["total_badges"]),
            reverse=True,
        )

        embed = discord.Embed(
            title=f"🏆 Classement des dresseurs — {guild.name}",
            description=(
                "Chaque badge rapporte des points selon sa rareté.\n"
                "🥉 1 pt · 🥈 2 pts · 🥇 3 pts · 💎 4 pts · 🌟 5 pts"
            ),
            color=discord.Color.gold(),
        )

        if not leaderboard:
            embed.description += "\n\nAucun badge obtenu pour le moment !"
        else:
            lines = []

            for rank, item in enumerate(
                    leaderboard[:LEADERBOARD_PAGE_SIZE], start=1
            ):
                member = item["member"]
                score = item["score"]
                counts = item["rarity_counts"]

                rank_emoji = {
                    1: "🥇",
                    2: "🥈",
                    3: "🥉",
                }.get(rank, f"`#{rank}`")

                rarity_summary = " · ".join(
                    f"{RARITY_EMOJIS[rarity]} {count}"
                    for rarity, count in counts.items()
                    if count > 0
                )

                lines.append(
                    f"{rank_emoji} {member.mention} — **{score} pts**\n"
                    f"　{rarity_summary}"
                )

            embed.add_field(
                name="Classement",
                value="\n".join(lines),
                inline=False,
            )

            embed.set_footer(
                text=(
                    f"Top {min(len(leaderboard), LEADERBOARD_PAGE_SIZE)}"
                    f" / {len(leaderboard)} membres classés"
                )
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PokedexCog(bot))

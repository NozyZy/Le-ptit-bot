"""Pokédex and badges of the daily Pokémon (see docs/specs/pokedex.md).

No discord import here, so the rules can be unit-tested on their own.
"""
import datetime
import json
import math
from dataclasses import dataclass, field
from typing import Callable

from storage import atomic_write_json, load_json_safely

POKEDEX_DATA_FILE = "data/pokedex.json"
SPECIES_FILE = "database/pokemon/species.json"
STARTERS_FILE = "database/pokemon/starters.json"


def _load_species() -> dict[int, dict]:
    with open(SPECIES_FILE, "r", encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}


SPECIES = _load_species()
TOTAL_SPECIES = len(SPECIES)

# Evolution families with at least 2 members (single Pokémon don't count as a family)
FAMILIES: dict[int, set[int]] = {}
for _pid, _sp in SPECIES.items():
    FAMILIES.setdefault(_sp["family"], set()).add(_pid)
FAMILIES = {fam: ids for fam, ids in FAMILIES.items() if len(ids) > 1}


def _stage(pid: int) -> int:
    stage = 1
    while SPECIES[pid]["from"]:
        pid = SPECIES[pid]["from"]
        stage += 1
    return stage


FAMILY_STAGES = {fam: max(_stage(pid) for pid in ids) for fam, ids in FAMILIES.items()}
EEVEE_FAMILY = SPECIES[133]["family"]

GEN_SIZES: dict[int, int] = {}
for _sp in SPECIES.values():
    GEN_SIZES[_sp["gen"]] = GEN_SIZES.get(_sp["gen"], 0) + 1

REGIONS = {1: "Kanto", 2: "Johto", 3: "Hoenn", 4: "Sinnoh", 5: "Unys",
           6: "Kalos", 7: "Alola", 8: "Galar", 9: "Paldea"}

TYPE_NAMES = {
    "normal": "Normal", "combat": "Combat", "vol": "Vol", "poison": "Poison", "sol": "Sol",
    "roche": "Roche", "insecte": "Insecte", "spectre": "Spectre", "acier": "Acier",
    "feu": "Feu", "eau": "Eau", "plante": "Plante", "electrik": "Électrik", "psy": "Psy",
    "glace": "Glace", "dragon": "Dragon", "tenebres": "Ténèbres", "fee": "Fée",
}

LEGENDARIES = {pid for pid, sp in SPECIES.items() if sp["legendary"]}
MYTHICALS = {pid for pid, sp in SPECIES.items() if sp["mythical"]}
BABIES = {pid for pid, sp in SPECIES.items() if sp["baby"]}


def _load_starter_families() -> set[int]:
    with open(STARTERS_FILE, "r", encoding="utf-8") as f:
        starters = json.load(f)
    return {SPECIES[chain[0][2]]["family"] for chains in starters.values() for chain in chains}


STARTER_FAMILIES = _load_starter_families()

ENTRY_DEFAULTS = {
    "caught": {},
    "last_roll": None,
    "last_roll_id": None,
    "streak": 0,
    "best_streak": 0,
    "days": 0,
    "badges": {},
    # Badges earned through someone else's roll (Jumeaux), announced on the next own roll
    "pending_badges": [],
}


# ── Storage ───────────────────────────────────────────────────────────────────

def load_pokedex_data() -> dict:
    data = load_json_safely(POKEDEX_DATA_FILE, default={})
    if not isinstance(data, dict):
        return {}
    return data


def save_pokedex_data(data: dict) -> None:
    atomic_write_json(POKEDEX_DATA_FILE, data, backup=True, ensure_ascii=False, indent=2)


def get_entry(data: dict, user_id: str) -> dict:
    entry = data.setdefault(user_id, {})
    for key, default in ENTRY_DEFAULTS.items():
        if key not in entry:
            entry[key] = type(default)(default) if isinstance(default, (dict, list)) else default
    return entry


def caught_ids(entry: dict) -> set[int]:
    return {int(pid) for pid in entry.get("caught", {})}


# ── Badges ────────────────────────────────────────────────────────────────────

RARITY_EMOJIS = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "diamond": "💎", "legend": "🌟"}

CATEGORIES = ["Pokédex", "Évolutions", "Régions", "Types", "Raretés", "Assiduité", "Secrets"]


@dataclass
class BadgeContext:
    """What a badge can look at when today's Pokémon has just been registered."""
    entry: dict
    caught: set[int]
    pokemon_id: int
    # Yesterday's roll, None if the player did not roll yesterday
    yesterday_id: int | None = None
    twin: bool = False
    # Every stage of the player's starter on the server where they roll
    starter_ids: set[int] = field(default_factory=set)


@dataclass
class Badge:
    id: str
    name: str
    description: str
    category: str
    rarity: str
    check: Callable[[BadgeContext], bool]
    progress: Callable[[dict, set[int]], tuple[int, int]] | None = None
    secret: bool = False

    @property
    def emoji(self) -> str:
        return RARITY_EMOJIS[self.rarity]


def completed_families(caught: set[int], stages: int | None = None) -> int:
    return sum(
        1 for fam, ids in FAMILIES.items()
        if ids <= caught and (stages is None or FAMILY_STAGES[fam] == stages)
    )


def gen_count(caught: set[int], gen: int) -> int:
    return sum(1 for pid in caught if SPECIES[pid]["gen"] == gen)


def type_count(caught: set[int], type_: str) -> int:
    return sum(1 for pid in caught if type_ in SPECIES[pid]["types"])


def _count_badge(id_, name, description, category, rarity, counter, target, secret=False):
    return Badge(
        id=id_, name=name, description=description, category=category, rarity=rarity,
        check=lambda ctx: counter(ctx.entry, ctx.caught) >= target,
        progress=lambda entry, caught: (min(counter(entry, caught), target), target),
        secret=secret,
    )


def _build_badges() -> list[Badge]:
    badges: list[Badge] = []

    def caught_count(entry, caught):
        return len(caught)

    # Pokédex
    for target, id_, name, rarity in [
        (1, "dex_1", "Premier pas", "bronze"),
        (10, "dex_10", "Collectionneur en herbe", "bronze"),
        (25, "dex_25", "Sac à dos plein", "bronze"),
        (50, "dex_50", "Demi-centaine", "bronze"),
        (100, "dex_100", "Centurion", "silver"),
        (151, "dex_151", "Le Prof. Chen serait fier", "silver"),
        (250, "dex_250", "Quart de Pokédex", "gold"),
        (500, "dex_500", "À mi-chemin (ou presque)", "diamond"),
    ]:
        what = "ton premier Pokémon" if target == 1 else f"{target} Pokémon différents"
        badges.append(_count_badge(id_, name, f"Capturer {what}", "Pokédex", rarity, caught_count, target))
    badges.append(_count_badge("dex_all", "Attrapez-les tous", f"Compléter le Pokédex ({TOTAL_SPECIES} Pokémon)",
                               "Pokédex", "legend", caught_count, TOTAL_SPECIES))

    # Évolutions
    def families(entry, caught):
        return completed_families(caught)

    def trilogies(entry, caught):
        return completed_families(caught, stages=3)

    def eevee(entry, caught):
        return len(FAMILIES[EEVEE_FAMILY] & caught)

    for target, id_, name, rarity in [
        (1, "family_1", "Famille réunie", "silver"),
        (5, "family_5", "Arbre généalogique", "silver"),
        (10, "family_10", "Réunion de famille", "gold"),
        (25, "family_25", "Généalogiste", "gold"),
        (50, "family_50", "Patriarche", "diamond"),
    ]:
        what = "une lignée d'évolution complète" if target == 1 else f"{target} lignées d'évolution complètes"
        badges.append(_count_badge(id_, name, f"Avoir {what}", "Évolutions", rarity, families, target))
    badges.append(_count_badge("trilogy_1", "Trilogie", "Compléter une lignée à 3 stades",
                               "Évolutions", "gold", trilogies, 1))
    badges.append(_count_badge("trilogy_5", "Saga", "Compléter 5 lignées à 3 stades",
                               "Évolutions", "gold", trilogies, 5))
    badges.append(Badge(
        "heir", "Héritier", "Compléter la lignée d'un starter", "Évolutions", "gold",
        check=lambda ctx: any(FAMILIES[fam] <= ctx.caught for fam in STARTER_FAMILIES),
    ))
    badges.append(_count_badge("eevee", "Évolimaniaque", "Capturer Évoli et ses 8 évolutions",
                               "Évolutions", "legend", eevee, len(FAMILIES[EEVEE_FAMILY])))
    badges.append(Badge(
        "live_evolution", "En direct du labo", "Tirer l'évolution du Pokémon tiré la veille",
        "Évolutions", "diamond", secret=True,
        check=lambda ctx: ctx.yesterday_id is not None
        and SPECIES[ctx.pokemon_id]["from"] == ctx.yesterday_id,
    ))

    # Régions
    for gen, region in REGIONS.items():
        size = GEN_SIZES[gen]
        counter = (lambda g: lambda entry, caught: gen_count(caught, g))(gen)
        for percent, title, rarity in [
            (25, "Explorateur", "gold"),
            (50, "Dresseur", "diamond"),
            (75, "Champion", "diamond"),
            (100, "Maître", "legend"),
        ]:
            target = math.ceil(size * percent / 100)
            badges.append(_count_badge(
                f"region_{gen}_{percent}", f"{title} de {region}",
                f"Capturer {percent} % des Pokémon de {region} ({target}/{size})",
                "Régions", rarity, counter, target,
            ))
    badges.append(_count_badge(
        "globetrotter", "Globe-trotter", "Capturer au moins un Pokémon de chaque région",
        "Régions", "bronze",
        lambda entry, caught: len({SPECIES[pid]["gen"] for pid in caught}), len(REGIONS),
    ))

    # Types
    for type_, type_name in TYPE_NAMES.items():
        counter = (lambda t: lambda entry, caught: type_count(caught, t))(type_)
        badges.append(_count_badge(
            f"type_{type_}", f"Spécialiste {type_name}", f"Capturer 10 Pokémon de type {type_name}",
            "Types", "gold" if type_ == "glace" else "silver", counter, 10,
        ))
    badges.append(_count_badge(
        "rainbow", "Arc-en-ciel", "Capturer au moins un Pokémon de chacun des 18 types", "Types", "bronze",
        lambda entry, caught: len({t for pid in caught for t in SPECIES[pid]["types"]}), len(TYPE_NAMES),
    ))

    # Raretés
    def among(group):
        return lambda entry, caught: len(group & caught)

    for id_, name, description, rarity, group, target in [
        ("legendary_1", "Légende vivante", "Capturer un Pokémon légendaire", "bronze", LEGENDARIES, 1),
        ("mythical_1", "Mythe ou réalité ?", "Capturer un Pokémon fabuleux", "bronze", MYTHICALS, 1),
        ("baby_1", "Nounou", "Capturer un bébé Pokémon", "bronze", BABIES, 1),
        ("legendary_10", "Panthéon", "Capturer 10 Pokémon légendaires", "silver", LEGENDARIES, 10),
        ("mythical_5", "Chasseur de mythes", "Capturer 5 Pokémon fabuleux", "gold", MYTHICALS, 5),
        ("legendary_25", "Olympe", "Capturer 25 Pokémon légendaires", "gold", LEGENDARIES, 25),
        ("baby_all", "Crèche complète", f"Capturer les {len(BABIES)} bébés Pokémon", "legend",
         BABIES, len(BABIES)),
        ("legendary_all", "Tous les légendaires", f"Capturer les {len(LEGENDARIES)} Pokémon légendaires",
         "legend", LEGENDARIES, len(LEGENDARIES)),
    ]:
        badges.append(_count_badge(id_, name, description, "Raretés", rarity, among(group), target))
    badges.append(Badge(
        "shiny", "✨ Ça brille !", "Capturer un Pokémon shiny", "Raretés", "legend",
        check=lambda ctx: any(c.get("shiny") for c in ctx.entry["caught"].values()),
    ))

    # Assiduité
    def best_streak(entry, caught):
        return entry["best_streak"]

    def days(entry, caught):
        return entry["days"]

    for target, id_, name, rarity in [
        (3, "streak_3", "Ponctuel", "bronze"),
        (7, "streak_7", "Une semaine sans faute", "bronze"),
        (30, "streak_30", "Habitué", "silver"),
        (100, "streak_100", "Accro (et alors ?)", "gold"),
        (365, "streak_365", "Un an sans rater un jour", "diamond"),
    ]:
        badges.append(_count_badge(id_, name, f"Tirer son Pokémon {target} jours d'affilée",
                                   "Assiduité", rarity, best_streak, target))
    for target, id_, name, rarity in [
        (30, "days_30", "Fidèle", "silver"),
        (100, "days_100", "Pilier", "gold"),
        (365, "days_365", "Vétéran", "diamond"),
    ]:
        badges.append(_count_badge(id_, name, f"Tirer son Pokémon {target} jours au total",
                                   "Assiduité", rarity, days, target))

    # Secrets
    badges.append(Badge(
        "deja_vu", "Déjà vu", "Tirer le même Pokémon pour la 3e fois", "Secrets", "silver", secret=True,
        check=lambda ctx: ctx.entry["caught"][str(ctx.pokemon_id)]["count"] >= 3,
    ))
    badges.append(Badge(
        "irony", "Ironie du sort", "Tirer un Pokémon de la lignée de ton starter", "Secrets", "gold",
        secret=True, check=lambda ctx: ctx.pokemon_id in ctx.starter_ids,
    ))
    badges.append(Badge(
        "twins", "Jumeaux", "Tirer le même Pokémon le même jour qu'un autre membre du serveur",
        "Secrets", "gold", secret=True, check=lambda ctx: ctx.twin,
    ))
    badges.append(Badge(
        "alpha_omega", "Alpha et Oméga", f"Capturer le n°1 et le n°{TOTAL_SPECIES}", "Secrets", "diamond",
        secret=True, check=lambda ctx: {1, TOTAL_SPECIES} <= ctx.caught,
    ))

    return badges


BADGES = _build_badges()
BADGES_BY_ID = {badge.id: badge for badge in BADGES}
TOTAL_BADGES = len(BADGES)


# ── Daily roll ────────────────────────────────────────────────────────────────

@dataclass
class RollResult:
    is_new: bool
    count: int
    total_caught: int
    total_badges: int
    new_badges: list[Badge]


def register_daily(
        data: dict,
        user_id: str,
        pokemon_id: int,
        shiny: bool,
        today: datetime.date,
        starter_ids: set[int] | None = None,
        is_guild_member: Callable[[str], bool] = lambda uid: False,
) -> RollResult | None:
    """Register the player's own daily Pokémon. Returns None for an id unknown to the Pokédex.

    Asking again the same day changes nothing: only the first roll of the day counts.
    """
    if pokemon_id not in SPECIES:
        return None

    entry = get_entry(data, user_id)
    today_str = today.isoformat()
    key = str(pokemon_id)
    new_badges: list[Badge] = []

    if entry["last_roll"] != today_str:
        yesterday_str = (today - datetime.timedelta(days=1)).isoformat()
        rolled_yesterday = entry["last_roll"] == yesterday_str
        yesterday_id = entry["last_roll_id"] if rolled_yesterday else None

        entry["streak"] = entry["streak"] + 1 if rolled_yesterday else 1
        entry["best_streak"] = max(entry["best_streak"], entry["streak"])
        entry["days"] += 1
        entry["last_roll"] = today_str
        entry["last_roll_id"] = pokemon_id

        caught = entry["caught"].setdefault(key, {"count": 0, "first": today_str, "shiny": False})
        caught["count"] += 1
        caught["last"] = today_str
        caught["shiny"] = caught["shiny"] or shiny

        twins = [
            uid for uid, other in data.items()
            if uid != user_id and other.get("last_roll") == today_str
            and other.get("last_roll_id") == pokemon_id and is_guild_member(uid)
        ]
        for uid in twins:
            other = get_entry(data, uid)
            if "twins" not in other["badges"]:
                other["badges"]["twins"] = today_str
                other["pending_badges"].append("twins")

        ctx = BadgeContext(
            entry=entry, caught=caught_ids(entry), pokemon_id=pokemon_id,
            yesterday_id=yesterday_id, twin=bool(twins), starter_ids=starter_ids or set(),
        )
        for badge_id in entry["pending_badges"]:
            if badge_id in BADGES_BY_ID:
                new_badges.append(BADGES_BY_ID[badge_id])
        entry["pending_badges"] = []
        for badge in BADGES:
            if badge.id not in entry["badges"] and badge.check(ctx):
                entry["badges"][badge.id] = today_str
                new_badges.append(badge)

    caught = entry["caught"].get(key)
    return RollResult(
        # A second roll the same day after a cache update (different Pokémon) is not registered
        is_new=caught is not None and caught["first"] == today_str,
        count=caught["count"] if caught else 0,
        total_caught=len(entry["caught"]),
        total_badges=len(entry["badges"]),
        new_badges=new_badges,
    )

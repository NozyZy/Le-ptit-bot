"""Build database/pokemon/species.json from the PokeAPI CSV dumps.

Usage: python scripts/build_species.py

Run again when a new generation comes out. The output is committed, so the bot
never downloads it at runtime.
"""
import csv
import io
import json
import os

import requests

CSV_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/{}.csv"
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "database", "pokemon", "species.json")
FRENCH_LANGUAGE_ID = "5"

# Same keys as the type colors of the daily Pokémon embed in bot.py
FRENCH_TYPES = {
    "normal": "normal", "fighting": "combat", "flying": "vol", "poison": "poison",
    "ground": "sol", "rock": "roche", "bug": "insecte", "ghost": "spectre",
    "steel": "acier", "fire": "feu", "water": "eau", "grass": "plante",
    "electric": "electrik", "psychic": "psy", "ice": "glace", "dragon": "dragon",
    "dark": "tenebres", "fairy": "fee",
}


def fetch_csv(name: str) -> list[dict]:
    resp = requests.get(CSV_URL.format(name), timeout=30)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def main():
    species = fetch_csv("pokemon_species")
    type_names = {row["id"]: FRENCH_TYPES[row["identifier"]] for row in fetch_csv("types")
                  if row["identifier"] in FRENCH_TYPES}
    french_names = {row["pokemon_species_id"]: row["name"] for row in fetch_csv("pokemon_species_names")
                    if row["local_language_id"] == FRENCH_LANGUAGE_ID}

    ids = {row["id"] for row in species}
    types: dict[str, list[tuple[int, str]]] = {}
    # pokemon_id == species id for default forms; alternate forms have ids above 10000
    for row in fetch_csv("pokemon_types"):
        if row["pokemon_id"] in ids:
            types.setdefault(row["pokemon_id"], []).append((int(row["slot"]), type_names[row["type_id"]]))

    out = {}
    for row in sorted(species, key=lambda r: int(r["id"])):
        out[row["id"]] = {
            "name": french_names.get(row["id"], row["identifier"].capitalize()),
            "gen": int(row["generation_id"]),
            "family": int(row["evolution_chain_id"]),
            "from": int(row["evolves_from_species_id"]) if row["evolves_from_species_id"] else None,
            "types": [t for _, t in sorted(types[row["id"]])],
            "legendary": row["is_legendary"] == "1",
            "mythical": row["is_mythical"] == "1",
            "baby": row["is_baby"] == "1",
        }

    # One species per line: readable diffs without a 5000-line file
    lines = [f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in out.items()]
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("{\n" + ",\n".join(lines) + "\n}\n")
    print(f"{len(out)} espèces écrites dans {os.path.normpath(OUTPUT)}")


if __name__ == "__main__":
    main()

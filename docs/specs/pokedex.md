# Spec : Pokédex — « Attrapez-les tous »

Statut : **v2, décisions intégrées, catalogue de badges à valider avant dev**

## 1. Contexte

Aujourd'hui, écrire `pokémon` (ou `pokemon`, `pokémon ?`…) dans un salon déclenche le
**Pokémon du jour** (`bot.py`, handler `on_message`, bloc `re.fullmatch(r"pok[eé]mon…")`) :

- Le Pokémon est tiré dans `ALL_POKEMONS` (cache Tyradex, `data/pokemon_cache.json`)
  avec une graine `hash((user.id, jour_de_l_année, année))`. Il est donc **le même toute la
  journée pour un utilisateur donné**, quel que soit le serveur.
- 1 chance sur 8193 d'être shiny (`rng.randint(0, 8192) == 0`).
- `pokémon @machin` affiche le Pokémon du jour **de la personne mentionnée**.
- **Rien n'est sauvegardé.**

Demande : garder cette feature, **sauvegarder les Pokémon capturés** dans un Pokédex
consultable, et ajouter un **système de badges/succès**.

## 2. Décisions

| # | Sujet | Décision |
|---|-------|----------|
| D1 | Que compte-t-on ? | **Seuls les Pokémon que tu tires toi-même** (`pokémon` sans mention ou en te mentionnant). Regarder celui d'un autre n'enregistre rien, pour personne. Pas de notion de « vu ». |
| D2 | Mécanique de tirage | **Inchangée** : 1 Pokémon par jour. |
| D3 | Historique | **On part de zéro**, pas de rattrapage des jours passés. |
| D4 | Pagination `/pokedex` | **20 Pokémon par page, en 2 colonnes de 10.** |
| D5 | Récompenses | **Badges/succès** (remplace l'idée d'annonce publique). Catalogue au §6. |
| D6 | Portée | Pokédex **global par utilisateur** (le tirage ne dépend pas du serveur). |

## 3. Comportement

### 3.1 Capture

Quand quelqu'un tire son propre Pokémon du jour :

- Ajouté au Pokédex s'il n'y est pas.
- Shiny : flag `shiny` passé à `true` sur l'entrée (jamais repassé à `false`).
- `count` (nombre de fois tiré) incrémenté **au plus une fois par jour** : redemander le même jour
  ne change rien, ni pour le Pokédex ni pour les badges.
- Les badges sont évalués juste après (voir §5).

### 3.2 Retour dans l'embed existant

Uniquement pour son propre Pokémon :

- Nouveau : `🆕 Nouveau ! Ajouté à ton Pokédex.` — sinon : `Déjà capturé (x fois)`.
- Badge(s) débloqué(s) ce jour-là : `🏅 Badge débloqué : 🥇 **Trilogie** — Compléter une lignée à 3 stades`
  (une ligne par badge, champ d'embed dédié).
- Footer : `Pokédex : 42/1025 · 🏅 12/96 | Reviens demain…`

### 3.3 `/pokedex [membre] [filtre]`

- `membre` : défaut = soi. `filtre` : `tous` (défaut), `capturés`, `manquants`, `shiny`.
- En-tête : `Pokédex de X — 42/1025 (4,1 %) · ✨ 1 · 🏅 12/96`
- Page : **20 entrées, 2 champs d'embed inline de 10 lignes** (`#025 Pikachu ✨` ; manquant :
  `#026 ???`). Avec ~1025 Pokémon, ça fait 52 pages en filtre `tous`.
- Boutons ⏮️ ◀️ ▶️ ⏭️, timeout 2 min, seul l'auteur de la commande peut paginer
  (même style que les `discord.ui.View` de `cogs/pokemon_starter.py`).

### 3.4 `/badges [membre] [categorie]`

- Liste des badges par catégorie (§6), 1 page par catégorie, mêmes boutons.
- Badge obtenu : `🥇 **Trilogie** — Compléter une lignée à 3 stades · 12/03/2027`
- Badge visible pas encore obtenu : `🔒 Trilogie — Compléter une lignée à 3 stades (0/1)`,
  avec la progression quand elle a un sens (ex. `Centurion (42/100)`).
- Badge **secret** pas encore obtenu : `🔒 ??? — Badge secret`.

## 4. Données

### 4.1 Référentiel des espèces (nouveau, statique)

Les badges ont besoin de la génération, de la famille d'évolution, des types et du statut
légendaire/fabuleux/bébé. Le cache actuel ne contient que `name`, `id`, `image`,
`shiny_image` et **le premier type seulement**.

**Proposition** : un fichier versionné `database/pokemon/species.json` (comme `starters.json`),
généré une fois par un script `scripts/build_species.py` à partir des CSV de PokeAPI
(`pokemon_species.csv`, `pokemon_types.csv`, `types.csv` sur
`raw.githubusercontent.com/PokeAPI/pokeapi`). J'ai vérifié que ces CSV sont accessibles et
contiennent 1025 espèces.

```json
{ "133": { "gen": 1, "family": 67, "from": null, "types": ["normal"],
           "legendary": false, "mythical": false, "baby": false } }
```

- Clé = numéro national, identique au `pokedex_id` de Tyradex (à contrôler par un test qui
  compare les deux listes d'IDs).
- Types traduits en français pour coller aux clés de couleurs existantes (`eau`, `feu`, …).
- Pourquoi pas Tyradex : le modèle `Pokemon` de la lib lit la clé `evolutions` ; je n'ai pas
  pu vérifier que l'API renvoie bien cette clé (réseau vers tyradex.app bloqué ici). Les CSV
  PokeAPI évitent la question et ne coûtent aucun appel réseau au démarrage.

### 4.2 Sauvegarde joueur

`data/pokedex.json` (déjà couvert par `data/` dans `.gitignore`), via `atomic_write_json(...,
backup=True)` / `load_json_safely`, comme `data/pokemon_starters.json`.

```json
{
  "302102401324679168": {
    "caught": {
      "25": { "count": 3, "first": "2026-10-07", "last": "2026-11-02", "shiny": false }
    },
    "last_roll": "2026-11-02",
    "last_roll_id": 25,
    "streak": 4,
    "best_streak": 12,
    "days": 57,
    "badges": { "first_catch": "2026-10-07", "trilogy": "2027-03-12" }
  }
}
```

- `last_roll`, `last_roll_id`, `streak`, `best_streak`, `days` servent aux badges
  d'assiduité et aux badges « veille / jour même » (§6.7).
- `badges` stocke la date d'obtention. Un badge obtenu n'est **jamais retiré**, même si le
  référentiel change.
- La plupart des badges sont des fonctions pures de `caught`. Ajouter un badge plus tard
  l'attribue rétroactivement au prochain tirage de chaque joueur (sans annonce de masse :
  annoncé au prochain tirage, comme les autres).

## 5. Implémentation proposée

- Nouveau cog `cogs/pokedex.py`, chargé dans `main()` à côté de `cogs.pokemon_starter` :
  stockage, `/pokedex`, `/badges`, Views de pagination.
- `cogs/pokedex_badges.py` (ou un module `pokedex/badges.py`) : catalogue déclaratif, chaque
  badge = `id`, nom, description, catégorie, rareté, `secret`, et une fonction
  `check(state, ctx) -> bool` + optionnellement `progress(state) -> (n, total)`.
- `bot.py` : extraire le tirage dans une fonction pure `daily_pokemon(user_id, today)` ;
  le handler appelle `register_daily(user_id, guild, pokemon_id, shiny, today)` qui renvoie
  `is_new`, `count`, `total`, `new_badges`.
- Enregistrement dans un `try/except` : si le Pokédex plante, le Pokémon du jour s'affiche
  quand même (log d'erreur).
- Pas de nouvelle dépendance. Tests unitaires sur le tirage, l'enregistrement (idempotence
  sur la journée) et chaque `check` de badge.

## 6. Catalogue de badges

**96 badges.** Rareté attribuée selon le temps **médian** pour l'obtenir avec 1 tirage/jour
tous les jours, estimé par simulation (300 joueurs simulés, données PokeAPI, 1025 espèces).
Les badges d'assiduité et sociaux dépendent du joueur, pas du hasard : rareté fixée à la main.

| Rareté | Médiane | |
|---|---|---|
| 🥉 Bronze | < 2 mois | pour accrocher les nouveaux |
| 🥈 Argent | 2 – 6 mois | |
| 🥇 Or | 6 – 18 mois | |
| 💎 Diamant | 1,5 – 5 ans | |
| 🌟 Légende | > 5 ans | quasi impossible, c'est assumé |

### 6.1 Progression du Pokédex (9)

| Badge | Condition | Médiane | Rareté |
|---|---|---|---|
| Premier pas | 1er Pokémon capturé | 1 j | 🥉 |
| Collectionneur en herbe | 10 Pokémon | 10 j | 🥉 |
| Sac à dos plein | 25 Pokémon | 25 j | 🥉 |
| Demi-centaine | 50 Pokémon | 51 j | 🥉 |
| Centurion | 100 Pokémon | 3,5 mois | 🥈 |
| Le Prof. Chen serait fier | 151 Pokémon | 5,4 mois | 🥈 |
| Quart de Pokédex | 250 Pokémon | 9,5 mois | 🥇 |
| À mi-chemin (ou presque) | 500 Pokémon | 23 mois | 💎 |
| Attrapez-les tous | 1025 Pokémon (tout le Pokédex) | ~20 ans | 🌟 |

### 6.2 Évolutions (10)

« Lignée » = toute la famille d'évolution (ex. Bulbizarre / Herbizarre / Florizarre).
Les Pokémon sans évolution (199 familles d'un seul membre) ne comptent pas.

| Badge | Condition | Médiane | Rareté |
|---|---|---|---|
| Famille réunie | 1 lignée complète | 2 mois | 🥈 |
| Arbre généalogique | 5 lignées complètes | 5,5 mois | 🥈 |
| Trilogie | 1 lignée **à 3 stades** complète | 6,8 mois | 🥇 |
| Réunion de famille | 10 lignées complètes | 7,8 mois | 🥇 |
| Héritier | Lignée complète d'un starter (n'importe lequel des 27) | 12 mois | 🥇 |
| Généalogiste | 25 lignées complètes | 13 mois | 🥇 |
| Saga | 5 lignées à 3 stades complètes | 14 mois | 🥇 |
| Patriarche | 50 lignées complètes | 19 mois | 💎 |
| Évolimaniaque | Évoli + ses 8 évolutions | ~7,4 ans | 🌟 |
| *(secret)* En direct du labo | Tirer l'évolution directe du Pokémon tiré **la veille** | ~4 ans (18 %/an) | 💎 |

### 6.3 Régions (37)

Pour chacune des 9 générations — Kanto (151), Johto (100), Hoenn (135), Sinnoh (107),
Unys (156), Kalos (72), Alola (88), Galar (96), Paldea (120) — 4 paliers :

| Badge | Condition | Médiane | Rareté |
|---|---|---|---|
| Explorateur de {région} | 25 % de la génération | ~10 mois | 🥇 |
| Dresseur de {région} | 50 % | ~2 ans | 💎 |
| Champion de {région} | 75 % | ~3,9 ans | 💎 |
| Maître de {région} | 100 % | 13 à 15 ans | 🌟 |

Le temps est quasiment le même pour toutes les régions : il dépend du pourcentage, pas de
la taille. **« Génération complète » est donc en pratique inatteignable** avec 1 tirage/jour,
d'où les paliers intermédiaires.

+ **Globe-trotter** : au moins 1 Pokémon de chaque génération (médiane 25 j, 🥉).

### 6.4 Types (19)

| Badge | Condition | Médiane | Rareté |
|---|---|---|---|
| Spécialiste {type} (×18) | 10 Pokémon ayant ce type (1er ou 2e type) | 2,2 mois (Eau) à 7,5 mois (Glace) | 🥈 / 🥇 |
| Arc-en-ciel | Au moins 1 Pokémon de chacun des 18 types | 45 j | 🥉 |

Rareté par type : 🥈 si médiane ≤ 6 mois (17 types), 🥇 sinon (Glace, 7,5 mois).

### 6.5 Raretés (9)

| Badge | Condition | Médiane | Rareté |
|---|---|---|---|
| Légende vivante | 1 légendaire (71 au total) | 10 j | 🥉 |
| Mythe ou réalité ? | 1 fabuleux (23 au total) | 35 j | 🥉 |
| Nounou | 1 bébé Pokémon (19 au total) | 41 j | 🥉 |
| Panthéon | 10 légendaires | 5 mois | 🥈 |
| Chasseur de mythes | 5 fabuleux | 7,8 mois | 🥇 |
| Olympe | 25 légendaires | 14,5 mois | 🥇 |
| Crèche complète | Les 19 bébés | ~9 ans | 🌟 |
| Tous les légendaires | Les 71 légendaires | ~13 ans | 🌟 |
| ✨ Ça brille ! | 1 shiny (1/8193 par jour) | ~15,5 ans | 🌟 |

### 6.6 Assiduité (8)

Jours calendaires selon l'horloge du serveur qui fait tourner le bot (même date que le
tirage). Un jour manqué remet la série à 0.

| Badge | Condition | Rareté |
|---|---|---|
| Ponctuel | Série de 3 jours | 🥉 |
| Une semaine sans faute | Série de 7 jours | 🥉 |
| Habitué | Série de 30 jours | 🥈 |
| Accro (et alors ?) | Série de 100 jours | 🥇 |
| Un an sans rater un jour | Série de 365 jours | 💎 |
| Fidèle | 30 jours de tirage au total | 🥈 |
| Pilier | 100 jours au total | 🥇 |
| Vétéran | 365 jours au total | 💎 |

### 6.7 Fun / secrets (4)

| Badge | Condition | Estimation | Rareté |
|---|---|---|---|
| *(secret)* Déjà vu | Tirer le même Pokémon pour la 3e fois | médiane 6 mois | 🥈 |
| *(secret)* Ironie du sort | Tirer un Pokémon de la lignée de **ton starter** (cog starter) sur le serveur où tu tires | médiane ~8 mois | 🥇 |
| *(secret)* Jumeaux | Tirer le même Pokémon le même jour qu'un autre membre du serveur | ~1 fois / 2 ans par joueur avec 10 joueurs actifs | 🥇 |
| *(secret)* Alpha et Oméga | Avoir capturé #0001 et #1025 | médiane 3,6 ans | 💎 |

Notes :
- « Jumeaux » : vérifié au moment du tirage contre les `last_roll`/`last_roll_id` des autres
  membres du serveur. Les deux joueurs le débloquent (le premier sera notifié à son prochain
  tirage). Probabilité par jour ≈ (k−1)/1025 pour k joueurs actifs ce jour-là.
- « Ironie du sort » lit `data/pokemon_starters.json` (starter par serveur) : seul badge qui
  dépend du serveur où on tire.

**Total : 9 + 10 + 37 + 19 + 9 + 8 + 4 = 96 badges**, dont 5 secrets.

## 7. Risques / points relevés dans le code

- **R1 — 1 tirage/jour = progression très lente sur la fin.** Attendu : ~307 Pokémon distincts
  après 1 an, ~673 après 3 ans, tout le Pokédex en ~21 ans en moyenne. C'est accepté (D2) ;
  les badges sont calibrés pour qu'il y ait toujours quelque chose à débloquer dans les
  semaines qui viennent la première année.
- **R2 — Pokémon n°0.** Dans la lib Tyradex 1.0.2, `pokedex_id` vaut `-1` si l'API renvoie `0`
  (`pokedex_id if (pokedex_id := data.get('pokedex_id')) else -1`, vérifié dans le code de la
  lib). Si le cache contient une entrée MissingNo., elle aura l'id `-1` et peut être tirée
  comme Pokémon du jour. Je n'ai pas pu vérifier si elle existe (réseau bloqué vers
  tyradex.app). Règle : tout id absent de `species.json` n'est **pas** enregistré dans le
  Pokédex et ne compte pas dans le total.
- **R3 — Le tirage dépend de l'ordre/longueur de `ALL_POKEMONS`.** Quand le cache est mis à
  jour, le Pokémon du jour peut changer en cours de journée. Le compteur « une fois par jour »
  empêche d'en capturer deux.
- **R4 — Stabilité de la graine.** Vérifié : `hash()` d'un tuple d'entiers ne dépend pas de
  `PYTHONHASHSEED`, le tirage est stable entre redémarrages.

## 8. Questions restantes

| # | Question | Proposition |
|---|----------|-------------|
| Q1 | Le catalogue de badges (§6) te va ? Noms, paliers, nombre ? | — |
| Q2 | `species.json` généré depuis PokeAPI (§4.1) plutôt qu'étendre le cache Tyradex ? | Oui |
| Q3 | Les badges 🌟/💎 méritent-ils un message plus visible (ex. ping du serveur) ? | Non, juste la ligne dans l'embed |

## 9. Critères d'acceptation

- [ ] `pokémon` sans mention enregistre le Pokémon du jour dans `data/pokedex.json`.
- [ ] `pokémon @x` n'enregistre rien, ni pour l'auteur ni pour `@x`.
- [ ] Redemander le même jour ne change ni le Pokédex, ni les compteurs, ni les badges.
- [ ] L'embed affiche « Nouveau ! » / « Déjà capturé (x fois) », la progression et les badges du jour.
- [ ] `/pokedex` : 20 entrées par page en 2 colonnes de 10, filtres, pagination réservée à l'auteur.
- [ ] `/badges` : badges obtenus avec date, verrouillés avec progression, secrets masqués.
- [ ] Un id absent de `species.json` (ex. `-1`) n'est ni enregistré ni compté.
- [ ] Fichier corrompu → mis de côté, pas écrasé (`load_json_safely`).
- [ ] Le Pokémon du jour s'affiche même si l'enregistrement plante.
- [ ] Tests unitaires : tirage, idempotence journalière, série, et `check` de chaque badge.

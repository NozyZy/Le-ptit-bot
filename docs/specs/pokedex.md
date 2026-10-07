# Spec : Pokédex — « Attrapez-les tous »

Statut : **brouillon, à valider avant dev**

## 1. Contexte

Aujourd'hui, écrire `pokémon` (ou `pokemon`, `pokémon ?`…) dans un salon déclenche le
**Pokémon du jour** (`bot.py`, handler `on_message`, bloc `re.fullmatch(r"pok[eé]mon…")`) :

- Le Pokémon est tiré dans `ALL_POKEMONS` (cache Tyradex, `data/pokemon_cache.json`)
  avec une graine `hash((user.id, jour_de_l_année, année))`. Il est donc **le même toute la
  journée pour un utilisateur donné**, quel que soit le serveur.
- 1 chance sur 8193 d'être shiny (`rng.randint(0, 8192) == 0`).
- Si on mentionne quelqu'un (`pokémon @machin`), le bot affiche le Pokémon du jour **de la
  personne mentionnée**.
- **Rien n'est sauvegardé** : une fois le message passé, le Pokémon est perdu.

Demande (NozZy) : garder cette feature et **sauvegarder les Pokémon déjà vus** dans un
Pokédex consultable.

## 2. Objectifs

1. Chaque Pokémon du jour obtenu est enregistré dans le Pokédex de l'utilisateur.
2. L'utilisateur peut consulter son Pokédex (et celui des autres) : progression, liste, shinies.
3. Zéro changement visible sur la feature existante, à part une ligne de progression en plus.

### Hors scope (v1)

- Échanges, combats, lien avec les starters (`cogs/pokemon_starter.py`).
- Rattrapage des jours passés (voir §7, Q4).
- Classement inter-serveurs.

## 3. Comportement

### 3.1 Enregistrement (« capture »)

Quand quelqu'un écrit `pokémon` **sans mention** (ou en se mentionnant soi-même) :

- Le Pokémon du jour est ajouté à son Pokédex s'il n'y est pas déjà.
- S'il est shiny et que la version shiny n'était pas encore possédée, on l'enregistre aussi.
- Le compteur de rencontres de ce Pokémon est incrémenté **au plus une fois par jour**
  (redemander 10 fois le même jour ne gonfle pas les stats).

Quand on regarde le Pokémon de quelqu'un d'autre (`pokémon @machin`) :

- **Proposition** : rien n'est capturé pour personne, mais l'auteur le marque comme **« vu »**
  (comme dans les jeux : *vus* vs *capturés*). Voir Q1.

### 3.2 Retour dans l'embed existant

Ajouter au message actuel, uniquement pour son propre Pokémon :

- Si nouveau : `🆕 Nouveau ! Ajouté à ton Pokédex.`
- Sinon : `Déjà capturé (x fois)`.
- Footer : `Pokédex : 42/1025` (remplace ou complète le footer actuel).

### 3.3 Commande `/pokedex`

`/pokedex [membre] [filtre]`

- `membre` (optionnel, défaut = soi) : voir le Pokédex de quelqu'un d'autre.
- `filtre` (optionnel) : `tous` (défaut), `capturés`, `manquants`, `shiny`.

Affichage : embed paginé avec boutons ◀️ ▶️ (même style que les `discord.ui.View` du cog
starter), timeout ~2 min, seul l'auteur peut paginer.

- En-tête : `Pokédex de X — 42/1025 capturés (4,1 %) · ✨ 1 shiny · 👁️ 50 vus`
- Page : ~20 entrées, format `#025 Pikachu ✨` ; les manquants en `#026 ???`.
- Option : générations (Gen 1 = #1–151, …) comme filtre/pages plutôt que pages de 20 (Q5).

### 3.4 (Optionnel v1.1) Classement serveur

`/pokedex_top` : top 10 du serveur par nombre de Pokémon capturés (membres du serveur courant
uniquement, le Pokédex étant global, voir §4).

## 4. Données

Nouveau fichier `data/pokedex.json` (le dossier `data/` est déjà dans `.gitignore`), écrit
avec `atomic_write_json(..., backup=True)` et lu avec `load_json_safely`, comme
`data/pokemon_starters.json`.

**Portée : globale par utilisateur** (pas par serveur), parce que le tirage du jour ne dépend
que de `user.id` et de la date : c'est le même Pokémon sur tous les serveurs.

```json
{
  "302102401324679168": {
    "caught": {
      "25": { "count": 3, "first": "2026-10-07", "last": "2026-11-02", "shiny": false }
    },
    "seen": [133, 150],
    "last_roll": "2026-11-02"
  }
}
```

- Clé = `pokedex_id` (string pour JSON), **jamais le nom** (les noms Tyradex peuvent bouger).
- `last_roll` sert à n'incrémenter `count` qu'une fois par jour.
- `seen` n'est utile que si Q1 = oui.
- Total affiché = nombre d'entrées de `ALL_POKEMONS` avec `id > 0` (voir R2).

## 5. Implémentation proposée

- Nouveau cog `cogs/pokedex.py` (chargé dans `main()` à côté de `cogs.pokemon_starter`) :
  stockage, `/pokedex`, la View de pagination.
- Le handler `on_message` de `bot.py` appelle une fonction du cog (ex.
  `register_daily(user_id, pokemon_id, shiny, today)`) qui renvoie `is_new`, `count`, `total`.
- Extraire le tirage du jour dans une fonction pure `daily_pokemon(user_id, today)` pour
  pouvoir la tester et la réutiliser.
- Pas de nouvelle dépendance.

## 6. Risques / points relevés dans le code

- **R1 — « Attrapez-les tous » est quasi impossible avec 1 tirage/jour.** Avec ~1025 Pokémon et
  un tirage aléatoire avec remise, il faut en moyenne n·Hₙ ≈ **7 700 jours (~21 ans)** pour tout
  avoir. Attendu : ~307 Pokémon distincts après 1 an, ~673 après 3 ans. Le shiny à 1/8193 par
  jour, c'est en moyenne une fois tous les ~22 ans. Si l'objectif est de pouvoir finir, il faut
  changer la mécanique (Q2).
- **R2 — Pokémon n°0.** Je n'ai pas pu vérifier (réseau bloqué vers tyradex.app) si
  `Tyradex.Pokemon.all()` renvoie une entrée `pokedex_id = 0` (MissingNo.). Si oui, il faut
  l'exclure du total, sinon personne ne peut atteindre 100 %. À vérifier sur le cache de prod.
- **R3 — Le tirage dépend de l'ordre/longueur de `ALL_POKEMONS`.** Quand le cache est mis à
  jour (nouveaux Pokémon), le Pokémon du jour peut changer en cours de journée. Sans gravité
  pour le Pokédex puisqu'on stocke par `id`, mais un utilisateur pourrait capturer 2 Pokémon
  ce jour-là. Acceptable.
- **R4 — Stabilité de la graine.** Vérifié : `hash()` d'un tuple d'entiers ne dépend pas de
  `PYTHONHASHSEED`, le tirage est bien stable entre redémarrages.

## 7. Questions ouvertes (à trancher avant dev)

| # | Question | Proposition |
|---|----------|-------------|
| Q1 | Voir le Pokémon de quelqu'un (`pokémon @x`) : « vu » pour l'auteur ? capture pour `@x` ? | « Vu » pour l'auteur, pas de capture pour `@x` (sinon les potes remplissent ton dex à ta place) |
| Q2 | Rendre la complétion atteignable ? | Garder 1 tirage/jour en v1, et décider plus tard (ex. tirage bonus, capture via combats du cog starter) |
| Q3 | Pokédex global ou par serveur ? | Global (cohérent avec le tirage) |
| Q4 | Rattraper l'historique ? Techniquement on peut recalculer le Pokémon de n'importe quel jour passé (graine déterministe), mais on ne sait pas qui l'a vraiment demandé | Non, on commence à zéro |
| Q5 | Pagination : pages de 20 ou par génération ? | Par génération + filtre |
| Q6 | Shiny : entrée séparée ou simple flag sur le Pokémon ? | Flag `shiny` sur l'entrée, compteur ✨ dans l'en-tête |
| Q7 | Annonce publique quand quelqu'un complète une génération / le dex ? | Oui, message dans le salon (c'est drôle et ça arrivera rarement) |

## 8. Critères d'acceptation

- [ ] `pokémon` sans mention enregistre le Pokémon du jour dans `data/pokedex.json`.
- [ ] Redemander le même jour n'incrémente pas `count` et n'ajoute rien.
- [ ] L'embed affiche « Nouveau ! » la première fois, et la progression `x/total`.
- [ ] Un shiny est enregistré comme tel ; `/pokedex filtre:shiny` le liste.
- [ ] `/pokedex` et `/pokedex @membre` affichent progression et liste paginée.
- [ ] Le total exclut un éventuel `id = 0`.
- [ ] Fichier corrompu → mis de côté, pas écrasé (comportement de `load_json_safely`).
- [ ] La feature Pokémon du jour fonctionne toujours si le Pokédex plante (try/except
      autour de l'enregistrement, log d'erreur, pas de crash de l'embed).

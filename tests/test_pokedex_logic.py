"""Run from the repository root: python -m unittest discover -s tests"""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pokedex_logic as dex  # noqa: E402

DAY = datetime.date(2026, 10, 7)


def day(n: int) -> datetime.date:
    return DAY + datetime.timedelta(days=n)


def badge_ids(result) -> set[str]:
    return {b.id for b in result.new_badges}


class SpeciesDataTest(unittest.TestCase):
    def test_reference_data(self):
        self.assertEqual(dex.TOTAL_SPECIES, 1025)
        self.assertEqual(sum(dex.GEN_SIZES.values()), 1025)
        self.assertEqual(len(dex.FAMILIES[dex.EEVEE_FAMILY]), 9)
        self.assertEqual(len(dex.STARTER_FAMILIES), 27)
        self.assertEqual(dex.SPECIES[25]["name"], "Pikachu")

    def test_badge_catalog(self):
        self.assertEqual(dex.TOTAL_BADGES, 96)
        self.assertEqual(len(dex.BADGES_BY_ID), 96, "ids de badges en double")
        self.assertEqual(sum(b.secret for b in dex.BADGES), 5)
        for badge in dex.BADGES:
            self.assertIn(badge.category, dex.CATEGORIES)
            self.assertIn(badge.rarity, dex.RARITY_EMOJIS)


class RegisterDailyTest(unittest.TestCase):
    def setUp(self):
        self.data = {}

    def roll(self, pid, when=DAY, user="1", shiny=False, **kwargs):
        return dex.register_daily(self.data, user, pid, shiny, when, **kwargs)

    def test_first_capture(self):
        result = self.roll(25)
        self.assertTrue(result.is_new)
        self.assertEqual(result.count, 1)
        self.assertEqual(result.total_caught, 1)
        self.assertIn("dex_1", badge_ids(result))
        self.assertEqual(self.data["1"]["caught"]["25"]["first"], DAY.isoformat())

    def test_same_day_is_idempotent(self):
        self.roll(25)
        again = self.roll(25)
        self.assertEqual(again.count, 1)
        self.assertEqual(again.new_badges, [])
        self.assertEqual(self.data["1"]["days"], 1)
        self.assertTrue(again.is_new, "capturé aujourd'hui : toujours affiché comme nouveau")

    def test_same_day_different_pokemon_is_not_registered(self):
        self.roll(25)
        other = self.roll(26)
        self.assertNotIn("26", self.data["1"]["caught"])
        self.assertFalse(other.is_new)
        self.assertEqual(other.count, 0)

    def test_already_caught_another_day(self):
        self.roll(25)
        result = self.roll(25, day(1))
        self.assertFalse(result.is_new)
        self.assertEqual(result.count, 2)

    def test_unknown_id_is_ignored(self):
        self.assertIsNone(self.roll(-1))
        self.assertIsNone(self.roll(0))
        self.assertEqual(self.data, {})

    def test_shiny_is_kept(self):
        self.roll(25, shiny=True)
        result = self.roll(25, day(1))
        self.assertTrue(self.data["1"]["caught"]["25"]["shiny"])
        self.assertNotIn("shiny", badge_ids(result))
        self.assertIn("shiny", self.data["1"]["badges"])

    def test_streak(self):
        for n in range(3):
            result = self.roll(1 + n, day(n))
        self.assertIn("streak_3", badge_ids(result))
        self.roll(10, day(5))
        entry = self.data["1"]
        self.assertEqual(entry["streak"], 1)
        self.assertEqual(entry["best_streak"], 3)
        self.assertEqual(entry["days"], 4)

    def test_trilogy_and_family(self):
        self.roll(1)
        self.roll(2, day(1))
        result = self.roll(3, day(2))
        self.assertTrue({"family_1", "trilogy_1", "heir"} <= badge_ids(result))

    def test_two_stage_family_is_not_a_trilogy(self):
        self.roll(129)  # Magicarpe
        result = self.roll(130, day(1))  # Léviator
        self.assertIn("family_1", badge_ids(result))
        self.assertNotIn("trilogy_1", badge_ids(result))
        self.assertNotIn("heir", badge_ids(result))

    def test_live_evolution_needs_yesterday(self):
        self.roll(129)
        self.assertIn("live_evolution", badge_ids(self.roll(130, day(1))))
        self.data = {}
        self.roll(129)
        self.assertNotIn("live_evolution", badge_ids(self.roll(130, day(2))))

    def test_deja_vu(self):
        self.roll(25)
        self.roll(25, day(1))
        self.assertIn("deja_vu", badge_ids(self.roll(25, day(2))))

    def test_irony(self):
        result = self.roll(5, starter_ids={4, 5, 6})
        self.assertIn("irony", badge_ids(result))

    def test_twins_only_same_server(self):
        self.roll(25, user="2")
        result = self.roll(25, user="1", is_guild_member=lambda uid: False)
        self.assertNotIn("twins", badge_ids(result))

        self.data = {}
        self.roll(25, user="2")
        result = self.roll(25, user="1", is_guild_member=lambda uid: uid == "2")
        self.assertIn("twins", badge_ids(result))
        self.assertIn("twins", self.data["2"]["badges"])
        # The other player hears about it on their next own roll
        later = self.roll(26, day(1), user="2")
        self.assertIn("twins", badge_ids(later))
        self.assertEqual(self.data["2"]["pending_badges"], [])

    def test_region_and_type_progress(self):
        badge = dex.BADGES_BY_ID["region_1_25"]
        entry = dex.get_entry({}, "x")
        self.assertEqual(badge.progress(entry, {1, 2, 152}), (2, 38))
        badge = dex.BADGES_BY_ID["type_feu"]
        self.assertEqual(badge.progress(entry, {4, 5, 6, 1}), (3, 10))

    def test_badges_are_never_awarded_twice(self):
        self.roll(1)
        result = self.roll(4, day(1))
        self.assertNotIn("dex_1", badge_ids(result))


if __name__ == "__main__":
    unittest.main()

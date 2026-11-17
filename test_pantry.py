import unittest
import pantry


class TestSevenfoldPantry(unittest.TestCase):

    def test_seven_resources_exist(self):
        self.assertEqual(len(pantry.SEVENFOLD_PANTRY), 7)

    def test_all_resources_have_descriptions(self):
        for item, description in pantry.SEVENFOLD_PANTRY.items():
            self.assertTrue(item.strip())
            self.assertTrue(description.strip())

    def test_steward_rule_exists(self):
        self.assertIn("nourishes others", pantry.STEWARD_RULE)

    def test_registry_contains_expected_resources(self):
        names = " ".join(pantry.SEVENFOLD_PANTRY.keys())
        for resource in (
            "Wheat", "Barley", "Grapes", "Figs",
            "Pomegranates", "Olives", "Dates"
        ):
            self.assertIn(resource, names)


if __name__ == "__main__":
    unittest.main()

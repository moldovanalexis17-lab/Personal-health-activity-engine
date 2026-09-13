"""Small regression tests for calculations that do not need Google Sheets."""

import unittest

from test_sheets import (
    calculeaza_activitate,
    calculeaza_bmi,
    intensitate_normalizata,
    scor_procent,
)


REFERENCE_ACTIVITY = {
    "moderata_min": 150,
    "moderata_max": 300,
    "viguroasa_min": 75,
    "viguroasa_max": 150,
}


class EngineTests(unittest.TestCase):
    def test_bilingual_activity_intensity_is_normalized(self):
        self.assertEqual(intensitate_normalizata("Moderata"), "moderate")
        self.assertEqual(intensitate_normalizata("Moderate"), "moderate")
        self.assertEqual(intensitate_normalizata("Viguros"), "vigorous")
        self.assertEqual(intensitate_normalizata("Vigorous"), "vigorous")

    def test_bmi_uses_metric_units(self):
        self.assertEqual(calculeaza_bmi(70, 175), 22.9)

    def test_percentage_score_is_limited_to_zero_and_one_hundred(self):
        self.assertEqual(scor_procent(300, 150), 100)
        self.assertEqual(scor_procent(-10, 150), 0)
        self.assertEqual(scor_procent(10, 0), 0)

    def test_vigorous_activity_accepts_the_romanian_sheet_value(self):
        result = calculeaza_activitate(
            {
                "zile_active": 3,
                "minute_zi": 30,
                "intensitate": "Viguros",
            },
            REFERENCE_ACTIVITY,
        )

        self.assertEqual(result["durata"], 90)
        self.assertEqual(result["minim"], 75.0)
        self.assertEqual(result["evaluare"], "Within the recommended range")


if __name__ == "__main__":
    unittest.main()

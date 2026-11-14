"""Smoke test for the Phase 1 Streamlit page."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

import adhikar_ai


class AppSmokeTest(unittest.TestCase):
    def test_intro_and_disabled_search(self) -> None:
        app_path = Path(adhikar_ai.__file__).parent / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=15)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(
            app.title[0].value, "AdhikarAI — Government Scheme Discovery"
        )
        self.assertIn("does not assess eligibility", app.info[0].value)
        self.assertTrue(app.text_input[0].disabled)
        self.assertTrue(app.button[0].disabled)


if __name__ == "__main__":
    unittest.main()

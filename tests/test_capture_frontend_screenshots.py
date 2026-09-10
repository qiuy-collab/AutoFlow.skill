import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "capture_frontend_screenshots.py"
SPEC = importlib.util.spec_from_file_location("capture_frontend_screenshots", MODULE_PATH)
CAPTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAPTURE)


class FakeLocator:
    def __init__(self):
        self.calls = []

    def screenshot(self, **kwargs):
        self.calls.append(kwargs)


class FakePage:
    def __init__(self):
        self.page_calls = []
        self.selector = None
        self.locator_instance = FakeLocator()

    def screenshot(self, **kwargs):
        self.page_calls.append(kwargs)

    def locator(self, selector):
        self.selector = selector
        return self.locator_instance


class CaptureScopeTests(unittest.TestCase):
    def test_browser_path_uses_explicit_cross_platform_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            browser = Path(temp) / "browser"
            browser.touch()
            with patch.dict(os.environ, {"AUTOFLOW_BROWSER_PATH": str(browser)}):
                self.assertEqual(CAPTURE.choose_browser_executable(), str(browser))

    def test_selector_scope_captures_the_complete_selected_board(self):
        page = FakePage()

        CAPTURE.capture_shot(
            page,
            {"capture_scope": "selector", "capture_selector": "#orders-board"},
            Path("orders.png"),
        )

        self.assertEqual(page.selector, "#orders-board")
        self.assertEqual(page.page_calls, [])
        self.assertEqual(page.locator_instance.calls, [{"path": "orders.png"}])

    def test_page_and_viewport_scopes_use_the_expected_page_capture_mode(self):
        page = FakePage()

        CAPTURE.capture_shot(page, {"capture_scope": "page"}, Path("page.png"))
        CAPTURE.capture_shot(page, {"capture_scope": "viewport"}, Path("viewport.png"))

        self.assertEqual(
            page.page_calls,
            [
                {"path": "page.png", "full_page": True},
                {"path": "viewport.png", "full_page": False},
            ],
        )

    def test_selector_scope_requires_a_selector(self):
        with self.assertRaisesRegex(SystemExit, "requires capture_selector"):
            CAPTURE.capture_shot(FakePage(), {"capture_scope": "selector"}, Path("missing.png"))


if __name__ == "__main__":
    unittest.main()

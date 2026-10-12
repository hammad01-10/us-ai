import unittest
from unittest.mock import patch

from core import resource_index
from core.resource_controller import open_resource


class ResourceIndexTests(unittest.TestCase):
    def setUp(self):
        resource_index._RESOURCE_INDEX_CACHE = None
        resource_index._RESOURCE_INDEX_CACHE_TIME = 0.0

    def test_resource_index_is_cached_briefly(self):
        pc = {
            "system": {"platform": "Windows"},
            "installed_programs": ["Example"],
            "shortcuts": [],
            "windows_tools": [],
        }
        with patch("core.resource_index.inspect_pc", return_value=pc) as inspect:
            first = resource_index.build_resource_index()
            second = resource_index.build_resource_index()

        self.assertIs(first, second)
        inspect.assert_called_once()
        self.assertEqual(first["resources"][0]["type"], "installed_program")

    @patch("core.resource_controller.open_application", return_value="Opening Example.")
    def test_installed_program_can_be_opened(self, open_application):
        result = open_resource({"type": "installed_program", "name": "Example"})

        self.assertEqual(result, {"status": "opened", "message": "Opening Example."})
        open_application.assert_called_once_with("Example")


if __name__ == "__main__":
    unittest.main()

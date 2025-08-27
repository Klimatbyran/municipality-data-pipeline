import json
import os
import unittest

OUTPUT_PATH = "output/climate-data.json"


class TestClimateData(unittest.TestCase):
    """Test suite for climate data JSON output validation."""

    def test_file_exists(self):
        """Test that the output file exists."""
        self.assertTrue(os.path.exists(OUTPUT_PATH), f"{OUTPUT_PATH} does not exist.")

    def test_file_not_empty(self):
        """Test that the output file is not empty."""
        size = os.path.getsize(OUTPUT_PATH)
        self.assertGreater(
            size, 10, f"{OUTPUT_PATH} is empty or too small (size: {size} bytes)."
        )

    def test_json_has_data(self):
        """Test that the JSON file has data."""
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"JSON is malformed: {e}")
        self.assertIsInstance(data, list, f"Expected a list, got {type(data)}")
        self.assertGreater(len(data), 0, "JSON file is valid but contains no entries.")


if __name__ == "__main__":
    unittest.main()

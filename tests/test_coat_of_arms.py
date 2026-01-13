from unittest.mock import patch
import unittest
from facts.coatOfArms.coat_of_arms import get_coat_of_arms, get_municipality_wiki_id

class TestGetMunicipalityWikiID(unittest.TestCase):

    @patch("facts.coatOfArms.coat_of_arms.requests.get")
    def test_single_result(self, mock_get):
        
        mock_get.return_value.json.return_value = {
            "search": [{"id": "Q123", "label": "Stockholm"}]
        }
        result = get_municipality_wiki_id("Stockholm")
        self.assertEqual(result, ["Q123"])

    @patch("facts.coatOfArms.coat_of_arms.requests.get")
    def test_no_results(self, mock_get):
        mock_get.return_value.json.return_value = {"search": []}
        result = get_municipality_wiki_id("NonexistentTown")
        self.assertEqual(result, [])


class TestGetCoatOfArms(unittest.TestCase):

    @patch("facts.coatOfArms.coat_of_arms.get_municipality_wiki_id")
    @patch("facts.coatOfArms.coat_of_arms.requests.get")
    def test_p94_exists(self, mock_requests_get, mock_get_wiki_id):
        mock_get_wiki_id.return_value = ["Q123"]

        mock_requests_get.return_value.json.return_value = {
            "entities": {
                "Q123": {
                    "claims": {
                        "P94": [
                            {"mainsnak": {"datavalue": {"value": "Stockholm_Coat.png"}}}
                        ]
                    }
                }
            }
        }

        mock_requests_get.return_value.url = "https://commons.wikimedia.org/Stockholm_Coat.png"

        result = get_coat_of_arms("Stockholm")
        self.assertEqual(result, "https://commons.wikimedia.org/Stockholm_Coat.png")

    @patch("facts.coatOfArms.coat_of_arms.get_municipality_wiki_id")
    @patch("facts.coatOfArms.coat_of_arms.requests.get")
    def test_p94_missing_p154_exists(self, mock_requests_get, mock_get_wiki_id):
        mock_get_wiki_id.return_value = ["Q456"]
        mock_requests_get.return_value.json.return_value = {
            "entities": {
                "Q456": {
                    "claims": {
                        "P154": [
                            {"mainsnak": {"datavalue": {"value": "Fallback_Logo.png"}}}
                        ]
                    }
                }
            }
        }
        mock_requests_get.return_value.url = "https://commons.wikimedia.org/Fallback_Logo.png"

        result = get_coat_of_arms("FallbackTown")
        self.assertEqual(result, "https://commons.wikimedia.org/Fallback_Logo.png")

    @patch("facts.coatOfArms.coat_of_arms.get_municipality_wiki_id")
    @patch("facts.coatOfArms.coat_of_arms.requests.get")
    def test_no_images(self, mock_requests_get, mock_get_wiki_id):
        mock_get_wiki_id.return_value = ["Q789"]
        mock_requests_get.return_value.json.return_value = {
            "entities": {
                "Q789": {
                    "claims": {}
                }
            }
        }

        result = get_coat_of_arms("EmptyTown")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
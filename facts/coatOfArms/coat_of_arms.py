"""Module for retrieving territory coat of arms images from Wikidata."""
from urllib.parse import quote
import requests


def _extract_filename_from_property(property_statements):
    """Extract filename from a Wikidata property statement list."""
    for statement in property_statements:
        snak = statement.get("mainsnak", {})
        if "datavalue" in snak:
            return snak["datavalue"]["value"].replace(" ", "_")
    return None


def _get_image_url_from_filename(filename, headers):
    """Get the final image URL from a Commons filename."""
    url = (
        f"https://commons.wikimedia.org/wiki/Special:Redirect/file/"
        f"{quote(filename)}"
    )
    res = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
    return res.url


def _extract_coat_of_arms_from_p18(p18_statements):
    """Extract coat of arms filename from P18 statements by filtering keywords."""
    coat_of_arms_keywords = ["vapen", "kommunvapen", "vapensköld", "coat_of_arms"]

    for statement in p18_statements:
        snak = statement.get("mainsnak", {})
        if "datavalue" in snak:
            candidate_filename = snak["datavalue"]["value"].replace(" ", "_")
            if any(keyword.lower() in candidate_filename.lower()
                   for keyword in coat_of_arms_keywords):
                return candidate_filename
    return None


def get_coat_of_arms(territory_name):

    """ Retrieve coat of arms URL for a given territory.
    
    Searches for territory in Wikidata and retrieves the coat of arms image URL
    from either P94 (coat of arms image) or P154 (logo image) properties.
    
    Args:
        territory_name (str): Name of the territory to search for
        
    Returns:
        Optional[str]: URL to coat of arms image, or None if not found 
    """


    wiki_ids = get_territory_wiki_id(territory_name)

    if not wiki_ids:
        return None
    headers = {"User-Agent": "KlimatkollenFetcher/1.0 (contact: hej@klimatkollen.se)"}
    coat_of_arms_url = None

    for wiki_id in wiki_ids:
        url = (
            f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids="
            f"{wiki_id}&props=claims&format=json"
        )
        res = requests.get(url, headers=headers, timeout=30)

        try:
            response = res.json()
            claims = response["entities"][wiki_id]["claims"]

            p94 = claims.get("P94")
            p154 = claims.get("P154")
            p18 = claims.get("P18")

            filename = None
            if p94:
                filename = _extract_filename_from_property(p94)
            elif p154:
                filename = _extract_filename_from_property(p154)
            elif p18:
                filename = _extract_coat_of_arms_from_p18(p18)

            if filename:
                coat_of_arms_url = _get_image_url_from_filename(filename, headers)
                break

        except ValueError:
            print(f"Could not parse response to JSON for {territory_name}")
            continue  # Try next wiki_id

    # Only print "not found" message if we checked all entries and found nothing
    if not coat_of_arms_url:
        print(f"Found no coat of arms image for {territory_name}")

    return coat_of_arms_url


def get_territory_wiki_id(territory_name):
    """Get territory wiki ID from Wikidata."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": territory_name,
        "language": "sv",
        "format": "json"
    }
    headers = {
        "User-Agent": "KlimatkollenFetcher/1.0 (contact: hej@klimatkollen.se)"
    }

    res = requests.get(url, params=params, headers=headers, timeout=30)

    try:
        response = res.json()
        search_results = response.get("search", [])
        if not search_results:
            return []

        # Prefer entries with "kommun" or "municipality" in the label (municipality entries)
        # as they're more likely to have coat of arms (P94)
        kommun_entries = []
        other_entries = []

        for territory in search_results:
            territory_id = territory.get("id")
            label = territory.get("label", "").lower()
            description = territory.get("description", "").lower()

            # Check if this looks like a municipality entry
            if ("kommun" in label or "municipality" in label or
                "kommun" in description or "municipality" in description):
                kommun_entries.append(territory_id)
            else:
                other_entries.append(territory_id)

        # Return municipality entries first, then others
        wiki_ids = kommun_entries + other_entries or [search_results[0].get("id")]

        return wiki_ids

    except ValueError:
        print("Could not find valid wikiId")
        return []

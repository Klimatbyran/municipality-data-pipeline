"""Module for retrieving municipality coat of arms images from Wikidata."""
from urllib.parse import quote
import requests

def get_coat_of_arms(municipality_name):

    """ Retrieve coat of arms URL for a given municipality.
    
    Searches for municipality in Wikidata and retrieves the coat of arms image URL
    from either P94 (coat of arms image) or P154 (logo image) properties.
    
    Args:
        municipality_name (str): Name of the municipality to search for
        
    Returns:
        Optional[str]: URL to coat of arms image, or None if not found 
    """


    wiki_ids = get_municipality_wiki_id(municipality_name)

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
            filename = None

            if p94:
                for statement in p94:
                    snak = statement.get("mainsnak",{})
                    if "datavalue" in snak:
                        filename = snak["datavalue"]["value"].replace(" ", "_")
                        break

                if filename and isinstance(filename, str):
                    url = (
                        f"https://commons.wikimedia.org/wiki/Special:Redirect/file/"
                        f"{quote(filename)}"
                    )
                    res = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
                    coat_of_arms_url = res.url

            else:
                if p154:
                    for statement in p154:
                        snak = statement.get("mainsnak",{})
                        if "datavalue" in snak:
                            filename = snak["datavalue"]["value"].replace(" ", "_")
                            break

                    if filename and isinstance(filename, str):
                        url = (
                            f"https://commons.wikimedia.org/wiki/Special:Redirect/file/"
                            f"{quote(filename)}"
                        )
                        res = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
                        coat_of_arms_url = res.url

                else:
                    print(f"Found no coat of arms image for {municipality_name}")

        except ValueError:
            print(f"Could not parse response to JSON for {municipality_name}")
            return None

    return coat_of_arms_url


def get_municipality_wiki_id(municipality_name):
    """Get municipality wiki ID from Wikidata."""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": municipality_name,
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

        wiki_ids = [search_results[0].get("id")]

        if len(search_results) > 1:
            for municipality in search_results:
                if (
                    f"{municipality_name} Municipality"
                    in municipality["label"]
                ):
                    valid_id = municipality.get("id")
                    if valid_id not in wiki_ids:
                        wiki_ids.append(valid_id)

        return wiki_ids

    except ValueError:
        print("Could not find valid wikiId")
        return []

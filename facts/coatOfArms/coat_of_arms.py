
import requests
import json 
from urllib.parse import quote

""" Måste skapa en check som först kollar t.ex "bollnäs" wikiId om den inte har en coat of arms, kolla bollnäs municipality-wikiId. M """


def get_coat_of_arms(municipalityName):
    wikiIDs = get_municipality_wikiId(municipalityName)
    
    headers = {"User-Agent": "KlimatkollenFetcher/1.0 (contact: hej@klimatkollen.se)"}
    coatOfArmsUrl = None
   
    for id in wikiIDs:
        url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={id}&props=claims&format=json'
        res = requests.get(url, headers=headers) 
 
        try: 
            response = res.json()
            claims = response["entities"][id]["claims"]

            p94 = claims.get("P94")
            p154 = claims.get("P154")
            filename = None 

            if p94:
                print("P94 exists:", p94[0])

                for statement in p94:
                    snak = statement.get("mainsnak",{})
                    if "datavalue" in snak:
                        filename = snak["datavalue"]["value"]
                        break
                
                if filename and isinstance(filename, str):
                    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}"
                    coatOfArmsUrl = url

            else:
                print("No P94 exists, trying P154...")

                if p154:
                    for statement in p154:
                        snak = statement.get("mainsnak",{})
                        if "datavalue" in snak:
                            filename = snak["datavalue"]["value"]
                            break
                    
                    if filename and isinstance(filename, str):
                        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}"
                        coatOfArmsUrl = url

                else:
                    print("No P154 exists")

        except ValueError:
            print("Could not parse response to JSON")
            return
    return coatOfArmsUrl


def get_municipality_wikiId(municipalityName):
    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbsearchentities",
        "search": municipalityName,
        "language": "sv",
        "format": "json"
    }

    headers = {
        "User-Agent": "KlimatkollenFetcher/1.0 (contact: hej@klimatkollen.se)"
    }

    res = requests.get(url, params=params, headers=headers)
    
    try:
        response = res.json()
        searchResults = response["search"]
        wikiIDs = []
        wikiIDs.append(searchResults[0].get("id"))
        
    
        if len(searchResults) > 1:
            for municipality in searchResults:
                if municipalityName + " Municipality" in municipality["label"]:
                    validID = municipality.get("id")
                    if validID not in wikiIDs:
                        wikiIDs.append(municipality.get("id"))
        return wikiIDs

    except ValueError:
        print("Could not find valid wikiId")
        return

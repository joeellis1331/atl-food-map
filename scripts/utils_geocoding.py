import time
import pandas
from geopy.geocoders import Nominatim
from functools import lru_cache
import re

# Initialize geolocator with longer timeout
geolocator = Nominatim(user_agent="ATL_food_map", timeout=10)

# need to do some cleaning because OpenStreetMap is not as robust as google maps
def clean_address(address):
    if not isinstance(address, str):
        return ""

    # Remove unit/suite/apartment identifiers
    address = re.sub(
        r'\b(?:Unit|Suite|Ste|Apt|Apartment|Stall)\s*\w+\b|#\s*\w+',
        '',
        address,
        flags=re.IGNORECASE
    )

    # Collapse multiple spaces and remove trailing spaces
    address = re.sub(r'\s{2,}', ' ', address).strip()
    # Remove space before commas
    address = re.sub(r'\s+,', ',', address)

    # Expand cardinal directions
    direction_map = {
        r'\bN\b': 'North',
        r'\bS\b': 'South',
        r'\bE\b': 'East',
        r'\bW\b': 'West',
        r'\bNE\b': 'Northeast',
        r'\bNW\b': 'Northwest',
        r'\bSE\b': 'Southeast',
        r'\bSW\b': 'Southwest'
    }
    for abbr, full in direction_map.items():
        address = re.sub(abbr, full, address, flags=re.IGNORECASE)

    # Standardize street suffixes
    suffix_map = {
        r'\bSt\b': 'Street',
        r'\bHwy\b': 'Highway',
        r'\bAve\b': 'Avenue',
        r'\bRd\b': 'Road',
        r'\bDr\b': 'Drive',
        r'\bBlvd\b': 'Boulevard',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPl\b': 'Place',
        r'\bTer\b': 'Terrace',
        r'\bPkwy\b': 'Parkway',
        r'\bCir\b': 'Circle',
        r'\bTrl\b': 'Trail'
    }
    for abbr, full in suffix_map.items():
        address = re.sub(abbr, full, address, flags=re.IGNORECASE)

    return address


# # Caching decorator for geocoding
@lru_cache(maxsize=None)
#initial geocoding function
def try_geocode(query, fallback):
    if fallback == False:
        try:
            location = geolocator.geocode(query, country_codes='US')
            if location:
                return location.latitude, location.longitude
        except Exception as e:
            return None, None
    else:
        try:
            location = lambda query: geolocator.geocode("%s, Georgia, United States" % query)
            if location:
                address = location(query)
                return address.latitude, address.longitude
        except Exception as e:
            return None, None

    return None, None

'''
main geocode wrapper function, utilizes openstreetmap as geocoder.
First pass is to use the address, if openstreetmap doesn't recognize the address (it is community curated
therefore sometimes the address doesn't match google exactly) it uses the place name in hope to hit a match
'''
def geocode_with_fallback(row):
    address = clean_address(row.get('Location', ''))
    name = row.get('Name', '')

    #trys to geocode based on the address
    name_fallback = False
    lat, lon = try_geocode(address, name_fallback)

    #if address doesn't work, falls back to trying just restaurant name
    if lat is None or lon is None:
        name_fallback = True
        #uses alternative function
        lat, lon = try_geocode(name, name_fallback)
        #if fails again, doesn't geocode
        if lat is None or lon is None:
            print(f"WARING: Geocoding failed for both address and name -> '{address}' / '{name}'")

    return lat, lon
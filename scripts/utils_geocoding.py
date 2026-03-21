import time
import pandas
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from functools import lru_cache
import re
import pickle
import os
from geopy.extra.rate_limiter import RateLimiter

# Initialize geolocator with longer timeout
geolocator = Nominatim(user_agent="ATL_food_map (joeellis.2013@gmail.com)", timeout=10)
#rate limits API calls, helps not get timed out
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1,
    max_retries=3,
    error_wait_seconds=5
)

#sets up/loads cache file for geocode calls
CACHE_FILE = "geocode_cache.pkl"
# load cache at import
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "rb") as f:
        geocode_cache = pickle.load(f)
else:
    geocode_cache = {}

#########################################

'''
saves cache file
'''
def save_cache():
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(geocode_cache, f)

'''
normalizes subtle differences in query
'''
def normalize_query(q):
    #checks to see if query is none, na, etc.
    if not isinstance(q, str):
        return ""
    #strips leading/trailing, makes everything lower
    return re.sub(r'\s+', ' ', q.strip().lower())

'''cleans addresses because OpenStreetMap is not as robust as google maps'''
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


'''
This is the wrapper geocoding function, it tries initial and fallback options, check caches
'''
def try_geocode(query, fallback):
    # build the full query, added GA, USA helps
    if not fallback:
        final_query = query
    else:
        final_query = f"{query}, Georgia, United States"

    # normalizes final query, sets it as "key"
    key = normalize_query(final_query)

    # checks if exact same query has been run before to avoid repeated API calls
    if key in geocode_cache:
        return geocode_cache[key]

    try:
        location = geocode(final_query, country_codes='US')

        if location:
            result = (location.latitude, location.longitude)
            #cache successful results
            geocode_cache[key] = result
        else:
            result = (None, None)

    except Exception:
        result = (None, None)

    return result

'''
main geocode wrapper function, utilizes openstreetmap as geocoder.
First pass is to use the address, if openstreetmap doesn't recognize the address (it is community curated
therefore sometimes the address doesn't match google exactly) it uses the place name in hope to hit a match
'''
def geocode_with_fallback(row, geocode_errors):
    #cleans up any abbreviation in address
    address = clean_address(row.get('Location', ''))
    name = row.get('Name', '')

    #trys to geocode based on the address
    lat, lon = try_geocode(address, False)

    #if address doesn't work, falls back to trying just restaurant name
    if lat is None or lon is None:
        #uses alternative function
        lat, lon = try_geocode(name, True)
        #if fails again, doesn't geocode
        if lat is None or lon is None:
            geocode_errors.append(f"'{address}' / '{name}'")

    return lat, lon
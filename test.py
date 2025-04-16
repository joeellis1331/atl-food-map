import time
import pandas
from geopy.geocoders import Nominatim
from functools import lru_cache
import folium
import re


@lru_cache(maxsize=None)
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
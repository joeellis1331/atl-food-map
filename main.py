import time
import pandas
from geopy.geocoders import Nominatim
from functools import lru_cache
import folium

#######################################
## Get data
#######################################

#load excel file
file_path = './ATL-Food-and-Drink-Review-List.xlsx'  # Replace with your file path
excel_file = pandas.ExcelFile(file_path)

#creates empty dict to store keys as sheet names and values as the row/column data
all_data = {}
#loops through each sheet
for sheet_name in excel_file.sheet_names:
    #ignores general info and to try list sheets
    if sheet_name not in ['General Notes', 'To Try']:
        sheet_data = excel_file.parse(sheet_name)
        #adds the sheet name, which signifies the place type (i.e. restaurant, bar, dessert) to pandas df
        sheet_data['place_type'] = sheet_name
        all_data[sheet_name] = sheet_data

#creates one big dataframe
combined_df = pandas.concat(all_data.values(), ignore_index=True)


#######################################
## map data
#######################################
# Initialize geolocator with longer timeout
geolocator = Nominatim(user_agent="ATL_food_map", timeout=10)

# Safe address cleaner
def clean_address(address):
    if isinstance(address, str):
        return address.replace("#", "Unit ").strip()
    return ""

# Caching decorator for geocoding
@lru_cache(maxsize=None)
def try_geocode(query):
    try:
        location = geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocode error for '{query}': {e}\n")
    return None, None

# Combined geocoding logic: Try Location, then fallback to Name
def geocode_with_fallback(row):
    address = clean_address(row.get('Location', ''))
    name = row.get('Name', '')

    lat, lon = try_geocode(address)
    if lat is None or lon is None:
        print(f"Falling back to name: {name}")
        lat, lon = try_geocode(name)

    return lat, lon

# Apply geocoding and update DataFrame
def apply_geocoding(df):
    df['coordinates'] = df.apply(geocode_with_fallback, axis=1)
    df[['latitude', 'longitude']] = pandas.DataFrame(df['coordinates'].tolist(), index=df.index)
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

# Create map with geocoded city center
def create_map(city_address='Atlanta, Georgia, USA'):
    center = try_geocode(city_address)
    if center[0] is not None and center[1] is not None:
        return folium.Map(location=center, zoom_start=12)
    else:
        print("Could not geocode city center.")
        return None

# Add markers
def add_markers_to_map(df, food_map):
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row['Name']
        ).add_to(food_map)

# Main pipeline
def generate_food_map(df):
    df = apply_geocoding(df)
    food_map = create_map()

    if food_map:
        add_markers_to_map(df, food_map)
        food_map.save('ATL_food_map.html')
        print("Food map saved as ATL_food_map.html.")
    else:
        print("Failed to create food map.")

# Example usage:
generate_food_map(combined_df)
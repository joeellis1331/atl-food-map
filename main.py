import time
import pandas
from geopy.geocoders import Nominatim
from functools import lru_cache
import folium
import re

#######################################
## Get data
#######################################

#load excel file
file_path = './ATL-Food-and-Drink-Review-List.xlsx'  # Replace with your file path
excel_file = pandas.ExcelFile(file_path)

#creates empty dict to store keys as sheet names and values as the row/column data
all_data = {}
#color_counter
color_counter = 0
#loops through each sheet
for sheet_name in excel_file.sheet_names:
    #ignores general info and to try list sheets
    if sheet_name not in ['General Notes', 'To Try']:
        sheet_data = excel_file.parse(sheet_name)
        #adds the sheet name, which signifies the place type (i.e. restaurant, bar, dessert) to pandas df
        sheet_data['place_type'] = sheet_name
        #assigns a numeric id to use for color later
        sheet_data['color_id'] = color_counter
        color_counter +=1
        #adds sheet to full data
        all_data[sheet_name] = sheet_data

#creates one big dataframe
combined_df = pandas.concat(all_data.values(), ignore_index=True)


#######################################
## map data
#######################################
# Initialize geolocator with longer timeout
geolocator = Nominatim(user_agent="ATL_food_map", timeout=10)

# need to do some cleaning because OpenStreetMap is not as robust as google maps
def clean_address(address):
    if not isinstance(address, str):
        return ""

    # Replace '#' with 'Unit ' to standardize
    address = address.replace("#", "Unit ")

    # Remove unit/suite/apartment identifiers (numeric or letter suffixes)
    address = re.sub(
        r'\b(?:Unit|Suite|Ste|Apt|Apartment)\s*\w+\b',
        '',
        address,
        flags=re.IGNORECASE
    )

    # Clean up excess whitespace and dangling commas
    address = re.sub(r'\s{2,}', ' ', address).strip().rstrip(',')

    # Expand cardinal direction abbreviations
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

    return address


# Caching decorator for geocoding
@lru_cache(maxsize=None)
def try_geocode(query):
    try:
        location = geolocator.geocode(query, country_codes='US')
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocode error for '{query}': {e}")
    return None, None

#slightly alternative method for use with name query only
def name_try_geocode(query):
    try:
        location = lambda query: geolocator.geocode("%s, Atlanta GA" % query)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocode error for '{query}': {e}")
    return None, None

def geocode_with_fallback(row):
    address = clean_address(row.get('Location', ''))
    name = row.get('Name', '')

    #trys to geocode based on the address
    lat, lon = try_geocode(address)

    #if address doesn't work, falls back to trying just restaurant name
    if lat is None or lon is None:
        #uses alternative function
        lat, lon = name_try_geocode(name)
        #if fails again, doesn't geocode
        if lat is None or lon is None:
            print(f"WARNING: Geocoding failed for both address and name -> '{address}' / '{name}'")

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
        return folium.Map(location=center, zoom_start=11, tiles=None)
    else:
        print("Could not geocode city center.")
        return None

# Add markers
def add_markers_to_map(df, food_map):
    # Colors to map (should align with expected color_id values)
    colors = ['blue', 'green', 'pink', 'red']

    # Group markers by place_type
    for group_name, df_group in df.groupby('place_type'):
        feature_group = folium.FeatureGroup(group_name).add_to(food_map)

        for _, row in df_group.iterrows():
            # Use modulo to ensure color_id doesn't go out of bounds
            color_index = int(row['color_id']) % len(colors)
            icon_color = colors[color_index]

            #text to go in popup, <strong> is bold, and add parameters to ensure text fits nicer
            iframe = folium.IFrame(f'<strong>{row['Name']}</strong><br><br><r>Rating: {row['Stars (of 10)']} of 10<br><br>{row['Additional Notes']}')
            popup = folium.Popup(iframe, min_width=200, max_width=400)

            #adds marker to feature group on map
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color=icon_color)
            ).add_to(feature_group)

        feature_group.add_to(food_map)


# Main pipeline
def generate_food_map(df):
    #df = apply_geocoding(df)
    #df.to_pickle('df_food_geocode.pkl')
    df = pandas.read_pickle('df_food_geocode.pkl')
    food_map = create_map()
    #setting the initial tile to None and declaring here removes the header from the layer control title
    folium.TileLayer('cartodb positron', control=False).add_to(food_map)

    if food_map:
        add_markers_to_map(df, food_map)
        folium.LayerControl().add_to(food_map)

        food_map.save('ATL_food_map.html')
        print("Food map saved as ATL_food_map.html.")
    else:
        print("Failed to create food map.")

# Example usage:
generate_food_map(combined_df)



'''
Old Code
'''
# # Add markers
# def add_markers_to_map(df, food_map):
#     for _, row in df.iterrows():
#         group_name, color = get_group_color(row)
#         folium.Marker(
#             location=[row['latitude'], row['longitude']],
#             popup=row['Name'],
#             icon=folium.Icon(color=color)
#         ).add_to(food_map)
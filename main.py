'''
TO DO:
- add custom markers to map, using clip art saved locally
- contribute to openstreetmap for places that I want
'''


import time
import pandas
from geopy.geocoders import Nominatim
from functools import lru_cache
import folium
import re
from branca.element import Template, MacroElement


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
    if sheet_name not in ['General Notes']:
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

# Apply geocoding and update DataFrame
def apply_geocoding(df):
    df['coordinates'] = df.apply(geocode_with_fallback, axis=1)
    df[['latitude', 'longitude']] = pandas.DataFrame(df['coordinates'].tolist(), index=df.index)
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

# Create map with geocoded city center
def create_map(city_address='Atlanta, Georgia, USA'):
    center = try_geocode(city_address, False)
    if center[0] is not None and center[1] is not None:
        return folium.Map(location=center, zoom_start=11, tiles=None)
    else:
        print("Could not geocode city center.")
        return None


# Add markers, DEFAULT ICON CUSTOM COLOR
def add_markers_to_map(df, food_map):
    # Colors to map (should align with expected color_id values)
    colors = ['blue', 'green', 'pink', 'red', 'black']
    #icustom cons associated with groups
    icon_dict = {
        'To Try':'question',
        'Restaurants':'bowl-rice',
        'Dessert Only':'ice-cream',
        'Coffee and Bakery':'mug-hot',
        'Bars':'martini-glass'
    }

    # Group markers by place_type
    for group_name, df_group in df.groupby('place_type'):
        feature_group = folium.FeatureGroup(group_name).add_to(food_map)

        for _, row in df_group.iterrows():
            # Use modulo to ensure color_id doesn't go out of bounds
            color_index = int(row['color_id']) % len(colors)
            icon_color = colors[color_index]

            if group_name != 'To Try':
                #text to go in popup, <strong> is bold, and add parameters to ensure text fits nicer
                iframe = folium.IFrame(f'<strong>{row['Name']}</strong><br><br>Rating: {row['Stars (of 10)']} of 10<br><br>{row['Additional Notes']}')
            else:
                iframe = folium.IFrame(f'<strong>{row['Name']}</strong><br><br>Havent Tried!<br><br>Place Type: {row['Type']}')

            #sets popup width and height parameters
            popup = folium.Popup(iframe, min_width=200, max_width=400)

            #adds marker to feature group on map, Note: prefix='fa' is required for custom icon to show up, it stands for fontawesome
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color=icon_color, icon=icon_dict[group_name], prefix='fa')
            ).add_to(feature_group)

        feature_group.add_to(food_map)

#creates a legend which associates the marker colors with a place type
def add_color_legend(food_map):
    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        z-index: 9999;
        background-color: white;
        border: 2px solid #ccc;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        font-size: 14px;
    ">
        <b>Legend</b><br>
        <i style="background: blue; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> To Try<br>
        <i style="background: green; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Restaurants<br>
        <i style="background: pink; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Dessert Only<br>
        <i style="background: red; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Coffee and Bakery<br>
        <i style="background: black; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Bars
    </div>
    {% endmacro %}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    food_map.get_root().add_child(legend)

#specifies that the version showing is not complete, thats all
def draft_text(food_map):
    # HTML template for top-center watermark
    html = """
    {% macro html(this, kwargs) %}
    <style>
        #draft-watermark {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(255, 0, 0, 0.6);
            color: white;
            padding: 5px 12px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            z-index: 9999;
            pointer-events: none;
        }
    </style>
    <div id='draft-watermark'>DRAFT VERSION</div>
    {% endmacro %}
    """

    # Add the macro to the map
    watermark = MacroElement()
    watermark._template = Template(html)
    food_map.get_root().add_child(watermark)



# Main pipeline
def generate_food_map(df):
    #df = apply_geocoding(df)
    #df.to_pickle('df_food_geocode.pkl')
    df = pandas.read_pickle('df_food_geocode.pkl')
    food_map = create_map()
    #setting the initial tile to None and declaring here removes the header from the layer control title
    folium.TileLayer('cartodb positron', control=False).add_to(food_map)

    if food_map:
        #adds locations on map
        add_markers_to_map(df, food_map)
        #adds selectable layers
        folium.LayerControl().add_to(food_map)
        #adds color legend to make it more readable
        add_color_legend(food_map)
        #adds text stating the map is a draft
        draft_text(food_map)

        food_map.save('index.html')
        print("Food map saved as index.html.")
    else:
        print("Failed to create food map.")

# Example usage:
generate_food_map(combined_df)



#################################################################

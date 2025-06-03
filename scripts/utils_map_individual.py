import utils_geocoding
from geopy.geocoders import Nominatim
import folium
from branca.element import Template, MacroElement
import pandas
from folium.plugins import GroupedLayerControl, FeatureGroupSubGroup


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

    #adds groups to be able to be selectable layers
    #MUST COME AFTER MARKERS ARE ADDED
    folium.LayerControl(collapsed=False).add_to(food_map)

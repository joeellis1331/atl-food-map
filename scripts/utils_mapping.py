import utils_geocoding
import folium

def create_map(city_center):
# Create map with geocoded city center
    city_center = 'Atlanta, Georgia, USA'
    cc_coordnates = utils_geocoding.try_geocode(city_center, False)
    #checks to ensure both latitude and longitude are found
    if cc_coordnates[0] is not None and cc_coordnates[1] is not None:
        #creates intial folium map
        folium_map = folium.Map(location=cc_coordnates, zoom_start=10, tiles=None)
        #setting the initial tile to None in the above live and declaring it in the below line here removes the header from the layer control title
        folium.TileLayer('cartodb positron', control=False).add_to(folium_map)
    else:
        raise Exception(f'Error: Could not geocode {city_center}, food map not created')

    return folium_map


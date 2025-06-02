import argparse
import os
import pandas
import folium
import utils_dataframe
import utils_geocoding
import utils_map_elements

#define arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--gsheet_path',
        help='filepath to the downloaded .xlsx of the running google sheet with this information on my drive'
        )
    parser.add_argument(
        '--geocode',
        help='use flag when geocoding needs to run again (i.e. new places or updated addesses/names)',
        action="store_true"
    )
    return parser.parse_args()


def main():
    #load args
    args = parse_args()

    #runs if there is an update to the ATL food list sheet
    if args.geocode:
        print('Running geocoding...')
        #combines all sheets to one
        df = utils_dataframe.reformat_sheet(args.gsheet_path)
        #uses OpenStreetMap address with place name as a fallback to geocode
        df['coordinates'] = df.apply(utils_geocoding.geocode_with_fallback, axis=1)
        df[['latitude', 'longitude']] = pandas.DataFrame(df['coordinates'].tolist(), index=df.index)
        df = df.dropna(subset=['latitude', 'longitude'])
        #saves to a pickle for ease of recall later, geocoding takes time
        df.to_pickle('df_food_geocode.pkl')


    #no new places, used to update map without geocoding again
    print('updating food map...')
    #read pickle file with geocoded coords
    df = pandas.read_pickle('df_food_geocode.pkl')

    # Create map with geocoded city center
    city_center = 'Atlanta, Georgia, USA'
    cc_coordnates = utils_geocoding.try_geocode(city_center, False)
    #checks to ensure both latitude and longitude are found
    if cc_coordnates[0] is not None and cc_coordnates[1] is not None:
        #creates intial folium map
        food_map = folium.Map(location=cc_coordnates, zoom_start=10, tiles=None)
        #setting the initial tile to None in the above live and declaring it in the below line here removes the header from the layer control title
        folium.TileLayer('cartodb positron', control=False).add_to(food_map)
    else:
        raise Exception(f'Error: Could not geocode {city_center}, food map not created')


    #adds locations on map
    utils_map_elements.add_markers_to_map(df, food_map)
    #adds color legend to make it more readable
    utils_map_elements.add_color_legend(food_map)
    #adds text stating the map is a draft
    utils_map_elements.draft_text(food_map)

    #save map to use with GitHub Pages
    food_map.save('../docs/individuals.html')
    print("Food map successfully created, saved as individuals.html")



if __name__ == '__main__':
    main()
import argparse
import os
import pandas
import folium
import utils_dataframe
import utils_geocoding
import map_individual
import utils_html_elements
import utils_mapping
import map_choropleth
from branca.element import Template, MacroElement, Element

#define arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'gsheet_path',
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

    ####################################
    # update geocoding, or if changes to ATL food list google sheet
    ######################################
    if args.geocode:
        print('Running geocoding...')
        #combines all sheets to one
        df_gsheet = utils_dataframe.reformat_sheet(args.gsheet_path)
        #uses OpenStreetMap address with place name as a fallback to geocode
        df_gsheet['coordinates'] = df_gsheet.apply(utils_geocoding.geocode_with_fallback, axis=1)
        df_gsheet[['latitude', 'longitude']] = pandas.DataFrame(df_gsheet['coordinates'].tolist(), index=df_gsheet.index)
        df_gsheet = df_gsheet.dropna(subset=['latitude', 'longitude'])
        #saves to a pickle for ease of recall later, geocoding takes time
        df_gsheet.to_pickle('df_food_geocode.pkl')


    ####################################################
    # converts each xlsx sheet to an html
    # to be in displayed as a table on webpage
    ####################################################
    utils_dataframe.sheet_to_html(args.gsheet_path)


    ####################################################
    ##          updating map section                  ##
    ####################################################
    print('updating maps...')
    #read pickle file with geocoded coords
    df_gsheet = pandas.read_pickle('df_food_geocode.pkl')

    ################## place by place map #############
    #initialize the folium map
    individuals_map = utils_mapping.create_map(city_center='Atlanta, Georgia, USA')
    #adds locations on map
    map_individual.add_markers_to_map(df_gsheet, individuals_map)
    #html legend element to add
    utils_html_elements.add_html_element(individuals_map, utils_html_elements.indv_places_legend)
    individuals_map.save('./sub_pages/folium_maps/individuals.html')
    print("Individual locations map successfully created, saved as individuals.html")

    ################# choropleth map #################
    choro_map = utils_mapping.create_map(city_center='Atlanta, Georgia, USA')
    #loads county shape files and creates on big geojson
    df_geo = map_choropleth.curate_geojson()
    #calculate scoring for each area, add to geojson
    df_geo = map_choropleth.score_areas(df_gsheet, df_geo)
    #make choropleth
    map_choropleth.map_scored_areas(choro_map, df_geo)

    ## adding legend elements
    # replaces string placeholders in html with actual values
    choro_legend_html = utils_html_elements.choro_legend_template.format(
        rating_min=0.0,
        rating_max=5.0,
        reviews_min=int(df_geo['total_ratings'].min()),
        reviews_max=int(df_geo['total_ratings'].max())
    )
    #adds the legend to the choropleth map
    utils_html_elements.add_html_element(choro_map, choro_legend_html)

    #removes black box when clicking, I.E. focus outline
    # MUST BE PLACED JUST BEFORE SAVE
    choro_map.get_root().header.add_child(Element("""
    <style>
    path.leaflet-interactive:focus {
        outline: none;
    }
    </style>
    """))
    #saves map
    choro_map.save('./sub_pages/folium_maps/areas.html')
    print("Choropleth map successfully created, saved as areas.html")


    #########################################
    # saves final pickle file
    # can catch small changes to place names or ratings
    ##########################################
    df_gsheet.to_pickle('df_food_geocode.pkl')


if __name__ == '__main__':
    main()
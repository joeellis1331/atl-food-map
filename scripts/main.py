import argparse
import os
import pandas
import folium
import utils_dataframe
import utils_geocoding
import map_individual
import utils_html_elements
import utils_mapping
import utils_color_to_css
import map_choropleth
from branca.element import Template, MacroElement, Element

#define arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'gsheet_path',
        help='filepath to the downloaded .xlsx of the running google sheet with this information on my drive'
        )
    return parser.parse_args()


def main():
    #load args
    args = parse_args()

    ####################################################
    # converts each xlsx sheet to an html to be in displayed as a table on webpage
    ####################################################
    utils_dataframe.sheet_to_html(args.gsheet_path)


    #####################################
    # Updating the master dataframe
    #######################################
    ###### Finds new entries ##################
    print("Finding new entires....")
    #combines all sheets from new into one for checking
    df_gsheet_new = utils_dataframe.reformat_sheet(args.gsheet_path)
    #loads previous data
    df_gsheet_old = pandas.read_pickle('df_master.pkl')
    #finds new entries and/or changes to old ones
    new_entries = utils_dataframe.find_new_entries(df_gsheet_new, df_gsheet_old)

    ####### Geocodes new entries ##################
    if not new_entries.empty:
        print('Geocoding new entries......')
        #collects all errors for geocoding
        geocode_errors = []
        #tries geocoding
        new_entries['coordinates'] = new_entries.apply(lambda row: utils_geocoding.geocode_with_fallback(row, geocode_errors), axis=1)
        #log for errors
        if geocode_errors:
            with open("geocode_errors.log", 'w') as file:
                file.write('\n'.join(geocode_errors))
            f"\n{len(geocode_errors)} geocoding failures. See ./log/geocoding_errors.log\n"
        #saves cache for geocoding
        utils_geocoding.save_cache()
        #### splits lat and long into new columns, drops any rows that didnt get geocoded
        new_entries[['latitude', 'longitude']] = pandas.DataFrame(new_entries['coordinates'].tolist(), index=new_entries.index)
        new_entries = new_entries.dropna(subset=['latitude', 'longitude'])
        #### update master datframe #####################
        df_master = pandas.concat([df_gsheet_old, new_entries], ignore_index=True)
        df_master.to_pickle('df_master.pkl') #save
    else:
        print('No new entries, continuing to mapping...')



    ####################################################
    ##          updating map section                  ##
    ####################################################
    print('updating maps...')
    #read pickle file with geocoded coords
    df_master = pandas.read_pickle('df_master.pkl')

    ################## place by place map #############
    #initialize the folium map
    individuals_map = utils_mapping.create_map(city_center='Atlanta, Georgia, USA')
    #adds locations on map
    map_individual.add_markers_to_map(df_master, individuals_map)
    #html legend element to add
    utils_html_elements.add_html_element(individuals_map, utils_html_elements.indv_places_legend)
    individuals_map.save('./sub_pages/folium_maps/individuals.html')
    print("Individual locations map successfully created, saved as individuals.html")

    ################# choropleth map #################
    choro_map = utils_mapping.create_map(city_center='Atlanta, Georgia, USA')
    #loads county shape files and creates on big geojson
    df_geo = map_choropleth.curate_geojson()
    #calculate scoring for each area, add to geojson
    df_geo = map_choropleth.score_areas(df_master, df_geo)

    #this defines some useful parameters to use throughout
    choro_meta_dict = {
        'ratings_color':'Oranges',
        'ratings_min':df_geo['bayes_avg'][df_geo['bayes_avg'].notna()].min(),
        'ratings_max':df_geo['bayes_avg'][df_geo['bayes_avg'].notna()].max(),
        'reviews_color':'Greens',
        'reviews_min':df_geo['total_ratings'].min(),
        'reviews_max':df_geo['total_ratings'].max()
    }

    #make choropleth
    map_choropleth.map_scored_areas(choro_map, df_geo, choro_meta_dict)

    ## adding legend elements
    # replaces string placeholders in html with actual values
    choro_legend_html = utils_html_elements.choro_legend_template.format(
        ratings_color=utils_color_to_css.make_HTML_cmap_from_branca(
            choro_meta_dict['ratings_color'],
            choro_meta_dict['ratings_min'],
            choro_meta_dict['ratings_max']
            ),
        reviews_color=utils_color_to_css.make_HTML_cmap_from_branca(
            choro_meta_dict['reviews_color'],
            choro_meta_dict['reviews_min'],
            choro_meta_dict['reviews_max']
            ),
        rating_min=choro_meta_dict['ratings_min'],
        rating_max=choro_meta_dict['ratings_max'],
        reviews_min=choro_meta_dict['reviews_min'],
        reviews_max=choro_meta_dict['reviews_max']
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

if __name__ == '__main__':
    main()
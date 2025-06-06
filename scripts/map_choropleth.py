from shapely.geometry import Point, Polygon, LineString
from shapely.ops import split, unary_union, snap
from shapely.geometry.base import BaseGeometry
import pandas
import numpy
import geopandas
import folium
from folium import FeatureGroup
from branca.element import Template, MacroElement, Element
import matplotlib.pyplot as plt
from itertools import combinations

'''
takes individual shapefiles/geojsons manually curated using QGIS and combined into one big geojson.
Find other maps from Koordinates.com by zip code for dekalb and gwinnett counties:
https://koordinates.com/data/?q=gwinnett+county+ga+boundary

Atlanta map from here:
https://dpcd-coaplangis.opendata.arcgis.com/datasets/7e91b75124fc47cbab7ffdb5de1cdd0a_0/explore?location=33.848672%2C-84.234272%2C10.93
'''
def curate_geojson():
    #read in coordinate polygons for atlanta neighborhoods
    df_atl = geopandas.read_file('./geographic_files/atlanta_neighborhoods_epsg3857_final.geojson')
    df_atl['map'] = 'Atlanta'
    df_atl['ZIPCODE'] = None

    #Read other counties coord polygons
    df_dekalb = geopandas.read_file('./geographic_files/dekalb_minus_atl_epsg3857_final.geojson')
    df_dekalb['map'] = 'Dekalb'
    df_dekalb = df_dekalb.rename(columns={'PO_NAME':'NAME', 'ZIP':'ZIPCODE'})

    df_gwin = geopandas.read_file('./geographic_files/gwinnett_epsg3857_final.geojson')
    df_gwin['map'] = ' Gwinnett'
    df_gwin = df_gwin.rename(columns={'POST_OFFIC':'NAME'})

    #merge all only grabbing geo's from each
    df_geo = pandas.concat([df_atl, df_dekalb, df_gwin], join='inner')
    #reset index
    df_geo.reset_index(drop=True, inplace=True)
    #convert formatting, otherwise it doesn't plot properly later in the code
    df_geo = df_geo.to_crs(crs=4326)

    return df_geo


'''
Match scores into areas
'''
def score_areas(df_ratings, df_geo):
    #intialize new column to hold list of scores which match to the area
    df_geo['score_list'] = numpy.empty((len(df_geo), 0)).tolist()

    #find where each place fits in the coordinate polygon
    #coordinates, geometry
    for row in df_ratings.itertuples():
        #these places don't have scores yet
        if row.place_type != 'To Try':
            point = Point(row.longitude, row.latitude)  # shapely Point expects (lon, lat)
            #true/false mask to see which polygon the coords are within
            s = df_geo.contains(point)
            #finds the index of that row in df_geo
            ind_list = s[s].index.values
            #makes sure it only has one match
            if ind_list.size != 0 and ind_list.size < 2:
                #gets score list
                list_to_update = df_geo.at[ind_list[0], 'score_list']
                list_to_update.append(row._8) #stars out of 5 column
                df_geo.at[ind_list[0], 'score_list'] = list_to_update

    #Count total ratings in each geographic region
    df_geo['total_ratings'] = df_geo['score_list'].apply(lambda x: len(x))
    #finds the avg score in each area
    df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: round(numpy.mean(x), 2) if len(x) > 0 else numpy.nan)
    #df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: numpy.mean(x) if len(x) > 0 else 0.0)
    #adds ID column, need it for choropleth map key_on parameter
    df_geo['ID'] = df_geo.index

    return df_geo

def map_scored_areas(folium_map, df_geo):
    #layer control feature groups
    fg1 = folium.FeatureGroup(name='Average Rating', overlay=False).add_to(folium_map)
    fg2 = folium.FeatureGroup(name='Total Reviews', overlay=False).add_to(folium_map)

    ##### choropleth of the average restaurant score #####
    cp_avg = folium.Choropleth(
        geo_data=df_geo,
        name='Average Rating',
        data=df_geo,
        columns=['ID', 'avg_score'],
        key_on='feature.properties.ID',
        bins=[0, 1, 2, 3, 4, 5],
        fill_color='Reds',
        fill_opacity=0.5,
        line_opacity=0.2,
        nan_fill_color='gray',
        nan_fill_opacity=0.2,
        legend_name='Rating (Out of 5.0)'
        ).geojson.add_to(fg1)
    #adding a tooltip/hover displaying information when hovering over
    #fields and aliases are in order, same length for each
    folium.GeoJsonTooltip(
        fields=['NAME', 'map', 'ZIPCODE', 'total_ratings', 'avg_score'],
        aliases=['Neighborhood', 'County', 'Zipcode', 'Total Places Reviewed', 'Average Rating']
        ).add_to(cp_avg)
    popup = folium.GeoJsonPopup(
        fields=["name", "change"],
        aliases=["State", "% Change"],
        localize=True,
        labels=True,
        style="background-color: yellow;",
    )

    ##### choropleth of the restaurants reviewed in each region #####
    cp_total = folium.Choropleth(
        geo_data=df_geo,
        name='Total Reviews',
        data=df_geo,
        columns=['ID', 'total_ratings'],
        key_on='feature.properties.ID',
        fill_color='Greens',
        fill_opacity=0.5,
        line_opacity=0.2,
        nan_fill_color='gray',
        nan_fill_opacity=0.2,
        legend_name='Rating (Out of 5.0)'
        ).geojson.add_to(fg2)
    #adding a tooltip/hover displaying information when hovering over
    #fields and aliases are in order, same length for each
    folium.GeoJsonTooltip(
        fields=['NAME', 'map', 'ZIPCODE', 'total_ratings', 'avg_score'],
        aliases=['Neighborhood', 'County', 'Zipcode', 'Total Places Reviewed', 'Average Rating']
        ).add_to(cp_total)

    #adds groups to be able to be selectable layers
    #MUST COME AFTER MARKERS ARE ADDED
    folium.LayerControl(collapsed=False).add_to(folium_map)

    return folium_map





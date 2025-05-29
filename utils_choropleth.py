from shapely.geometry import Point, Polygon, LineString
from shapely.ops import split, unary_union, snap
from shapely.geometry.base import BaseGeometry
import pandas
import numpy
import geopandas
import folium
import matplotlib.pyplot as plt
from itertools import combinations


#read in coordinate polygons for atlanta neighborhoods
df_atl = geopandas.read_file('atlanta_neighborhoods_epsg3857_final.geojson')
df_atl['map'] = 'Atlanta'


#Read other counties coord polygons
df_dekalb = geopandas.read_file('dekalb_minus_atl_epsg3857_final.geojson')
df_dekalb['map'] = 'Dekalb'
df_dekalb = df_dekalb.rename(columns={'PO_NAME':'NAME'})

df_gwin = geopandas.read_file('gwinnett_epsg3857_final.geojson')
df_gwin['map'] = ' Gwinnett'
df_gwin = df_gwin.rename(columns={'POST_OFFIC':'NAME'})

#merge all only grabbing geo's from each
df_geo = pandas.concat([df_atl, df_dekalb, df_gwin], join='inner')
#reset index
df_geo.reset_index(drop=True, inplace=True)
#convert formatting, otherwise it doesn't plot properly later in the code
df_geo = df_geo.to_crs(crs=4326)


'''
DOWNLOADED QGIS AND MANUALLY CURATED THE SETS TO ENSURE THERE IS NO OVERLAP IN POLYGONS, ETC ETC
'''



# #create folium map with atl center
# m = folium.Map(location=[33.7501, -84.3885], zoom_start=10, tiles="CartoDB positron")
# for _, r in df_geo.iterrows():
#     # Without simplifying the representation of each borough,
#     # the map might not be displayed
#     sim_geo = geopandas.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
#     geo_j = sim_geo.to_json()
#     geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "orange"})
#     geo_j.add_to(m)
# m.save('test_geomap.html')



'''
Match scores into counties
'''
#read in food map with coordiantes and ratings
df_food = pandas.read_pickle('df_food_geocode.pkl')
#intialize new column to hold list of scores which match to the area
df_geo['score_list'] = numpy.empty((len(df_geo), 0)).tolist()

#find where each place fits in the coordinate polygon
#coordinates, geometry
for row in df_food.itertuples():
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

#finds the avg score in each area
df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: numpy.mean(x) if len(x) > 0 else numpy.nan)
#df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: numpy.mean(x) if len(x) > 0 else 0.0)
#adds ID column, need it for choropleth map key_on parameter
df_geo['ID'] = df_geo.index

#create folium map with atl center
m = folium.Map(location=[33.7501, -84.3885], zoom_start=10, tiles="CartoDB positron")
folium.Choropleth(
    geo_data=df_geo,
    name='Choropleth',
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
    ).add_to(m)
m.save('test_geomap.html')
#folium.LayerControl().add_to(m)








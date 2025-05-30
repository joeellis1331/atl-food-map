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


#read in coordinate polygons for atlanta neighborhoods
df_atl = geopandas.read_file('atlanta_neighborhoods_epsg3857_final.geojson')
df_atl['map'] = 'Atlanta'
df_atl['ZIPCODE'] = None

#Read other counties coord polygons
df_dekalb = geopandas.read_file('dekalb_minus_atl_epsg3857_final.geojson')
df_dekalb['map'] = 'Dekalb'
df_dekalb = df_dekalb.rename(columns={'PO_NAME':'NAME', 'ZIP':'ZIPCODE'})

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

#Count total ratings in each geographic region
df_geo['total_ratings'] = df_geo['score_list'].apply(lambda x: len(x))
#finds the avg score in each area
df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: round(numpy.mean(x), 2) if len(x) > 0 else numpy.nan)
#df_geo['avg_score'] = df_geo['score_list'].apply(lambda x: numpy.mean(x) if len(x) > 0 else 0.0)
#adds ID column, need it for choropleth map key_on parameter
df_geo['ID'] = df_geo.index

#create folium map with atl center
m = folium.Map(location=[33.7501, -84.3885], zoom_start=10, tiles=None)
#above line tile=None and below line remove "cartodb positron" from layer control legend
folium.TileLayer('cartodb positron', control=False).add_to(m)

#layer control feature groups
fg1 = folium.FeatureGroup(name='Average Rating',overlay=False).add_to(m)
fg2 = folium.FeatureGroup(name='Total Reviews',overlay=False).add_to(m)

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


##### adding legend elements #####
#rating_min = round(df_geo['avg_score'].min(), 1)
#rating_max = round(df_geo['avg_score'].max(), 1)
rating_min = 0.0
rating_max = 5.0

reviews_min = int(df_geo['total_ratings'].min())
reviews_max = int(df_geo['total_ratings'].max())


legend_html = f"""
{{% macro html(this, kwargs) %}}
<div style="
    position: fixed;
    bottom: 20px;
    left: 10px;
    width: 150px;
    z-index: 1000;
    font-size: 14px;
    background-color: white;
    padding: 10px;
    border: 2px solid gray;
    border-radius: 8px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
    <div style="margin-bottom: 15px;">
        <b>Average Rating</b>
        <div style="
            width: 100%;
            height: 10px;
            background: linear-gradient(to right, #fff5f0, #fcbba1, #fc9272, #fb6a4a, #de2d26);
            margin-top: 5px;
            border: 1px solid #ccc;
        "></div>
        <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <span>{rating_min}</span><span>{rating_max}</span>
        </div>
    </div>

    <div>
        <b>Total Reviews</b>
        <div style="
            width: 100%;
            height: 10px;
            background: linear-gradient(to right, #e5f5e0, #a1d99b, #31a354);
            margin-top: 5px;
            border: 1px solid #ccc;
        "></div>
        <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <span>{reviews_min}</span><span>{reviews_max}</span>
        </div>
    </div>
</div>
{{% endmacro %}}
"""


#add html legend to map
macro = MacroElement()
macro._template = Template(legend_html)
m.get_root().add_child(macro)
#adds layer control to toggle between total reviews and avg score
folium.LayerControl(collapsed=False).add_to(m)


# MUST BE PLACED JUST BEFORE SAVE
#removes black box when clicking, I.E. focus outline
m.get_root().header.add_child(Element("""
<style>
path.leaflet-interactive:focus {
    outline: none;
}
</style>
"""))

#saves map
m.save('areas.html')








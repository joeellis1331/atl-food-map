from shapely.geometry import Point, Polygon
import pandas
import geopandas
import folium
import matplotlib.pyplot as plt

df_food = pandas.read_pickle('df_food_geocode.pkl')
df_atl_neighborhoods = geopandas.read_file('Atlanta_Official_Neighborhood_Statistical_Areas_(NSA).geojson')

#needed to  convert CRS to match geojson
df_dekalb = geopandas.read_file('kx-dekalb-county-ga-zip-codes-SHP/dekalb-county-ga-zip-codes.shp').to_crs(crs=4326)
df_gwin = geopandas.read_file('kx-gwinnett-county-ga-zip-code-SHP/gwinnett-county-ga-zip-code.shp').to_crs(crs=4326)


###### test to see geometries
#only grabs geo's from each county
s = pandas.concat([df_atl_neighborhoods['geometry'], df_dekalb['geometry'], df_gwin['geometry']])
df_geo = geopandas.GeoDataFrame(s, columns=['geometry'])

#create folium map with atl center
m = folium.Map(location=[33.7501, -84.3885], zoom_start=10, tiles="CartoDB positron")
for _, r in df_geo.iterrows():
    # Without simplifying the representation of each borough,
    # the map might not be displayed
    sim_geo = geopandas.GeoSeries(r["geometry"]).simplify(tolerance=0.001)
    geo_j = sim_geo.to_json()
    geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "orange"})
    geo_j.add_to(m)
m.save('test_geomap.html')
quit()

#unneccessary
#geoseries = geopandas.GeoSeries(df_atl_neighborhoods['geometry'], crs="EPSG:4326")

'''
1. determine which neightborhood the restaurant lat and long is within
'''
#coordinates, geometry
for row in df_food.itertuples():
    point = Point(row.longitude, row.latitude)  # shapely Point expects (lon, lat)
    l = list(df_atl_neighborhoods.contains(point))
    if True in l:
        print('yes')



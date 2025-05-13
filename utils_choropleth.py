from shapely.geometry import Point, Polygon
import pandas
import geopandas

df_food = pandas.read_pickle('df_food_geocode.pkl')
df_atl_neighborhoods = geopandas.read_file('Atlanta_Official_Neighborhood_Statistical_Areas_(NSA).geojson')

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



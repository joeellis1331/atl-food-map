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
df_atl_neighborhoods = geopandas.read_file('Atlanta_Official_Neighborhood_Statistical_Areas_(NSA).geojson')
df_atl_neighborhoods['map'] = 'Atlanta'
#Read other counties coord polygons, needed to convert CRS to match geojson
df_dekalb = geopandas.read_file('kx-dekalb-county-ga-zip-codes-SHP/dekalb-county-ga-zip-codes.shp').to_crs(crs=4326)
df_dekalb['map'] = 'Dekalb'
df_gwin = geopandas.read_file('kx-gwinnett-county-ga-zip-code-SHP/gwinnett-county-ga-zip-code.shp').to_crs(crs=4326)
df_gwin['map'] = ' Gwinnett'
#merge all only grabbing geo's from each
df_geo = pandas.concat([df_atl_neighborhoods, df_dekalb, df_gwin], join='inner')
#convert to dataframe rather than series
#df_geo = geopandas.GeoDataFrame(s, columns=['geometry'])
df_geo.reset_index(drop=True, inplace=True)



'''
find overlapping of polygons
'''
overlapping_pairs = []
for i in range(len(df_geo)):
    for j in range(i + 1, len(df_geo)):
        if df_geo.at[i, 'geometry'].intersects(df_geo.at[j, 'geometry']):
            overlapping_pairs.append((i, j))


'''
handling overlapping polygons
'''
def split_intersection_middle(
    poly1: BaseGeometry,
    poly2: BaseGeometry,
    min_overlap_area: float = 1e-8,
    snap_tolerance: float = 1e-6
) -> tuple[Polygon, Polygon]:
    """
    Split the intersection between two polygons and return adjusted polygons
    with no overlap, distributing half of the intersection to each.

    Parameters:
        poly1, poly2: Shapely polygons
        min_overlap_area: below this, overlaps are ignored
        snap_tolerance: tolerance for snapping edges to reduce slivers
    Returns:
        (adjusted_poly1, adjusted_poly2)
    """

    # --- Geometry pre-cleaning ---
    poly1 = poly1.buffer(0)
    poly2 = poly2.buffer(0)
    poly1 = snap(poly1, poly2, snap_tolerance)
    poly2 = snap(poly2, poly1, snap_tolerance)

    intersection = poly1.intersection(poly2)

    if intersection.is_empty or intersection.area < min_overlap_area:
        return poly1, poly2

    def assign_by_overlap():
        area1 = poly1.intersection(intersection).area
        area2 = poly2.intersection(intersection).area
        if area1 >= area2:
            return intersection, Polygon()
        else:
            return Polygon(), intersection

    if not isinstance(intersection, Polygon):
        half1, half2 = assign_by_overlap()
    else:
        try:
            min_rect = intersection.minimum_rotated_rectangle
            if not isinstance(min_rect, Polygon):
                min_rect = intersection.envelope

            coords = list(min_rect.exterior.coords)
            edges = [(coords[i], coords[i+1]) for i in range(len(coords)-1)]
            longest_edge = max(edges, key=lambda e: LineString(e).length)

            p1, p2 = longest_edge
            midpoint = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            normal = (-dy, dx)
            length = 1e5

            split_line = LineString([
                (midpoint[0] - normal[0]*length, midpoint[1] - normal[1]*length),
                (midpoint[0] + normal[0]*length, midpoint[1] + normal[1]*length)
            ])

            split_polys = split(intersection, split_line)
            if len(split_polys.geoms) == 2:
                half1, half2 = split_polys.geoms
            else:
                half1, half2 = assign_by_overlap()
        except Exception:
            half1, half2 = assign_by_overlap()

    poly1_result = poly1.difference(intersection).union(half1).buffer(0)
    poly2_result = poly2.difference(intersection).union(half2).buffer(0)
    return poly1_result, poly2_result

for pair in overlapping_pairs:
    poly1, poly2 = df_geo.at[pair[0], 'geometry'], df_geo.at[pair[1], 'geometry']
    new_poly1, new_poly2 = split_intersection_middle(poly1, poly2, min_overlap_area=1e-5, snap_tolerance=1e-5)
    df_geo.at[pair[0], 'geometry'] = new_poly1
    df_geo.at[pair[1], 'geometry'] = new_poly2

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
    fill_color='YlGn',
    fill_opacity=0.5,
    line_opacity=0.2,
    legend_name='Rating (Out of 5.0)'
    ).add_to(m)
m.save('test_geomap.html')
#folium.LayerControl().add_to(m)








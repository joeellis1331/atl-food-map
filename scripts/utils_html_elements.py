from branca.element import Template, MacroElement

#function to actually add html elements to map
def add_html_element(folium_map, html):
    # Add the macro to the map
    element = MacroElement()
    element._template = Template(html)
    folium_map.get_root().add_child(element)

######## html elements #######
indv_places_legend = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed;
    bottom: 15px;
    left: 10px;
    z-index: 9999;
    background-color: white;
    border: 2px solid #ccc;
    border-radius: 5px;
    padding: 5px 5px;
    font-size: 10px;
    line-height: 1.5;
">
    <b>Legend</b><br>
    <div><span style="background: blue; width: 8px; height: 8px; display: inline-block; vertical-align: middle; margin-right: 3px;"></span><span style="vertical-align: middle;">To Try</span></div>
    <div><span style="background: green; width: 8px; height: 8px; display: inline-block; vertical-align: middle; margin-right: 3px;"></span><span style="vertical-align: middle;">Restaurants</span></div>
    <div><span style="background: pink; width: 8px; height: 8px; display: inline-block; vertical-align: middle; margin-right: 3px;"></span><span style="vertical-align: middle;">Dessert Only</span></div>
    <div><span style="background: red; width: 8px; height: 8px; display: inline-block; vertical-align: middle; margin-right: 3px;"></span><span style="vertical-align: middle;">Coffee and Bakery</span></div>
    <div><span style="background: black; width: 8px; height: 8px; display: inline-block; vertical-align: middle; margin-right: 3px;"></span><span style="vertical-align: middle;">Bars</span></div>
</div>
{% endmacro %}
"""

#Instead of interpolating immediately with an f-string, define the template as a regular string
#with placeholders, and format it later when you have the values.
choro_legend_template = """
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
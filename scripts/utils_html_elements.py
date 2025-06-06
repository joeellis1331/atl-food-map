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
        bottom: 10px;
        left: 10px;
        z-index: 9999;
        background-color: white;
        border: 2px solid #ccc;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        font-size: 14px;
    ">
        <b>Legend</b><br>
        <i style="background: blue; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> To Try<br>
        <i style="background: green; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Restaurants<br>
        <i style="background: pink; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Dessert Only<br>
        <i style="background: red; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Coffee and Bakery<br>
        <i style="background: black; width: 10px; height: 10px; float: left; margin-right: 6px;"></i> Bars
    </div>
    {% endmacro %}
    """

indv_watermark = """
    {% macro html(this, kwargs) %}
    <style>
        #draft-watermark {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(255, 0, 0, 0.6);
            color: white;
            padding: 5px 12px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            z-index: 9999;
            pointer-events: none;
        }
    </style>
    <div id='draft-watermark'>DRAFT VERSION</div>
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
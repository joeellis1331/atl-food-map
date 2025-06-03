from branca.element import Template, MacroElement

#function to actually add html elements to map
def add_html_element(food_map, html):
    # Add the macro to the map
    element = MacroElement()
    element._template = Template(html)
    food_map.get_root().add_child(element)

######## html elements #######
places_legend = """
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

watermark = """
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
import numpy
import matplotlib.cm as mpl_cm
import branca.colormap as cm
import matplotlib.colors

def convert_cmap_to_css_gradient(colors, n=5):
    stops = [f"{i * 100 / (n - 1):.0f}%" for i in range(n)]
    color_stops = ", ".join(f"{c} {s}" for c, s in zip(colors, stops))
    return f"linear-gradient(to right, {color_stops})"


def make_HTML_cmap_from_branca(colormap_name, min_val, max_val):
    bins = numpy.linspace(min_val, max_val, 6).tolist()

    #Create a branca LinearColormap using given bins and colormap name
    cmap = mpl_cm.get_cmap(colormap_name)
    n_bins = len(bins) - 1
    colors = [cmap(i / n_bins) for i in range(n_bins + 1)]

    # Convert RGBA tuples to hex
    hex_colors = [matplotlib.colors.to_hex(c) for c in colors]

    #return css styled string to use in HTML
    return convert_cmap_to_css_gradient(hex_colors)


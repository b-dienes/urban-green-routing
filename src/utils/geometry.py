from dataclasses import dataclass
from pyproj import Transformer
from utils.inputs import user_input, UserInput

@dataclass
class BoundingBoxMercator:
    xmin: object
    ymin: object
    xmax: object
    ymax: object

def bounding_box_mercator(user_input: UserInput):
    # This function transforms a two WGS84 (lat-long) coordinate pairs to Web Mercator

    sw_lon = user_input.sw_lon
    sw_lat = user_input.sw_lat
    ne_lon = user_input.ne_lon
    ne_lat = user_input.ne_lat

    # Transform from WGS84 to Web Mercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    # Transformation done here
    xmin, ymin = transformer.transform(sw_lon, sw_lat)
    xmax, ymax = transformer.transform(ne_lon, ne_lat)

    return BoundingBoxMercator(
        xmin = xmin, 
        ymin = ymin,
        xmax = xmax,
        ymax = ymax)

def tile_calculator(bbox_mercator: BoundingBoxMercator, resolution):
    # This function calculates width and height required for the NAIP request

    xmin = bbox_mercator.xmin
    ymin = bbox_mercator.ymin
    xmax = bbox_mercator.xmax
    ymax = bbox_mercator.ymax

    width  = int(round((xmax - xmin) / resolution))
    height = int(round((ymax - ymin) / resolution))
    print('Width: ', width)
    print('Height: ', height)
 
    return width, height

def bounding_box_osm(user_input: UserInput):

    xmin = user_input.sw_lon
    ymin = user_input.sw_lat
    xmax = user_input.ne_lon
    ymax = user_input.ne_lat

    # OSM requires WGS84 bbox as tuple: left, bottom, right, top
    bbox_osm = (xmin, ymin, xmax, ymax)
    print("bbox: ", bbox_osm)
    return bbox_osm
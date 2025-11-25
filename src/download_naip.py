# Import libraries
import requests
import os
from pyproj import Transformer

user = os.path.expanduser('~')
os.chdir(user + '/urban-green-routing/data/raw/')
output_folder = os.getcwd()
print("CURRENT USER FOLDER: ", user)
print("OUTPUT FOLDER: ", output_folder)

def bounding_box():
    # This function transforms a two WGS84 (lat-long) coordinate pairs to Web Mercator
    # No input parameters required
    # 2 user-defined Web Mercator coodinate pairs and resolution returned

    # Transform from WGS84 to Web Mercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    # USER INPUT:
    # SW and NE coordinates (lon, lat)
    # Resolution (min: 0.6 is the highest possible in NAIP)
    sw_lat, sw_lon = 44.043, -121.326
    ne_lat, ne_lon = 44.054, -121.312
    resolution = 0.6

    # Transformation done here
    xmin, ymin = transformer.transform(sw_lon, sw_lat)
    xmax, ymax = transformer.transform(ne_lon, ne_lat)

    return xmin, ymin, xmax, ymax, resolution


def tile_calculator(xmin, ymin, xmax, ymax, resolution):
    # This function calculates width and height required for the NAIP request
    # 5 input parameters, all defined and derived from used input in the bounding_box() function
    # Width (number of pixels) and height (number of pixels) returned
    width  = int(round((xmax - xmin) / resolution))
    height = int(round((ymax - ymin) / resolution))
    print('Width: ', width)
    print('Height: ', height)
    return width, height


def naip_downloader(xmin, ymin, xmax, ymax, width, height):
    # This function performs a request to GET NAIP satellite imagery
    # 6 input parameters, transformed bounding box coordinates, width, and height 
    # Image saved in project folder/data/raw
    print('NAIP DOWNLOADER RUNNING')

    url = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage"
    params = {
    "bbox": str(xmin) + ',' + str(ymin) + ',' + str(xmax) + ',' + str(ymax),
    "bboxSR": 102100,
    "imageSR": 102100,
    "size": str(width) + ',' + str(height),
    "adjustAspectRatio": True,
    "format": "jpgpng",
    "f": "image",
    "dpi":96}

    response = requests.get(url, params=params)

    with open('{0}/naip_test.jpg'.format(output_folder), 'wb') as f:
            f.write(response.content)

    print('NAIP DOWNLOADER FINISHED')

xmin, ymin, xmax, ymax, resolution = bounding_box()
width, height = tile_calculator(xmin, ymin, xmax, ymax, resolution)
naip_downloader(xmin, ymin, xmax, ymax, width, height)
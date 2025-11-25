# Import libraries
import requests
import os
from pyproj import Transformer

user = os.path.expanduser('~')
os.chdir(user + '/urban-green-routing/data/raw/')
output_folder = os.getcwd()
print("CURRENT USER FOLDER: ", user)
print("OUTPUT FOLDER: ", output_folder)


def user_input():
    # USER INPUT:
    # SW and NE coordinates (lon, lat)
    # Resolution (min: 0.6 meter/pixel is the highest possible in NAIP)
    sw_lat, sw_lon = 44.009502297007145, -121.34656587303277
    ne_lat, ne_lon = 44.06010437225738, -121.26681950157074
    resolution = 2.25

    return sw_lat, sw_lon, ne_lat, ne_lon, resolution

def bounding_box(sw_lat, sw_lon, ne_lat, ne_lon):
    # This function transforms a two WGS84 (lat-long) coordinate pairs to Web Mercator
    # No input parameters required
    # 2 user-defined Web Mercator coodinate pairs and resolution returned

    # Transform from WGS84 to Web Mercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    # Transformation done here
    xmin, ymin = transformer.transform(sw_lon, sw_lat)
    xmax, ymax = transformer.transform(ne_lon, ne_lat)

    return xmin, ymin, xmax, ymax


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


sw_lat, sw_lon, ne_lat, ne_lon, resolution = user_input()

if __name__ == "__main__":
    xmin, ymin, xmax, ymax = bounding_box(sw_lat, sw_lon, ne_lat, ne_lon)
    width, height = tile_calculator(xmin, ymin, xmax, ymax, resolution)
    naip_downloader(xmin, ymin, xmax, ymax, width, height)
# Import libraries
import requests
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_mercator, tile_calculator, BoundingBoxMercator


def naip_request(bbox_mercator: BoundingBoxMercator, width, height):
    print('NAIP DOWNLOADER RUNNING')
    xmin = bbox_mercator.xmin
    ymin = bbox_mercator.ymin
    xmax = bbox_mercator.xmax
    ymax = bbox_mercator.ymax

    url = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage"
    params = {
    "bbox": str(xmin) + ',' + str(ymin) + ',' + str(xmax) + ',' + str(ymax),
    "bboxSR": 102100,
    "imageSR": 102100,
    "size": str(width) + ',' + str(height),
    "adjustAspectRatio": True,
    "format": "tiff",
    "f": "image",
    "dpi":96}

    response = requests.get(url, params=params)
    return response.content

def naip_save(user_input: UserInput, response_content, output_folder):
    aoi_name = user_input.aoi_name
    output_path = output_folder / f"{aoi_name}.tif"

    with open(output_path, 'wb') as f:
            f.write(response_content)

    print('NAIP DOWNLOADER FINISHED: ', output_path)

def naip_downloader(user_input: UserInput, bbox_mercator: BoundingBoxMercator, width, height):

    response_content = naip_request(bbox_mercator, width, height)

    output_folder = get_data_folder("raw")

    naip_save(user_input, response_content, output_folder)

if __name__ == "__main__":
    user_input = user_input()
    bbox_mercator = bounding_box_mercator(user_input)
    width, height = tile_calculator(bbox_mercator, user_input.resolution)
    naip_downloader(user_input, bbox_mercator, width, height)
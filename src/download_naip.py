import logging
from pathlib import Path
import requests
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_mercator, tile_calculator, BoundingBoxMercator


logger = logging.getLogger(__name__)

class DownloadNaip:
    """
    Downloads NAIP imagery for a specified area of interest (AOI)
    and saves it to a local folder.
    """
    def __init__(self, user_input: UserInput, bbox_mercator: BoundingBoxMercator, width: int, height: int, raw_folder: Path) -> None:
        """
        Initialize DownloadNaip with user input, bounding box, image dimensions, and output folder.

        Args:
            user_input (UserInput): User input object.
            bbox_mercator (BoundingBoxMercator): Bounding box object in Web Mercator coordinates for the AOI.
            width (int): Width of the output image.
            height (int): Height of the output image.
            raw_folder (Path): Directory where the image will be saved.
        """
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder
        self.bbox_mercator: BoundingBoxMercator = bbox_mercator
        self.width = width
        self.height = height

    def naip_request(self) -> None:
        """
        Send a request to the NAIP ImageServer to download imagery for the specified bounding box.
        """
        
        logger.info("NAIP download started")

        xmin = self.bbox_mercator.xmin
        ymin = self.bbox_mercator.ymin
        xmax = self.bbox_mercator.xmax
        ymax = self.bbox_mercator.ymax

        url = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage"
        params = {
        "bbox": str(xmin) + ',' + str(ymin) + ',' + str(xmax) + ',' + str(ymax),
        "bboxSR": 102100,
        "imageSR": 102100,
        "size": str(self.width) + ',' + str(self.height),
        "adjustAspectRatio": True,
        "format": "tiff",
        "f": "image",
        "dpi":96}

        response = requests.get(url, params=params)
        self.response_content = response.content

    def naip_save(self) -> None:
        """
        Save the downloaded NAIP image to the raw data folder.
        """
        aoi_name = self.user_input.aoi_name
        output_path = self.raw_folder / f"{aoi_name}.tif"

        with open(output_path, 'wb') as f:
                f.write(self.response_content)

        logger.info("NAIP download finished")
        
    def naip_downloader(self) -> None:
        """
        Orchestrates the download and save process.
        Calls naip_request() to get image data and naip_save() to write it to disk.
        """
        self.naip_request()
        self.naip_save()

if __name__ == "__main__":
    user_input = user_input()
    bbox_mercator = bounding_box_mercator(user_input)
    width, height = tile_calculator(bbox_mercator, user_input.resolution)
    raw_folder = get_data_folder("raw")

    download_naip = DownloadNaip(user_input, bbox_mercator, width, height, raw_folder)
    download_naip.naip_downloader()
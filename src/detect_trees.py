import logging
from pathlib import Path
import torch
torch.set_num_threads(1)  # workaround for WinError 127
import detectree as dtr
import rasterio
import numpy as np
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


logger = logging.getLogger(__name__)

class DetectTrees:
    """
    Detect trees from a NAIP TIFF using detectree, and save a mask raster.
    """
    def __init__(self, user_input: UserInput, raw_folder: Path) -> None:
        """
        Initialize with user input and folder containing the TIFF file.

        Args:
            user_input (UserInput): AOI information including name.
            raw_folder (Path): Folder where input and output files are stored.
        """
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder
        self.input_tif = self.raw_folder / f"{self.user_input.aoi_name}.tif"

    def load_classifier(self) -> None:
        """
        Load pre-trained Detectree classifier and store it in self.clf.

        Raises:
            RuntimeError: If the classifier fails to load.
        """
        try:
            clf = dtr.Classifier()
        except RuntimeError as e:
            logger.error("Failed to load Detectree classifier: %s", e)
            raise

        self.clf = clf
        logger.info("Detectree classifier loaded for AOI: %s", self.user_input.aoi_name)

    def mask_predictor(self) -> None:
        """
        Predict a tree mask from the input TIFF and store it in self.mask_vis.

        The classifier returns a NumPy array of 0/1 values. This method converts it
        to an 8-bit visualization mask (0 → 0, 1 → 255).

        Raises:
            ValueError: If the input raster has invalid data or shape.
            MemoryError: If the image is too large to process.
        """
        try:
            mask_array = self.clf.predict_img(self.input_tif)
            mask_vis = (mask_array * 255).astype(np.uint8)
        except ValueError as e:
            logger.error("Invalid raster data: %s", e)
            raise
        except MemoryError as e:
             logger.error("Not enough memory to process raster: %s", e)
             raise

        self.mask_vis = mask_vis
        logger.info("Tree mask predicted")

    def mask_saver(self) -> None:
        """
        Save the predicted mask as a single-band uint8 TIFF.

        Raises:
            rasterio.errors.RasterioIOError: If the input TIFF file cannot be read by rasterio.
            PermissionError: If the output file cannot be written due to insufficient permissions.
        """
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask.tif"

        try:
            with rasterio.open(self.input_tif) as src:
                meta = src.meta.copy()
                meta.update(dtype=rasterio.uint8, count=1)
            with rasterio.open(output_path, 'w', **meta) as dst:
                dst.write(self.mask_vis, 1)
        except rasterio.errors.RasterioIOError as e:
            logger.error("Cannot read NAIP satellite image: %s", e)
            raise
        except PermissionError:
            logger.error("No permission to write tree mask raster: %s", output_path)
            raise

        logger.info("Tree mask raster saved to %s", output_path)

    def tree_detector(self, overwrite: bool = False) -> None:
        """
        Run the full detection pipeline: load model, predict mask, save output.
        """
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask.tif"

        if output_path.exists() and not overwrite:
            logger.info("Tree mask already exists at %s, skipping detection", output_path)
            return

        self.load_classifier()
        self.mask_predictor()
        self.mask_saver()

if __name__ == "__main__":
    user_input = user_input()
    raw_folder = get_data_folder("raw")

    detect_trees = DetectTrees(user_input, raw_folder)
    detect_trees.tree_detector(overwrite=False)
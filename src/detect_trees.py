from pathlib import Path
import detectree as dtr
import rasterio
import numpy as np
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


class DetectTrees:
    """
    Detect trees from a NAIP TIFF using detectree, and save a mask raster.
    """
    def __init__(self, user_input: UserInput, raw_folder: Path):
        """
        Initialize with user input and folder containing the TIFF file.

        Args:
            user_input (UserInput): AOI information including name.
            raw_folder (Path): Folder where input and output files are stored.
        """
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder
        self.input_tif = self.raw_folder / f"{self.user_input.aoi_name}.tif"

    def load_classifier(self):
        """
        Load pre-trained Detectree classifier and store it in self.clf.
        """
        clf = dtr.Classifier()
        self.clf = clf

    def mask_predictor(self):
        """
        Predict a tree mask from the input TIFF and store it in self.mask_vis.

        The classifier returns a NumPy array of 0/1 values. This method converts it
        to an 8-bit visualization mask (0 → 0, 1 → 255).
        """
        mask_array = self.clf.predict_img(self.input_tif)
        mask_vis = (mask_array * 255).astype(np.uint8)
        self.mask_vis = mask_vis

    def mask_saver(self):
        """
        Save the predicted mask as a single-band uint8 TIFF.
        """
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask.tif"

        with rasterio.open(self.input_tif) as src:
            meta = src.meta.copy()
            meta.update(dtype=rasterio.uint8, count=1)
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(self.mask_vis, 1)

    def tree_detector(self):
        """
        Run the full detection pipeline: load model, predict mask, save output.
        """
        self.load_classifier()
        self.mask_predictor()
        self.mask_saver()

if __name__ == "__main__":
    user_input = user_input()
    raw_folder = get_data_folder("raw")

    detect_trees = DetectTrees(user_input, raw_folder)
    detect_trees.tree_detector()
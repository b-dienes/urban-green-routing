import detectree as dtr
import rasterio
import numpy as np
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


def load_classifier():
    # Load pre-trained classifier
    clf = dtr.Classifier()
    print("Classifier loaded")
    return clf

def mask_predictor(clf, input_tif):
    # Predict tree mask
    mask_array = clf.predict_img(input_tif)  # Returns a numpy array directly

    mask_vis = (mask_array * 255).astype(np.uint8) # Scale mask for visualization (0 -> 0, 1 -> 255)
    print("Tree mask predicted")
    return mask_vis

def mask_saver(mask_vis, input_tif, output_path):
    # Save mask
    with rasterio.open(input_tif) as src:
        meta = src.meta.copy()
        meta.update(dtype=rasterio.uint8, count=1)  # Update metadata for single-band uint8 mask
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(mask_vis, 1)
    print("Done! Saved tree mask.")

def tree_detector(user_input: UserInput):
    aoi_name = user_input.aoi_name
    raw_folder = get_data_folder("raw")
    input_tif = raw_folder / f"{aoi_name}.tif"
    output_path = raw_folder / f"{aoi_name}_tree_mask.tif"

    clf = load_classifier()
    mask_vis = mask_predictor(clf, input_tif)
    mask_saver(mask_vis, input_tif, output_path)

if __name__ == "__main__":
    user_input = user_input()
    tree_detector(user_input)

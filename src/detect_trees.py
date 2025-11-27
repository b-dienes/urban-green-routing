from pathlib import Path
import detectree as dtr
import rasterio
import numpy as np

# Paths
project_dir = Path(__file__).parent.parent
input_tif = project_dir / "data" / "raw" / "naip_test.tif"
output_mask = project_dir / "data" / "raw" / "tree_mask.tif"

# Load pre-trained classifier
clf = dtr.Classifier()
print("Classifier loaded")

# Predict tree mask
mask_array = clf.predict_img(str(input_tif))  # Returns a numpy array directly
print("Tree mask predicted")
print(mask_array.shape, mask_array.dtype)




# Scale mask for visualization (0 -> 0, 1 -> 255)
mask_vis = (mask_array * 255).astype(np.uint8)

# Save mask
with rasterio.open(input_tif) as src:
    meta = src.meta.copy()
    meta.update(dtype=rasterio.uint8, count=1)  # Update metadata for single-band uint8 mask

    with rasterio.open(output_mask, 'w', **meta) as dst:
        dst.write(mask_vis, 1)

print("Done! Saved tree mask to:", output_mask)

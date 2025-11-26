from pathlib import Path
from segment_anything import sam_model_registry, SamPredictor
import torch
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt


project_root = Path.home() / "urban-green-routing" / "models" / "sam_vit_b_01ec64.pth"
print("THIS FOLDER: ", project_root)

checkpoint_path = project_root
model_type = "vit_b"

sam = sam_model_registry[model_type](checkpoint=checkpoint_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

sam.to(device=device)

predictor = SamPredictor(sam)
print("SAM model and predictor ready!")


# Example: load an image with Pillow
image_path = Path.home() / "urban-green-routing" / "data" / "raw" / "naip_test.tif"
image = Image.open(image_path).convert("RGB")
image_np = np.array(image)  # convert to NumPy array for SAM

predictor.set_image(image_np)


clicked_points = [
    (484.9265534465535, 723.8668331668327),
    (724.3335799864469, 835.4371809010163),
    (849.9588311037164, 917.7459244617942),
    (1056.321250524778, 1003.4468504304026),
    (1314.765929416332, 1164.914626429384),
    (1320.5033630812704, 1152.6201257188018),
    (1288.1278445434036, 1140.5305333533959),
    (1283.6198609495234, 1128.645849333166),
    (1387.7133002991206, 1031.7242020647418),
    (1101.0465253973755, 1119.4249738002295),
    (1077.4820657020925, 1179.0533022465538),
    (705.3155255753097, 1860.793515035295),
    (628.8457444493009, 1862.0787214407742),
    (815.6290753789359, 1948.6159527430361),
    (739.8018974556667, 1808.9568566809696),
    (849.2586429889734, 1751.1225684344083)
]


point_coords = np.array([[y, x] for x, y in clicked_points], dtype=np.float32)

# Labels: 1 = foreground (tree), 0 = background
point_labels = np.ones(len(point_coords), dtype=np.int32)

masks, scores, logits = predictor.predict(
    point_coords=point_coords,     # no specific points
    point_labels=point_labels,
    box=None,              # no bounding box
    multimask_output=True  # output multiple candidate masks
)

# Check results
print("Number of masks:", len(masks))
print("Scores:", scores)

plt.imshow(image_np)
plt.imshow(masks[0], alpha=0.5)  # overlay the first mask
plt.axis("off")
plt.show()
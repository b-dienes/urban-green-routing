from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import raster_to_vector


# Raster to vector: extract tree polygons
def extract_tree_polygons(aoi_name, raw_folder):

    input_raster = raw_folder / f"{aoi_name}_tree_mask_reprojected.tif"
    output_vector = raw_folder / f"{aoi_name}_tree_mask_polygons.gpkg"
    raster_to_vector(input_raster,output_vector)


# Tree buffer

# Street buffer


def process_vectors(user_input: UserInput):
    aoi_name = user_input.aoi_name
    raw_folder = get_data_folder("raw")
    extract_tree_polygons(aoi_name, raw_folder)

if __name__ == "__main__":
    user_input = user_input()
    process_vectors(user_input)
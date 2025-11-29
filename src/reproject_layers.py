from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import reproject_raster_layer, reproject_vector_layer


# Reproject satellite image
def reproject_naip_image(aoi_name, dst_crs, raw_folder):

    input_raster = raw_folder / f"{aoi_name}.tif"
    output_raster = raw_folder / f"{aoi_name}_reprojected.tif"

    reproject_raster_layer(dst_crs, input_raster, output_raster)

# Reproject tree mask
def reproject_tree_mask(aoi_name, dst_crs, raw_folder):

    input_raster = raw_folder / f"{aoi_name}_tree_mask.tif"
    output_raster = raw_folder / f"{aoi_name}_tree_mask_reprojected.tif"

    reproject_raster_layer(dst_crs, input_raster, output_raster)

# Reproject edges
def reproject_osm_edges(aoi_name, dst_crs, raw_folder):

    input_vector = raw_folder / f"{aoi_name}_edges.gpkg"
    output_vector = raw_folder / f"{aoi_name}_edges_reprojected.gpkg"

    reproject_vector_layer(dst_crs, input_vector, output_vector)

def reproject_layers(user_input: UserInput):
    aoi_name = user_input.aoi_name
    dst_crs = 'EPSG:5070' # EPSG:5070 for testing. Later it can change dynamically.
    raw_folder = get_data_folder("raw")
    reproject_naip_image(aoi_name, dst_crs, raw_folder)
    reproject_tree_mask(aoi_name, dst_crs, raw_folder)
    reproject_osm_edges(aoi_name, dst_crs, raw_folder)

if __name__ == "__main__":
    user_input = user_input()
    reproject_layers(user_input)
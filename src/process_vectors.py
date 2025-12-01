import geopandas as gpd
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import raster_to_vector, dissolve_vector, simplify_vector, buffer_vector


# Raster to vector: extract tree polygons
def extract_tree_polygons(aoi_name, raw_folder):
    input_raster_path = raw_folder / f"{aoi_name}_tree_mask_reprojected.tif"
    output_vector_path = raw_folder / f"{aoi_name}_tree_mask_polygons_reproj.gpkg"
    raster_to_vector(input_raster_path,output_vector_path)

def tree_buffer(aoi_name, raw_folder):
    input_vector_path = raw_folder / f"{aoi_name}_tree_mask_polygons_reproj.gpkg"
    output_vector_path = raw_folder / f"{aoi_name}_tree_buffer_polygons_reproj.gpkg"

    result = (
        gpd.read_file(input_vector_path)
        #.pipe(simplify_vector, tolerance = 2.5)
        #.pipe(dissolve_vector)
        .pipe(buffer_vector, distance = 1)
    )
    result.to_file(output_vector_path, driver="GPKG")

def road_buffer(aoi_name, raw_folder):
    input_vector_path = raw_folder / f"{aoi_name}_edges_reprojected.gpkg"
    output_vector_path = raw_folder / f"{aoi_name}_edges_buffer_reproj.gpkg"

    result = (
        gpd.read_file(input_vector_path)
        .pipe(buffer_vector, 1)
    )
    result.to_file(output_vector_path, driver="GPKG")

def process_vectors(user_input: UserInput):
    aoi_name = user_input.aoi_name
    raw_folder = get_data_folder("raw")
    extract_tree_polygons(aoi_name, raw_folder)
    tree_buffer(aoi_name, raw_folder)
    road_buffer(aoi_name, raw_folder)

if __name__ == "__main__":
    user_input = user_input()
    process_vectors(user_input)
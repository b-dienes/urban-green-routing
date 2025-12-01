import geopandas as gpd
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import raster_to_vector, dissolve_vector, simplify_vector, buffer_vector, clipping_vectors, calculate_area, join_by_attribute



def extract_tree_polygons(aoi_name, raw_folder):
    # Raster to vector: extract tree polygons
    input_raster_path = raw_folder / f"{aoi_name}_tree_mask_reprojected.tif"
    output_vector_path = raw_folder / f"{aoi_name}_tree_mask_polygons_reproj.gpkg"
    raster_to_vector(input_raster_path,output_vector_path)

def tree_buffer(aoi_name, raw_folder):
    # Buffers around trees
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
    # Buffers along roads
    input_vector_path = raw_folder / f"{aoi_name}_edges_reprojected.gpkg"
    output_vector_path = raw_folder / f"{aoi_name}_edges_buffer_reproj.gpkg"

    result = (
        gpd.read_file(input_vector_path)
        .pipe(buffer_vector, 2.5)
    )
    result.to_file(output_vector_path, driver="GPKG")

def clip_roads(aoi_name, raw_folder):
    # Clip road buffers with tree buffers
    input_vector_path = raw_folder / f"{aoi_name}_edges_buffer_reproj.gpkg"
    mask_vector_path = raw_folder / f"{aoi_name}_tree_buffer_polygons_reproj.gpkg"
    output_vector_path = raw_folder / f"{aoi_name}_edges_buffer_clipped.gpkg"

    input_vector = gpd.read_file(input_vector_path)
    mask_vector = gpd.read_file(mask_vector_path)

    clipping_vectors(input_vector, mask_vector, output_vector_path)

def calculate_areas(aoi_name, raw_folder):
    road_buffer_path = raw_folder / f"{aoi_name}_edges_buffer_reproj.gpkg"
    road_clip_path = raw_folder / f"{aoi_name}_edges_buffer_clipped.gpkg"
    edges_path = raw_folder / f"{aoi_name}_edges.gpkg"
    output_vector_path = raw_folder / f"{aoi_name}_edges_areas.gpkg"

    # Area of road buffers
    road_buffer = gpd.read_file(road_buffer_path)
    road_buffer_area = calculate_area(road_buffer)

    # Area of clipped road buffers
    road_clip = gpd.read_file(road_clip_path)
    road_clip_area = calculate_area(road_clip)

    # Join areas to edges based on ID
    result = (
        road_edges = gpd.read_file(edges_path)
        .pipe(join_by_attribute, road_buffer_area)
        .pipe(join_by_attribute, road_clip_area)
    )
    result.to_file(output_vector_path, driver="GPKG")

    # Calculate green index

def process_vectors(user_input: UserInput):
    aoi_name = user_input.aoi_name
    raw_folder = get_data_folder("raw")
    extract_tree_polygons(aoi_name, raw_folder)
    tree_buffer(aoi_name, raw_folder)
    road_buffer(aoi_name, raw_folder)
    clip_roads(aoi_name, raw_folder)
    calculate_areas(aoi_name, raw_folder)

if __name__ == "__main__":
    user_input = user_input()
    process_vectors(user_input)
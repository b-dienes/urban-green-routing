from pathlib import Path
import geopandas as gpd
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import (
    raster_to_vector,
    dissolve_vector,
    simplify_vector,
    add_id,
    buffer_vector,
    clipping_vectors,
    calculate_area,
    join_by_attribute,
    calculate_greendex
)


class ProcessVectors:

    def __init__(self, user_input: UserInput, raw_folder: Path):
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder

    def extract_tree_polygons(self):
        # Raster to vector: extract tree polygons
        input_raster_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_reprojected.tif"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_polygons_reproj.gpkg"
        raster_to_vector(input_raster_path,output_vector_path)

    def tree_buffer(self):
        # Buffers around trees
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_polygons_reproj.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_buffer_polygons_reproj.gpkg"

        result = gpd.read_file(input_vector_path).pipe(buffer_vector, distance = 1)
        result.to_file(output_vector_path, driver="GPKG")

    def road_buffer(self):
        # Buffers along roads
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_reprojected.gpkg"
        id_vector_path =  self.raw_folder / f"{self.user_input.aoi_name}_edges_id_reprojected.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"

        result = (
            gpd.read_file(input_vector_path)
            .pipe(add_id, id_vector_path)
            .pipe(buffer_vector, 2.5)
        )
        result.to_file(output_vector_path, driver="GPKG")

    def clip_roads(self):
        # Clip road buffers with tree buffers
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"
        mask_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_buffer_polygons_reproj.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_clipped.gpkg"

        input_vector = gpd.read_file(input_vector_path)
        mask_vector = gpd.read_file(mask_vector_path)

        clipping_vectors(input_vector, mask_vector, output_vector_path)

    def calculate_areas(self):
        road_buffer_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"
        road_clip_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_clipped.gpkg"
        edges_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_id_reprojected.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_greendex.gpkg"

        # Area calculations
        road_buffer_area = gpd.read_file(road_buffer_path).pipe(calculate_area)
        road_clip_area = gpd.read_file(road_clip_path).pipe(calculate_area)

        # Join areas to edges based on ID and calculate green index
        result = (
            gpd.read_file(edges_path)
            .pipe(join_by_attribute, road_buffer_area)
            .pipe(join_by_attribute, road_clip_area)
            .pipe(calculate_greendex)
        )
        result.to_file(output_vector_path, driver="GPKG")

    def process_vectors(self):
        self.extract_tree_polygons()
        self.tree_buffer()
        self.road_buffer()
        self.clip_roads()
        self.calculate_areas()

if __name__ == "__main__":
    user_input = user_input()
    raw_folder = get_data_folder("raw")

    process_vectors = ProcessVectors(user_input, raw_folder)
    process_vectors.process_vectors()
import logging
from pathlib import Path
from functools import wraps
import geopandas as gpd
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import (
    raster_to_vector,
    add_id,
    buffer_vector,
    clipping_vectors,
    calculate_area,
    join_by_attribute,
    calculate_greendex
)


logger = logging.getLogger(__name__)

def handle_errors(method):
    """
    Decorator to wrap vector processing methods for error handling.

    Raises:
        MemoryError: If the processing step exhausts memory.
        RuntimeError: For any other errors encountered during processing.

    Returns:
        the original method's result if successful.
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except MemoryError as e:
            logger.error("Memory error in %s: %s", method.__name__, e)
            raise
        except Exception as e:
            logger.error("Error in %s: %s", method.__name__, e)
            raise RuntimeError(f"{method.__name__} failed: {e}")
    return wrapper

class ProcessVectors:
    """
    Processing pipeline that extracts tree polygons, creates buffers,
    clips road buffers, and computes greendex metrics for road segments.
    """

    def __init__(self, user_input: UserInput, raw_folder: Path) -> None:
        """
        Initialize the processing object with user input and folder paths.
        
        Args:
            user_input (UserInput): Object containing AOI name and configuration parameters.
            raw_folder (Path): Folder where all intermediate and output vector files are stored.
        """
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder

    def _process_step(self, path: Path, method: callable, step_name: str, overwrite: bool) -> None:
        """
        Helper method to avoid repeating file existence checks for workflow steps.

        Args:
            path (Path): Path to the output file of this step.
            method (callable): The processing method to run if the file does not exist or overwrite=True.
            step_name (str): Name of the step for logging purposes.
            overwrite (bool): Whether to force rerun the step even if file exists.

        Behavior:
            - Logs that the step is skipped if file exists and overwrite is False.
            - Otherwise, calls the provided method.
        """
        if path.exists() and not overwrite:
            logger.info("%s already exists: skipping", step_name)                 
        else:
            method()


    @handle_errors
    def extract_tree_polygons(self) -> None:
        """
        Convert the tree raster mask into vector polygons.
        """
        input_raster_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_reprojected.tif"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_polygons_reproj.gpkg"
        raster_to_vector(input_raster_path,output_vector_path)
        logger.info("Tree raster mask converted to polygons: %s", output_vector_path)

    @handle_errors
    def tree_buffer(self) -> None:
        """
        Create buffer polygons around the extracted tree polygons to define influence zone around trees.
        """
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_polygons_reproj.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_buffer_polygons_reproj.gpkg"

        result = gpd.read_file(input_vector_path).pipe(buffer_vector, distance = 1)
        result.to_file(output_vector_path, driver="GPKG")
        logger.info("Tree polygon buffer prepared: %s", output_vector_path)

    @handle_errors
    def road_buffer(self) -> None:
        """
        Add unique IDs to road edges and generate buffer polygons around them.
        """
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_reprojected.gpkg"
        id_vector_path =  self.raw_folder / f"{self.user_input.aoi_name}_edges_id_reprojected.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"

        result = (
            gpd.read_file(input_vector_path)
            .pipe(add_id, id_vector_path)
            .pipe(buffer_vector, 2.5)
        )
        result.to_file(output_vector_path, driver="GPKG")
        logger.info("Road buffer prepared: %s", output_vector_path)

    @handle_errors
    def clip_roads(self) -> None:
        """
        Clip road buffer polygons using tree buffer polygons.
        The result represents areas where trees overlap the road buffer zones.
        """
        input_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"
        mask_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_buffer_polygons_reproj.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_clipped.gpkg"

        input_vector = gpd.read_file(input_vector_path)
        mask_vector = gpd.read_file(mask_vector_path)

        clipping_vectors(input_vector, mask_vector, output_vector_path)
        logger.info("Road buffers clipped: %s", output_vector_path)

    @handle_errors
    def calculate_areas(self) -> None:
        """
        Compute road buffer and tree overlay areas, and calculate greendex metrics.

        Greendex compares tree-covered buffer area to total road buffer area
        and assigns a weight based on segment length and green coverage.
        """
        road_buffer_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"
        road_clip_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_clipped.gpkg"
        edges_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_id_reprojected.gpkg"
        output_vector_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_greendex.gpkg"

        road_buffer_area = gpd.read_file(road_buffer_path).pipe(calculate_area)
        road_clip_area = gpd.read_file(road_clip_path).pipe(calculate_area)

        result = (
            gpd.read_file(edges_path)
            .pipe(join_by_attribute, road_buffer_area)
            .pipe(join_by_attribute, road_clip_area)
            .pipe(calculate_greendex)
        )
        result.to_file(output_vector_path, driver="GPKG")
        logger.info("Greendex calculated: %s", output_vector_path)

    def process_vectors(self, overwrite: bool = False) -> None:
        """
        Orchestrates the full vector workflow: tree extraction, buffering, clipping, and greendex calculation.

        Uses _process_step helper to avoid repeated file existence checks and logging.
        """
        polygons_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_polygons_reproj.gpkg"
        self._process_step(polygons_path, self.extract_tree_polygons, "Tree polygons", overwrite)
        
        tree_buffer_path = self.raw_folder / f"{self.user_input.aoi_name}_tree_buffer_polygons_reproj.gpkg"
        self._process_step(tree_buffer_path, self.tree_buffer, "Tree buffers", overwrite)

        edges_buffer_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_reproj.gpkg"
        self._process_step(edges_buffer_path, self.road_buffer, "Road buffers", overwrite)

        edges_clipped_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_buffer_clipped.gpkg"
        self._process_step(edges_clipped_path, self.clip_roads, "Clipped road buffers", overwrite)
        
        areas_calculated_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_greendex.gpkg"
        self._process_step(areas_calculated_path, self.calculate_areas, "Area calculation", overwrite)

if __name__ == "__main__":
    user_input = user_input()
    raw_folder = get_data_folder("raw")

    process_vectors = ProcessVectors(user_input, raw_folder)
    process_vectors.process_vectors(overwrite=False)
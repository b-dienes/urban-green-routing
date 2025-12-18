import logging
from pathlib import Path
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import reproject_raster_layer, reproject_vector_layer


logger = logging.getLogger(__name__)

class ReprojectLayers:
    """
    Reproject raster and vector layers for a given AOI to a target CRS.
    """
    def __init__(self, user_input: UserInput, dst_crs: str, raw_folder: Path) -> None:
        """
        Initialize with AOI info, target CRS, and folder containing layers.

        Args:
            user_input (UserInput): AOI information including name.
            dst_crs (str or CRS): Target coordinate reference system.
            raw_folder (Path): Folder containing raw layers.
        """
        self.user_input: UserInput = user_input
        self.dst_crs = dst_crs
        self.raw_folder = raw_folder


    def reproject_all_layers(self) -> None:
        """
        Reproject all defined layers (NAIP satellite image, tree mask, OSM edges) to the target CRS.

        Uses the utility functions 'reproject_raster_layer' and 'reproject_vector_layer'
        depending on the layer type.

        Raises:
            PermissionError: If the output file cannot be written due to permissions.
            RuntimeError: If the reprojection function fails for any reason.
        """

        LAYERS = [
            {"input": "{aoi}.tif", "output": "{aoi}_reprojected.tif", "func": reproject_raster_layer},
            {"input": "{aoi}_tree_mask.tif", "output": "{aoi}_tree_mask_reprojected.tif", "func": reproject_raster_layer},
            {"input": "{aoi}_edges.gpkg", "output": "{aoi}_edges_reprojected.gpkg", "func": reproject_vector_layer}
        ]

        for layer in LAYERS:
            input_path = self.raw_folder / layer["input"].format(aoi=self.user_input.aoi_name)
            output_path = self.raw_folder / layer["output"].format(aoi=self.user_input.aoi_name)

            try:
                layer["func"](self.dst_crs, input_path, output_path)
            except PermissionError:
                logger.error("No permission to write reprojected layer to %s", output_path)
                raise
            except Exception as e:
                logger.error("Reprojection failed for %s: %s", layer["input"].format(aoi=self.user_input.aoi_name), e)
                raise

            logger.info("Layer reprojected: %s -> %s", layer["input"].format(aoi=self.user_input.aoi_name), layer["output"].format(aoi=self.user_input.aoi_name))

    def reproject_layers(self) -> None:
        """
        Run the reproject pipeline.
        """
        self.reproject_all_layers()

if __name__ == "__main__":
    user_input = user_input()
    dst_crs = 'EPSG:5070' # EPSG:5070 for testing. Later it can change dynamically.
    raw_folder = get_data_folder("raw")

    reprojector = ReprojectLayers(user_input, dst_crs, raw_folder)
    reprojector.reproject_layers()
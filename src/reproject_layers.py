from pathlib import Path
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import reproject_raster_layer, reproject_vector_layer


class ReprojectLayers:
    """
    Reproject raster and vector layers for a given AOI to a target CRS.
    """
    def __init__(self, user_input: UserInput, dst_crs, raw_folder: Path):
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

    def reproject_naip_image(self):
        """
        Reproject the NAIP TIFF to the target CRS.
        """
        input_raster = self.raw_folder / f"{self.user_input.aoi_name}.tif"
        output_raster = self.raw_folder / f"{self.user_input.aoi_name}_reprojected.tif"

        reproject_raster_layer(self.dst_crs, input_raster, output_raster)

    def reproject_tree_mask(self):
        """
        Reproject the predicted tree mask TIFF to the target CRS.
        """
        input_raster = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask.tif"
        output_raster = self.raw_folder / f"{self.user_input.aoi_name}_tree_mask_reprojected.tif"

        reproject_raster_layer(self.dst_crs, input_raster, output_raster)

    def reproject_osm_edges(self):
        """
        Reproject the OSM edges GeoPackage to the target CRS.
        """
        input_vector = self.raw_folder / f"{self.user_input.aoi_name}_edges.gpkg"
        output_vector = self.raw_folder / f"{self.user_input.aoi_name}_edges_reprojected.gpkg"

        reproject_vector_layer(self.dst_crs, input_vector, output_vector)

    def reproject_layers(self):
        """
        Reproject all layers (NAIP, tree mask, OSM edges) to the target CRS.
        """
        self.reproject_naip_image()
        self.reproject_tree_mask()
        self.reproject_osm_edges()

if __name__ == "__main__":
    user_input = user_input()
    dst_crs = 'EPSG:5070' # EPSG:5070 for testing. Later it can change dynamically.
    raw_folder = get_data_folder("raw")

    reproject_layers = ReprojectLayers(user_input, dst_crs, raw_folder)
    reproject_layers.reproject_layers()
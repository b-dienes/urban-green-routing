import logging
from pathlib import Path
import osmnx as ox
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_osm


logger = logging.getLogger(__name__)

class DownloadOsm:
    """
    Download and manage OpenStreetMap (OSM) network data for an AOI.
    Retrieves a street network graph, saves it, and optionally visualizes it.
    """
    def __init__(self, user_input: UserInput, bbox_osm: tuple[float, float, float, float], raw_folder: Path) -> None:
        """
        Initialize downloader with user input, bounding box, and output folder.

        Args:
            user_input (UserInput): AOI information including name.
            bbox_osm: Bounding box (west, south, east, north).
            raw_folder (Path): Folder to save outputs.
        """
        self.user_input: UserInput = user_input
        self.bbox_osm = bbox_osm
        self.raw_folder: Path = raw_folder

    def osm_request(self) -> None:
        """
        Retrieve the OSM graph for the bounding box and store it in response_content.

        Raises:
            ValueError: If the downloaded graph is empty.
            RuntimeError: For network or OSM data retrieval errors.
        """
        try:
            G = ox.graph_from_bbox(self.bbox_osm, network_type="walk", simplify=False)
        except Exception as e:
            logger.error(f"OSM download failed due to network or server error: {e}")
            raise

        if len(G.nodes) == 0 or len(G.edges) == 0:
            raise ValueError("Downloaded OSM graph is empty. Check AOI")

        logger.info("OSM graph retrieved: %dnodes, %dedges", len(G.nodes), len(G.edges))
        self.response_content = G

    def osm_save(self) -> None:
        """
        Save the downloaded graph as a GraphML file.

        Raises:
            PermissionError: If the output file cannot be written due to insufficient permissions.
        """
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_graph.graphml"

        try:
            ox.save_graphml(self.response_content, output_path)
        except PermissionError:
            logger.error("No permission to write OSM graph to %s", output_path)
            raise

        logger.info("OSM graph saved to %s", output_path)

    def osm_gpkg_save(self) -> None:
        """
        Save graph nodes and edges as GeoPackages.

        Raises:
            PermissionError: If the output file cannot be written due to insufficient permissions.        
        """
        output_path_nodes = self.raw_folder / f"{self.user_input.aoi_name}_nodes.gpkg"
        output_path_edges = self.raw_folder / f"{self.user_input.aoi_name}_edges.gpkg"

        nodes, edges = ox.graph_to_gdfs(self.response_content)

        try:
            nodes.to_file(output_path_nodes, driver="GPKG")
            edges.to_file(output_path_edges, driver="GPKG")
        except PermissionError:
            logger.error("No permission to write OSM GeoPackages to %s and %s", output_path_nodes, output_path_edges,)
            raise

        logger.info("%s_nodes.gpkg and %s_edges.gpkg saved", self.user_input.aoi_name, self.user_input.aoi_name)

    def osm_visualize(self) -> None:
        """
        Visualize the graph using OSMnx's built-in plotting.
        """
        ox.plot_graph(self.response_content, node_size=10, edge_color="green", edge_linewidth=1, figsize=(12, 12))

    def osm_graph_downloader(self, visualize: bool = False, overwrite: bool = False) -> None:
        """
        Run the full OSM download pipeline. Optionally visualize the graph.

        Args:
            visualize (bool): Show graph plot. Defaults to False.
        """
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_graph.graphml"        

        if output_path.exists() and not overwrite:
            logger.info("OSM graph already exists at %s, skipping download", output_path)
            self.response_content = ox.load_graphml(output_path)
            return

        self.osm_request()
        self.osm_save()
        self.osm_gpkg_save()
        
        if visualize:
            self.osm_visualize()

if __name__ == "__main__":
    user_input = user_input()
    bbox_osm = bounding_box_osm(user_input)
    raw_folder = get_data_folder("raw")

    download_osm = DownloadOsm(user_input, bbox_osm, raw_folder)
    download_osm.osm_graph_downloader(visualize=True, overwrite=False)
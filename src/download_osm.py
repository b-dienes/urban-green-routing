from pathlib import Path
import osmnx as ox
import matplotlib.pyplot as plt
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_osm


class DownloadOsm:

    def __init__(self, user_input: UserInput, bbox_osm, raw_folder: Path):
        self.user_input: UserInput = user_input
        self.bbox_osm = bbox_osm
        self.raw_folder: Path = raw_folder

    def osm_request(self):
        G = ox.graph_from_bbox(self.bbox_osm, network_type="walk", simplify=False)
        print("Graph retrieved: ", G)
        self.response_content = G

    def osm_save(self):
        # Save graph to disk as graphml
        output_path = self.raw_folder / f"{self.user_input.aoi_name}_graph.graphml"
        ox.save_graphml(self.response_content, output_path)

    def osm_visualize(self):
        # Visualize
        fig, ax = ox.plot_graph(self.response_content, node_size=10, edge_color="green", edge_linewidth=1, figsize=(12, 12))
        print("Plot succeeded")

    def osm_gpkg_save(self):
        # Convert graph to GeoDataFrames and save as standard GIS layers
        output_path_nodes = self.raw_folder / f"{self.user_input.aoi_name}_nodes.gpkg"
        output_path_edges = self.raw_folder / f"{self.user_input.aoi_name}_edges.gpkg"

        nodes, edges = ox.graph_to_gdfs(self.response_content)
        nodes.to_file(output_path_nodes, driver="GPKG")
        edges.to_file(output_path_edges, driver="GPKG")

    def osm_graph_downloader(self):
        self.osm_request()
        self.osm_save()
        self.osm_visualize()
        self.osm_gpkg_save()

if __name__ == "__main__":
    user_input = user_input()
    bbox_osm = bounding_box_osm(user_input)
    raw_folder = get_data_folder("raw")

    download_osm = DownloadOsm(user_input, bbox_osm, raw_folder)
    download_osm.osm_graph_downloader()
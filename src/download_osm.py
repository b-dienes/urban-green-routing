import osmnx as ox
import matplotlib.pyplot as plt
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_osm


def osm_request(bbox_osm):
    G = ox.graph_from_bbox(bbox_osm, network_type="walk", simplify=False)
    print("Graph retrieved: ", G)
    return G

def osm_save(user_input: UserInput, response_content, output_folder):
    # Save graph to disk as graphml
    aoi_name = user_input.aoi_name
    output_path = output_folder / f"{aoi_name}_graph.graphml"

    ox.save_graphml(response_content, output_path)

def osm_visualize(response_content):
    # Visualize
    fig, ax = ox.plot_graph(response_content, node_size=10, edge_color="green", edge_linewidth=1, figsize=(12, 12))
    print("Plot succeeded")

def osm_gpkg_save(user_input: UserInput, response_content,output_folder):
    # Convert graph to GeoDataFrames and save as standard GIS layers
    aoi_name = user_input.aoi_name
    output_path_nodes = output_folder / f"{aoi_name}_nodes.gpkg"
    output_path_edges = output_folder / f"{aoi_name}_edges.gpkg"

    nodes, edges = ox.graph_to_gdfs(response_content)
    nodes.to_file(output_path_nodes, driver="GPKG")
    edges.to_file(output_path_edges, driver="GPKG")

def osm_graph_downloader(user_input, bbox_osm):
    response_content = osm_request(bbox_osm)
    output_folder = get_data_folder("raw")
    osm_save(user_input, response_content, output_folder)
    osm_visualize(response_content)
    osm_gpkg_save(user_input, response_content,output_folder)


if __name__ == "__main__":
    user_input = user_input()
    bbox_osm = bounding_box_osm(user_input)
    osm_graph_downloader(user_input, bbox_osm)
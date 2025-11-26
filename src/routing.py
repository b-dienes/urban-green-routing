import osmnx as ox
import matplotlib.pyplot as plt
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput
from utils.geometry import bounding_box_osm

def osm_request(bbox_osm):
    G = ox.graph_from_bbox(bbox_osm, network_type="walk", simplify=False)
    print("Graph retrieved: ", G)
    return G

def osm_save(response_content, output_folder):
    # Save graph to disk as graphml
    ox.save_graphml(response_content, '{0}/osm_graph.graphml'.format(output_folder))

def osm_visualize(response_content):
    # Visualize
    fig, ax = ox.plot_graph(response_content, node_size=10, edge_color="green", edge_linewidth=1, figsize=(12, 12))
    print("Plot succeeded")

def osm_gpkg_save(response_content,output_folder):
    # Convert graph to GeoDataFrames and save as standard GIS layers
    nodes, edges = ox.graph_to_gdfs(response_content)
    nodes.to_file("{0}/nodes.gpkg".format(output_folder), driver="GPKG")  # GeoPackage
    edges.to_file("{0}/edges.gpkg".format(output_folder), driver="GPKG")

def osm_graph_downloader(bbox_osm):
    response_content = osm_request(bbox_osm)
    output_folder = get_data_folder("raw")
    osm_save(response_content, output_folder)
    osm_visualize(response_content)
    osm_gpkg_save(response_content,output_folder)


if __name__ == "__main__":
    user_input = user_input()
    bbox_osm = bounding_box_osm(user_input)
    osm_graph_downloader(bbox_osm)
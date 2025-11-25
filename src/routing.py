from download_naip import user_input
import os
import osmnx as ox
import matplotlib.pyplot as plt


user = os.path.expanduser('~')
os.chdir(user + '/urban-green-routing/data/raw/')
output_folder = os.getcwd()
print("CURRENT USER FOLDER: ", user)
print("OUTPUT FOLDER: ", output_folder)

ymin, xmin, ymax, xmax, resolution = user_input()

def osm_graph_downloader(xmin, ymin, xmax, ymax):

    # Bbox as tuple
    bbox = (ymax, ymin, xmax, xmin)
    print("bbox: ", bbox)

    G = ox.graph_from_bbox(bbox, network_type="walk", simplify=False)
    print("Graph retrieved: ", G)
    print("Number of nodes:", len(G.nodes))
    print("Number of edges:", len(G.edges))
    
    # Save graph to disk as graphml
    ox.save_graphml(G, '{0}/osm_graph.graphml'.format(output_folder))
    # Visualize
    fig, ax = ox.plot_graph(G, node_size=10, edge_color="green", edge_linewidth=1, figsize=(12, 12))
    print("Plot succeeded")
    
    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)
    
    # Save as standard GIS layers
    nodes.to_file("{0}/nodes.gpkg".format(output_folder), driver="GPKG")  # GeoPackage
    edges.to_file("{0}/edges.gpkg".format(output_folder), driver="GPKG")


osm_graph_downloader(xmin, ymin, xmax, ymax)
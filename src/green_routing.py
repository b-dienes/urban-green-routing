import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
from shapely.ops import linemerge
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


def create_graph(user_input: UserInput, raw_folder):
    aoi_name = user_input.aoi_name
    nodes_path = raw_folder / f"{aoi_name}_nodes.gpkg"
    edges_path = raw_folder / f"{aoi_name}_edges_greendex.gpkg"

    nodes = gpd.read_file(nodes_path)
    edges = gpd.read_file(edges_path)

    # Loop through nodes and edges row by row and add values to graph
    G = nx.DiGraph()
    for idx, row in nodes.iterrows():
        G.add_node(row['osmid'], x=row.geometry.x, y=row.geometry.y)
    for idx, row in edges.iterrows():
        G.add_edge(
            row['u'],
            row['v'],
            weight=row['weight'],
            length=row['length']
        )
    return G, edges

def create_route(user_input: UserInput, graph):
    routing_source = user_input.routing_source
    routing_target = user_input.routing_target
    routing_weight = user_input.routing_weight.value

    path = nx.shortest_path(graph, source=routing_source, target=routing_target, weight=routing_weight)
    return path

def create_edgepairs(path):
    # Build list of ordered edge pairs
    edge_pairs = list(zip(path[:-1], path[1:]))
    return edge_pairs

def retrieve_edges(edge_pairs, edges):
    # Retrieve edges in order
    ordered_edges = []
    for u, v in edge_pairs:
        match = edges[(edges["u"] == u) & (edges["v"] == v)]
        ordered_edges.append(match.iloc[0])
    return ordered_edges

def convert_edges(ordered_edges, edges):
    # Convert edges to GeoDataFrame
    route_edges_gdf = gpd.GeoDataFrame(ordered_edges, crs=edges.crs)
    return route_edges_gdf

def merge_edges(route_edges_gdf):
    # Merge geometries in the correct order
    route_line = linemerge(route_edges_gdf.geometry.tolist())
    return route_line

def save_route(user_input: UserInput, route_line, route_edges_gdf, edges, raw_folder):
    # Create and save route GeoDataFrame
    aoi_name = user_input.aoi_name
    routing_weight = user_input.routing_weight.value
    output_route_path = raw_folder / f"{aoi_name}_route_{routing_weight}.gpkg"

    route_gdf = gpd.GeoDataFrame(
        {
            "weight": [route_edges_gdf["weight"].sum()],
            "length": [route_edges_gdf["length"].sum()],
        },
        geometry=[route_line],
        crs=edges.crs
    )
    route_gdf.to_file(output_route_path, driver="GPKG")

def run_routing(user_input):
    raw_folder = get_data_folder("raw")
    graph, edges = create_graph(user_input, raw_folder)
    path = create_route(user_input, graph)
    edge_pairs = create_edgepairs(path)
    ordered_edges = retrieve_edges(edge_pairs, edges)
    route_edges_gdf = convert_edges(ordered_edges, edges)
    route_line = merge_edges(route_edges_gdf)
    save_route(user_input, route_line, route_edges_gdf, edges, raw_folder)

if __name__ == "__main__":
    user_input = user_input()
    run_routing(user_input)
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
from shapely.ops import linemerge
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


def green_routing(user_input: UserInput):
    aoi_name = user_input.aoi_name
    raw_folder = get_data_folder("raw")

    nodes_path = raw_folder / f"{aoi_name}_nodes.gpkg"
    edges_path = raw_folder / f"{aoi_name}_edges_greendex.gpkg"
    output_route_path = raw_folder / f"{aoi_name}_route.gpkg"

    nodes = gpd.read_file(nodes_path)
    edges = gpd.read_file(edges_path)

    G = nx.DiGraph()

    # Loop through nodes and edges row by row and add values to graph
    for idx, row in nodes.iterrows():
        G.add_node(row['osmid'], x=row.geometry.x, y=row.geometry.y)

    for idx, row in edges.iterrows():
        G.add_edge(
            row['u'],
            row['v'],
            weight=row['weight'],
            length=row['length'],
            greendex=row['greendex']
        )

    source = nodes['osmid'].iloc[0]
    target = nodes['osmid'].iloc[-1]
    print("Source: ", source)
    print("Target: ", target)

    path = nx.shortest_path(G, source=source, target=target, weight='weight')
    print("Shortest path (greenness + length):", path)

    # Build list of ordered edge pairs
    edge_pairs = list(zip(path[:-1], path[1:]))

    # Retrieve edges IN ORDER
    ordered_edges = []
    for u, v in edge_pairs:
        match = edges[(edges["u"] == u) & (edges["v"] == v)]

        if len(match) == 0:
            raise ValueError(f"Edge ({u}, {v}) not found in edges GeoDataFrame")

        ordered_edges.append(match.iloc[0])

    # Convert to GeoDataFrame
    route_edges = gpd.GeoDataFrame(ordered_edges, crs=edges.crs)

    # Merge geometries in the correct order
    route_line = linemerge(route_edges.geometry.tolist())

    # Create route GeoDataFrame
    route_gdf = gpd.GeoDataFrame(
        {
            "weight": [route_edges["weight"].sum()],
            "length": [route_edges["length"].sum()],
            "greendex": [route_edges["greendex"].mean()],
        },
        geometry=[route_line],
        crs=edges.crs
    )

    # Save to file
    route_gdf.to_file(output_route_path, driver="GPKG")

if __name__ == "__main__":
    user_input = user_input()
    green_routing(user_input)
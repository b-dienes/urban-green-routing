import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
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

    G = nx.DiGraph()  # Use nx.Graph() if you want it undirected

    for idx, row in nodes.iterrows():
        G.add_node(row['osmid'], x=row.geometry.x, y=row.geometry.y)

    for idx, row in edges.iterrows():
        G.add_edge(
            row['u'],
            row['v'],
            weight=row['weight'],       # routing cost
            length=row['length'],     # original segment length
            greendex=row['greendex']  # tree coverage index
        )

    source = nodes['osmid'].iloc[0]
    target = nodes['osmid'].iloc[-1]

    path = nx.shortest_path(G, source=source, target=target, weight='weight')
    print("Shortest path (greenness + length):", path)

    
    # Get edges along the path safely
    edge_pairs = list(zip(path[:-1], path[1:]))  # exact consecutive pairs

    # Match GeoDataFrame to these pairs to get geometry
    route_edges = edges[edges.apply(lambda row: (row['u'], row['v']) in edge_pairs, axis=1)]

    # Merge geometries into one LineString
    route_line = LineString([pt for geom in route_edges.geometry for pt in geom.coords])

    # Create route GeoDataFrame
    route_gdf = gpd.GeoDataFrame(
        {'weight': [route_edges['weight'].sum()],
         'length': [route_edges['length'].sum()],
         'greendex': [route_edges['greendex'].mean()]},
        geometry=[route_line],
        crs=edges.crs
    )

    # Save to GeoPackage
    route_gdf.to_file(output_route_path, driver="GPKG")


if __name__ == "__main__":
    user_input = user_input()
    green_routing(user_input)
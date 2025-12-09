import geopandas as gpd
import networkx as nx
from shapely.ops import linemerge
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


class GreenRouting:
    """Encapsulates the routing workflow for an AOI using graph data built from nodes and edges."""

    def __init__(self, user_input, raw_folder, processed_folder):
        """
        Initialize the routing object with user input and folder paths.
        
        Args:
            user_input (UserInput): Object containing AOI name, routing source/target, and routing weight
            raw_folder (Path): Folder where raw node and edge files are stored
            processed_folder (Path): Folder where processed outputs will be saved
        """
        self.user_input = user_input
        self.raw_folder = raw_folder
        self.processed_folder = processed_folder

    def create_graph(self):
        """
        Build a directed graph from node and edge files in raw_folder.
        
        Side effects:
            Sets self.graph (nx.DiGraph) and self.edges (GeoDataFrame)
        """
        nodes_path = self.raw_folder / f"{self.user_input.aoi_name}_nodes.gpkg"
        edges_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_greendex.gpkg"

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

        self.graph = G
        self.edges = edges

    def create_route(self):
        """
        Compute the shortest path (nodes only) from routing source to target using the routing weight.
        
        Side effects:
            Sets self.path (list of node IDs)
        """
        routing_source = self.user_input.routing_source
        routing_target = self.user_input.routing_target

        routing_weight = self.user_input.routing_weight.value

        path = nx.shortest_path(self.graph, source=routing_source, target=routing_target, weight=routing_weight)
        self.path = path

    def create_edgepairs(self):
        """
        Build a list of ordered edge pairs from the nodes from self.path.
        
        Side effects:
            Sets self.edge_pairs (list of tuples)
        """
        edge_pairs = list(zip(self.path[:-1], self.path[1:]))
        self.edge_pairs = edge_pairs

    def retrieve_edges(self):
        """
        Retrieve the edges in order along the path from self.edge_pairs.
        
        Side effects:
            Sets self.ordered_edges (list of edge rows)
        """
        ordered_edges = []
        for u, v in self.edge_pairs:
            match = self.edges[(self.edges["u"] == u) & (self.edges["v"] == v)]
            ordered_edges.append(match.iloc[0])
        self.ordered_edges = ordered_edges

    def convert_edges(self):
        """
        Convert the ordered edges to a GeoDataFrame.
        
        Side effects:
            Sets self.route_edges_gdf (GeoDataFrame)
        """
        route_edges_gdf = gpd.GeoDataFrame(self.ordered_edges, crs=self.edges.crs)
        self.route_edges_gdf = route_edges_gdf

    def merge_edges(self):
        """
        Merge the geometries of the route edges into a single LineString.
        
        Side effects:
            Sets self.route_line (LineString)
        """
        route_line = linemerge(self.route_edges_gdf.geometry.tolist())
        self.route_line = route_line

    def save_route(self):
        """
        Save the route as a GeoPackage file in raw_folder.
        
        Side effects:
            Writes a GeoPackage file at self.raw_folder
        """
        aoi_name = self.user_input.aoi_name
        routing_weight = self.user_input.routing_weight.value
        output_route_path = self.raw_folder / f"{aoi_name}_route_{routing_weight}.gpkg"

        route_gdf = gpd.GeoDataFrame(
            {
                "weight": [self.route_edges_gdf["weight"].sum()],
                "length": [self.route_edges_gdf["length"].sum()],
            },
            geometry=[self.route_line],
            crs=self.edges.crs
        )
        route_gdf.to_file(output_route_path, driver="GPKG")

    def run_routing(self):
        """
        Run the full routing workflow in sequence.
        
        Calls:
            create_graph -> create_route -> create_edgepairs -> retrieve_edges -> convert_edges -> merge_edges -> save_route
        """
        self.create_graph()
        self.create_route()
        self.create_edgepairs()
        self.retrieve_edges()
        self.convert_edges()
        self.merge_edges()
        self.save_route()

if __name__ == "__main__":
    user_input = user_input()
    raw_folder = get_data_folder("raw")
    processed_folder = get_data_folder("processed")
    router = GreenRouting(user_input, raw_folder, processed_folder)
    router.run_routing()
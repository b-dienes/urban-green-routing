import logging
from pathlib import Path
import geopandas as gpd
import networkx as nx
from shapely.ops import linemerge
from utils.paths import get_data_folder
from utils.inputs import user_input, UserInput


logger = logging.getLogger(__name__)

class GreenRouting:
    """Encapsulates the routing workflow for an AOI using graph data built from nodes and edges."""

    def __init__(self, user_input: UserInput, raw_folder: Path, processed_folder: Path) -> None:
        """
        Initialize the routing object with user input and folder paths.
        
        Args:
            user_input (UserInput): Object containing AOI name, routing source/target, and routing weight
            raw_folder (Path): Folder where raw node and edge files are stored
            processed_folder (Path): Folder where processed outputs will be saved
        """
        self.user_input: UserInput = user_input
        self.raw_folder: Path = raw_folder
        self.processed_folder: Path = processed_folder

    def create_graph(self) -> None:
        """
        Build a directed graph from node and edge files in raw_folder.
        
        Side effects:
            Sets self.graph (nx.DiGraph) and self.edges (GeoDataFrame)
        """
        nodes_path = self.raw_folder / f"{self.user_input.aoi_name}_nodes.gpkg"
        edges_path = self.raw_folder / f"{self.user_input.aoi_name}_edges_greendex.gpkg"

        nodes = gpd.read_file(nodes_path)
        edges = gpd.read_file(edges_path)

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
        logger.info("Graph built from %s_nodes.gpkg and %s_edges_greendex.gpkg", self.user_input.aoi_name)

    def create_route(self) -> None:
        """
            Compute the shortest path as a list of nodes from routing source to target 
            using the routing weight.

            Note:
                This path includes nodes only; corresponding edges are filtered and 
                processed later in subsequent methods.

            Side effects:
                Sets self.path (list of node IDs)
        """
        path = nx.shortest_path(
            self.graph,
            source=self.user_input.routing_source,
            target=self.user_input.routing_target,
            weight=self.user_input.routing_weight.value)
        self.path = path
        logger.info("Route nodes selected based on field: %s", self.user_input.routing_weight.value)

    def create_edgepairs(self) -> None:
        """
        Build a list of ordered edge pairs from the nodes from self.path.
        
        Side effects:
            Sets self.edge_pairs (list of tuples)
        """
        edge_pairs = list(zip(self.path[:-1], self.path[1:]))
        self.edge_pairs = edge_pairs
        logger.info("Edgepairs created")

    def retrieve_edges(self) -> None:
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
        logger.info("Edges along path selected")

    def convert_edges(self) -> None:
        """
        Convert the ordered edges to a GeoDataFrame.
        
        Side effects:
            Sets self.route_edges_gdf (GeoDataFrame)
        """
        route_edges_gdf = gpd.GeoDataFrame(self.ordered_edges, crs=self.edges.crs)
        self.route_edges_gdf = route_edges_gdf
        logger.info("Edges converted to GeoDataFrame")

    def merge_edges(self) -> None:
        """
        Merge the geometries of the route edges into a single LineString.
        
        Side effects:
            Sets self.route_line (LineString)
        """
        route_line = linemerge(self.route_edges_gdf.geometry.tolist())
        self.route_line = route_line
        logger.info("Single linestring created")

    def save_route(self) -> None:
        """
        Save the route as a GeoPackage file in raw_folder.
        
        Side effects:
            Writes a GeoPackage file at self.raw_folder
        """
        output_route_path = self.processed_folder / f"{self.user_input.aoi_name}_route_{self.user_input.routing_weight.value}.gpkg"

        route_gdf = gpd.GeoDataFrame(
            {
                "weight": [self.route_edges_gdf["weight"].sum()],
                "length": [self.route_edges_gdf["length"].sum()],
            },
            geometry=[self.route_line],
            crs=self.edges.crs
        )
        route_gdf.to_file(output_route_path, driver="GPKG")
        logger.info("Route saved as %s: ", output_route_path)

    def run_routing(self) -> None:
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
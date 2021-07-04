import pathlib
import networkx
import json

DATA_FILE_PATH = pathlib.Path('assets/navigation.json')


class Navigator:
    def __init__(self, file_name: str = DATA_FILE_PATH):
        with open(file_name, 'r') as file:
            data = json.load(file)
        self.nodes, edges, adjacency_matrix = data['nodes'], data['edges'], data['adjacency_matrix']
        self.graph = networkx.Graph()
        for n1, n2 in edges:
            self.graph.add_edge(n1, n2, weight=adjacency_matrix[n1][n2])

    def navigate(self, from_node: int, to_node: int, avoid_nodes=None):
        if avoid_nodes is None:
            networkx.shortest_path(self.graph, from_node, to_node, weight='weight')
        elif (from_node in avoid_nodes) or (to_node in avoid_nodes):
            return None
        graph = self.graph.copy()
        for node in avoid_nodes:
            graph.remove_node(node)
        try:
            return networkx.shortest_path(graph, from_node, to_node, weight='weight')
        except networkx.exception.NetworkXNoPath:
            return None

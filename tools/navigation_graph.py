import json
import pathlib
import pygame
from geometry import Vector
from shared import ASSETS, UI, from_draw_coords, to_draw_coords


class NAVIGATION_GRAPH:
    screen_dims = (808, 448)
    window_title = 'Navigation Graph Generator'
    delay = 20

    node_width = 6
    indicator_width = 2
    edge_width = 2
    hover_threshold_distance = 26
    node_label_offset = (8, 4)

    class color:
        node = (0, 230, 0)
        node_path = (255, 0, 221)
        node_avoid = (0, 80, 255)
        hover_indicator = (187, 10, 196)
        edge = (30, 30, 30)
        edge_path = (153, 0, 133)
        label = (0, 0, 0)


class NodePair:
    _list: list['NodePair'] = []

    @classmethod
    def __iter__(cls):
        return NodePair._list.__iter__()

    @classmethod
    def __getitem__(cls, item):
        return NodePair._list.__getitem__(item)

    def __init__(self, coords: tuple[int, int]):
        center = from_draw_coords(coords)
        mirrored_center = center.mirror()
        center, mirrored_center = (center, mirrored_center) if (center.x < mirrored_center.x) else (mirrored_center, center)
        self._center, self._mirrored_center = center, mirrored_center
        NodePair._list.append(self)

    @classmethod
    def from_tuple(cls, coords: tuple[int, int]):
        return cls(coords)

    def to_tuple(self):
        return to_draw_coords(self._center)


class EdgePair:
    def __init__(self, index1: int, index2: int, parity: bool):
        index1, index2 = (index1, index2) if (index1 < index2) else (index2, index1)
        self.index1, self.index2 = index1, index2
        self.parity = parity

    @classmethod
    def from_tuple(cls, values: tuple[int, int, bool]):
        return cls(*values)

    def contains(self, index: int):
        return (self.index1 == index) or (self.index2 == index)

    def to_tuple(self):
        return self.index1, self.index2, self.parity


class NavigationGraph:
    def __init__(self, data_file: pathlib.Path = None):
        self.nodes = NodePair
        self.edges: set[EdgePair] = set()

        if data_file is not None:
            self.load(data_file)

        self.screen = pygame.display.set_mode(NAVIGATION_GRAPH.screen_dims)
        pygame.display.set_caption(NAVIGATION_GRAPH.window_title)
        pygame.display.set_icon(ASSETS.logo)
        pygame.font.init()
        self.font = pygame.font.SysFont(*UI.font)
        self.render()

    def modify(self):
        left_click_index = right_click_index = None

        while True:
            event = pygame.event.wait()
            mouse_position = pygame.mouse.get_pos()
            hover_index = self.index_closest(from_draw_coords(mouse_position))

            if (event.type == pygame.MOUSEBUTTONDOWN) and (event.button == 1):
                left_click_index = hover_index
            elif (event.type == pygame.MOUSEBUTTONUP) and (event.button == 1):
                if (left_click_index is None) and (hover_index is None):
                    self.add_node(mouse_position)
                elif (left_click_index is not None) and (hover_index is not None) and (not self.equal(hover_index, left_click_index)):
                    self.add_edge(left_click_index, hover_index)
                    left_click_index = None
                elif (left_click_index is not None) and ((hover_index is None) or (hover_index == left_click_index)):
                    new_point = from_draw_coords(mouse_position)
                    self.nodes[left_click_index] = new_point
                    self.nodes[self.mirror_index(left_click_index)] = new_point.mirror()
            elif (event.type == pygame.MOUSEBUTTONDOWN) and (event.button == 3):
                right_click_index = hover_index
            elif (event.type == pygame.MOUSEBUTTONUP) and (event.button == 3):
                if (hover_index is not None) and (right_click_index is not None) and (hover_index == right_click_index):
                    self.remove_node(right_click_index)
                    hover_index, left_click_index, right_click_index = None, None, None
                elif (hover_index is not None) and (right_click_index is not None):
                    self.remove_edge(right_click_index, hover_index)
                    left_click_index = right_click_index = None
            elif (event.type == pygame.KEYDOWN) and (event.key == pygame.K_ESCAPE):
                return
            elif (event.type == pygame.KEYDOWN) and (event.key == pygame.K_s):
                self.save()
                return

            self.render(hover_index)

    def render(self, hover_index=None):
        self.screen.blit(ASSETS.field, (0, 0))
        self.blit_edges()
        self.blit_nodes()
        if hover_index is not None:
            self.blit_selector(hover_index)
        pygame.display.flip()

    def add_node(self, coords: tuple[int, int]):
        self.nodes.append(NodePair(coords))

    def remove_node(self, index: int):
        index = min(index, self.mirror_index(index))
        del self.nodes[index: index + 2]

        edges = set()
        for edge in self.edges:
            if index not in edge and (index + 1) not in edge:
                index1, index2 = edge
                if index1 >= index + 2:
                    index1 -= 2
                if index2 >= index + 2:
                    index2 -= 2
                edges.add((index1, index2))
        self.edges = edges
        self.count_nodes -= 2

    def add_edge(self, index1: int, index2: int):
        if ((index1, index2) in self.edges) or ((index2, index1) in self.edges):
            return
        self.edges.add((index1, index2))
        self.edges.add((self.mirror_index(index1), self.mirror_index(index2)))

    def remove_edge(self, index1: int, index2: int):
        if ((index1, index2) not in self.edges) and ((index2, index1) not in self.edges):
            return
        self.edges.remove((index1, index2))
        self.edges.remove((index2, index1))
        self.edges.remove((self.mirror_index(index1), self.mirror_index(index2)))
        self.edges.remove((self.mirror_index(index2), self.mirror_index(index1)))

    def blit_nodes(self):
        for index in range(self.count_nodes):
            self.blit_node(index)

    def blit_node(self, index: int, color=NAVIGATION_GRAPH.color.node):
        text = self.font.render(str(index), True, NAVIGATION_GRAPH.color.label)
        text_position = to_draw_coords(self.nodes[index], offset=NAVIGATION_GRAPH.node_label_offset)
        square = pygame.Rect(0, 0, NAVIGATION_GRAPH.node_width, NAVIGATION_GRAPH.node_width)
        square.center = to_draw_coords(self.nodes[index])
        pygame.draw.rect(self.screen, color, square)
        self.screen.blit(text, text_position)

    def blit_edges(self):
        for edge in self.edges:
            self.blit_edge(*edge)

    def blit_edge(self, index1, index2, color=NAVIGATION_GRAPH.color.edge):
        pygame.draw.line(self.screen, color, to_draw_coords(self.nodes[index1]), to_draw_coords(self.nodes[index2]), NAVIGATION_GRAPH.edge_width)

    def blit_selector(self, index: int):
        for index_ in (index, self.mirror_index(index)):
            pygame.draw.circle(self.screen, NAVIGATION_GRAPH.color.hover_indicator, to_draw_coords(self.nodes[index_]),
                               NAVIGATION_GRAPH.node_width - NAVIGATION_GRAPH.indicator_width, width=NAVIGATION_GRAPH.indicator_width)

    def render_path(self, path: list[int], avoid_nodes: list[int] = None):
        avoid_nodes = [] if avoid_nodes is None else avoid_nodes
        for index in range(len(path) - 1):
            self.blit_edge(index, index + 1, color=NAVIGATION_GRAPH.color.edge_path)
        for index in path:
            self.blit_node(index, color=NAVIGATION_GRAPH.color.node_path)
        for index in avoid_nodes:
            self.blit_node(index, color=NAVIGATION_GRAPH.color.node_avoid)
        pygame.display.flip()

    def index_closest(self, point: Vector) -> int:
        min_distance = NAVIGATION_GRAPH.hover_threshold_distance + 1
        min_index = None
        for index, center in enumerate(self.nodes):
            distance = point.distance_to(center)
            if distance < min_distance:
                min_distance = distance
                min_index = index
        return min_index

    def adjacency_matrix(self):
        matrix = [[0] * self.count_nodes] * self.count_nodes
        for index1, index2 in self.edges:
            matrix[index1][index2] = matrix[index2][index1] = self.nodes[index1].distance_to(self.nodes[index2])
        return matrix

    def save(self):
        data = {'nodes': [(n.x, n.y) for n in self.nodes], 'edges': list(self.edges), 'adjacency_matrix': self.adjacency_matrix()}
        with open(ASSETS.navigation_file, 'w+') as file:
            json.dump(data, file, indent=2)
        print(f'Saved {self.count_nodes} nodes and {len(self.edges)} edges to "{ASSETS.navigation_file.name}".')

    def load(self, data_file: pathlib.Path):
        with open(data_file, 'r') as file:
            data = json.load(file)

        for node in data['nodes']:
            self.nodes.append(Vector(*node))
            self.count_nodes += 1
        for edge in data['edges']:
            self.edges.add(tuple(edge))
        print(f'Loaded {self.count_nodes} nodes and {len(self.edges)} edges from "{data_file.name}".')

    @staticmethod
    def mirror_index(index):
        return index - 2 * (index % 2) + 1

    @staticmethod
    def equal(index1, index2):
        return index1 // 2 == index2 // 2


def main():
    graph = NavigationGraph(ASSETS.navigation_file)
    graph.modify()


if __name__ == '__main__':
    main()

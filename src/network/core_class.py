from src.domain.point import Point

from dataclasses import dataclass

@dataclass(slots=True)
class Node:
    id: str
    coord: Point

@dataclass(slots=True)
class Link:
    id: str
    from_node: str
    to_node: str
    length: float


def get_boundary_nodes_of_network(nodes_dict: dict[str,Node]) -> (Point, Point):
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for node in nodes_dict.values():
        min_x = min(min_x, node.coord.x)
        min_y = min(min_y, node.coord.y)
        max_x = max(max_x, node.coord.x)
        max_y = max(max_y, node.coord.y)

    return Point(min_x, min_y), Point(max_x, max_y)
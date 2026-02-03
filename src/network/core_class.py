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
    length: str
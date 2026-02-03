from src.domain.point import Point

from dataclasses import dataclass, field
from typing import Dict

@dataclass(slots=True)
class Person:
    id: str
    coords_act_dict: Dict[str, Point] = field(default_factory=dict)
    is_coord_valid: bool = True

    def add_act_coord(self, act: str, point: Point):
        if act not in self.coords_act_dict:
            self.coords_act_dict[act] = point
        else:
            current_p = self.coords_act_dict[act]
            if point.x != current_p.x or point.y != current_p.y:
                self.is_coord_valid = False
                current_p.x = point.x
                current_p.y = point.y

def get_boundary_nodes_of_plans(person_dict: dict[str,Person]) -> (Point, Point):
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for person in person_dict.values():
        for act in person.coords_act_dict.values():
            min_x = min(min_x, act.x)
            min_y = min(min_y, act.y)
            max_x = max(max_x, act.x)
            max_y = max(max_y, act.y)

    return Point(min_x, min_y), Point(max_x, max_y)

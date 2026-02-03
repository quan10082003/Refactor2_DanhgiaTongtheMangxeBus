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

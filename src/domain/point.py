from dataclasses import dataclass
from shapely.geometry import Point as ShapelyPoint

@dataclass(slots=True)
class Point:
    x: float
    y: float

    @property
    def to_shapely(self) -> ShapelyPoint:
        return ShapelyPoint(self.x, self.y)
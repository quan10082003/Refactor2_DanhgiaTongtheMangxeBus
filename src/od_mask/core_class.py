from src.domain.point import Point

from dataclasses import dataclass
from abc import ABC, abstractmethod
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import Point as ShapelyPoint


@dataclass
class Zone:
    id: int
    boundary_points: list[Point]

    def contains(self, point: Point) -> bool:
        # 1. Tạo Polygon từ danh sách Point của bạn
        # Shapely cần một list các tuple (x, y) hoặc list các ShapelyPoint
        polygon = ShapelyPolygon([(p.x, p.y) for p in self.boundary_points])
        
        # 2. Kiểm tra
        # .contains: Trả về True nếu nằm hẳn bên trong
        # .touches: Trả về True nếu nằm trên biên
        return polygon.contains(point.to_shapely) or polygon.touches(point.to_shapely)



class ZoneGenerator(ABC):
    @abstractmethod
    def generate(self) -> list[Zone]:
        pass


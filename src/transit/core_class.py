from src.domain.point import Point

from dataclasses import dataclass

@dataclass(slots=True)
class StopFacility:
    id: str
    coord: Point
    ref_linkid: str

@dataclass(slots=True)
class TransitRoute:
    id: str
    line: str
    links_id: list[str]
    stops_id: list[str]
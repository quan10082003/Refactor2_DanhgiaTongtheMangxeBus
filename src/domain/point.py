from dataclasses import dataclass

@dataclass(slots=True)
class Point:
    x: str
    y: str
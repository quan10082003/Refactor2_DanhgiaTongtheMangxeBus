from src.domain.point import Point
from src.od_mask.core_class import ZoneGenerator, Zone

class ZoneGeneratorByGrid(ZoneGenerator):
    def __init__(self, max_p: Point, min_p: Point, rows:  int, cols: int):
        self._max_p = max_p
        self._min_p= min_p
        self.rows = rows
        self.cols = cols

    def _calculate_unit_size(self):
        # Tách việc tính toán ra hàm riêng để code clear hơn
        width = (self._max_p.x - self._min_p.x) / self.cols
        height = (self._max_p.y - self._min_p.y) / self.rows
        return width, height

    def generate(self) -> list[Zone]:
        zones_list = []
        unit_width, unit_height = self._calculate_unit_size()
        
        for r in range(self.rows):
            for c in range(self.cols):
                # Tính toán tọa độ các góc
                x_left = self._min_p.x + c * unit_width
                x_right = x_left + unit_width
                y_bottom = self._min_p.y + r * unit_height
                y_top = y_bottom + unit_height
                
                points = [
                    Point(x_left, y_bottom),
                    Point(x_right, y_bottom),
                    Point(x_right, y_top),
                    Point(x_left, y_top)
                ]
                
                
                zone_id = f"z_{r}_{c}" # ID có ý nghĩa hơn
                zones_list.append(Zone(id=zone_id, boundary_points=points))
        
        return zones_list
    
    def find_zone_id(self, point: Point) -> str:
        """
        Tìm Zone ID chứa điểm point (O(1)).
        Trả về "undefined" nếu point nằm ngoài vùng grid.
        """
        # Kiểm tra boundary box
        if not (self._min_p.x <= point.x <= self._max_p.x and 
                self._min_p.y <= point.y <= self._max_p.y):
            return "undefined"

        unit_width, unit_height = self._calculate_unit_size()
        
        # Tránh chia cho 0
        if unit_width == 0 or unit_height == 0:
            return "undefined"

        # Tính chỉ số dòng, cột
        c = int((point.x - self._min_p.x) / unit_width)
        r = int((point.y - self._min_p.y) / unit_height)

        # Xử lý biên (khi point nằm đúng trên biên phải/trên cùng của max_p)
        if c == self.cols:
            c = self.cols - 1
        if r == self.rows:
            r = self.rows - 1
            
        return f"z_{r}_{c}"
                
if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.network.network import  generate_nodes_and_links_dict
    from src.network.core_class import get_boundary_nodes_of_network

    path = load_config(r"config/config_path.yaml")
    network = path.paths.network
    nodes_dict, links_dict = generate_nodes_and_links_dict(network)
    max_p, _min_p = get_boundary_nodes_of_network(nodes_dict)
    
    zone_generator = ZoneGeneratorByGrid(max_p, _min_p, 10,10)
    zones = zone_generator.generate()
    print(zones[0])
    print(len(zones))

    #python -m src.od_mask.generator
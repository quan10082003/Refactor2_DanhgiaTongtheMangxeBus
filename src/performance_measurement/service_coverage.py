from src.domain.point import Point
from src.transit.core_class import TransitRoute, StopFacility
from src.transit.transit_schedule import generate_bus_routes_and_stops_dict
from src.plan.core_class import Person
from src.plan.plan import generate_people_acts_coord_dict

import numpy as np
from scipy.spatial import KDTree # Thư viện "thần thánh" cho bài toán này

def calculte_service_coverage(people_dict: dict[str,Person], bus_stops_dict: dict[str,StopFacility], act_coveraged: str, radia_m: float):
    stop_coords = np.array([[s.coord.x, s.coord.y] for s in bus_stops_dict.values()])
    
    # 2. Xây dựng cây KD-Tree từ các trạm dừng
    # Việc này chỉ tốn công một lần duy nhất
    tree = KDTree(stop_coords)
    
    service_coverage = 0
    
    for person in people_dict.values():
        if act_coveraged not in person.coords_act_dict:
            continue

        act_p = person.coords_act_dict[act_coveraged]
        query_point = [act_p.x, act_p.y]
        
        # 4. Sử dụng hàm query_ball_point để tìm tất cả các trạm trong bán kính radia_m
        # Hàm này cực nhanh vì nó loại bỏ các vùng không gian không liên quan
        indices = tree.query_ball_point(query_point, radia_m)
        
        # Nếu danh sách index trả về không rỗng nghĩa là người này được phục vụ
        if len(indices) > 0:
            service_coverage += 1

    return service_coverage

if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    schedule = path.paths.transit_schedule
    plan = path.paths.plan

    _, bus_stops_dict = generate_bus_routes_and_stops_dict(transit_schedule_path=schedule, bus_route_hint_str="bus")
    people_dict = generate_people_acts_coord_dict(plan_path=plan)
    people_number = len(people_dict)



    # Thầy sửa radian_m thành radia_m cho khớp tham số hàm của trò
    radia_m = 400.0
    service_coverage = calculte_service_coverage(
        people_dict=people_dict, 
        bus_stops_dict=bus_stops_dict, 
        radia_m=radia_m, 
        act_coveraged="home"
    )
    
    print("-" * 50)
    print(f"Service coverage Bus Stops ({radia_m}m): {service_coverage} / {people_number}")
    print(f"Percent: {service_coverage/people_number*100:.2f}%")
    print("-" * 50)

    # Cleanup bộ nhớ
    del bus_stops_dict
    del people_dict
    # python -m src.performance_measurement.service_coverage






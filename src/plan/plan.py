from src.transit.transit_vehicle import get_transit_type_dict
from src.domain.logic import is_public_transport_bus
from src.domain.point import Point
from src.plan.core_class import Person

import lxml.etree as etree

def generate_people_acts_coord_dict(plan_path: str) -> dict[str, Person]:
    people_dict: dict[str, Person] = {}
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(plan_path, parser)
    root = tree.getroot()

    for person_elem in root.xpath("//person"):
        person_id = person_elem.get("id")
        selected_plan = person_elem.xpath("./plan[@selected='yes']")[0]
        person_obj = Person(id=person_id)
        for act in selected_plan.xpath("./act"):
            act_type = act.get("type")
            x = float(act.get("x"))
            y = float(act.get("y"))
            person_obj.add_act_coord(act=act_type, point=Point(x, y)) 
        people_dict[person_id] = person_obj
    
    return people_dict

if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    plan_path = path.paths.plan
    try:
        people = generate_people_acts_coord_dict(plan_path)

        # --- PHẦN PRINT TEST ---
        print("-" * 50)
        print(f"[*] THỐNG KÊ DÂN SỐ:")
        print(f"    - Tổng số người (Agents): {len(people)}")
        
        # Đếm số người có tọa độ không nhất quán
        invalid_agents = [p for p in people.values() if not p.is_coord_valid]
        print(f"    - Số người có tọa độ hoạt động bị lệch: {len(invalid_agents)}")
        print("-" * 50)

        # Kiểm tra mẫu một người ngẫu nhiên
        if people:
            sample_id = next(iter(people))
            p = people[sample_id]
            print(f"[*] TEST AGENT (Mẫu: {sample_id}):")
            print(f"    - Các hoạt động ghi nhận: {list(p.coords_act_dict.keys())}")
            
            for act_name, coord in p.coords_act_dict.items():
                print(f"    - [{act_name}]: ({coord.x}, {coord.y})")
            
            status = "✅ Hợp lệ" if p.is_coord_valid else "❌ Cảnh báo: Tọa độ không đồng nhất!"
            print(f"    - Trạng thái dữ liệu: {status}")

    except Exception as e:
        print(f"[LỖI] Không thể xử lý file plans: {e}")

    # python -m src.plan.plan
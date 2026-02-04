import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
from lxml import etree
import pandas as pd

from src.domain.point import Point
from src.od_mask.core_class import Zone



def generate_personTrip_df(
    events_path: str, vehtype_dict: dict, zone_finder, bus_hint_str: str, output_arrow_path: str, 
    prefix_pt_driver="pt", batch_size=50000,
    schema_names: list = ['vehIdList','vehicleTypeList','mainMode','travelTime','startTime','actstart','actend','OZone','DZone','xO','yO','xD','yD']):

    # 1. Định nghĩa schema cho Arrow (Đảm bảo khớp với các key trong dict)
    arrow_schema = pa.schema([(name, pa.string()) for name in schema_names])
    
    temp_data = [] # Lưu list các dict
    person_trip_map = {}
    context = etree.iterparse(events_path, events=('end',))

    with pa.OSFile(output_arrow_path, 'wb') as sink:
        with ipc.new_stream(sink, arrow_schema) as writer:
            for event, elem in context:
                if elem.tag == "event":
                    e_type = elem.get("type")

                    # --- Logic thu thập dữ liệu (Giữ nguyên logic của bạn) ---
                    if e_type == "actend":
                        personId = elem.get("person")
                        if personId in person_trip_map or personId.startswith("pt_") or elem.get("actType") == "pt interaction":
                            elem.clear()
                            continue
                        
                        x, y = float(elem.get("x")), float(elem.get("y"))
                        person_location = Point(x, y)
                        in_zone_id = zone_finder.find_zone_id(person_location)
                        
                        person_trip_map[personId] = {
                            "actstart": elem.get("actType"),
                            "OZone": in_zone_id,
                            "xO": x,
                            "yO": y,
                            "vehIdList": [],
                            "vehicleTypeList": []
                        }

                    elif e_type == "departure":
                        personId = elem.get("person")
                        if personId in person_trip_map and "startTime" not in person_trip_map[personId]:
                            person_trip_map[personId]["mainMode"] = elem.get("computationalRoutingMode")
                            person_trip_map[personId]["startTime"] = float(elem.get("time"))

                    elif e_type == "PersonEntersVehicle":
                        personId = elem.get("person")
                        if personId in person_trip_map:
                            v_id = elem.get("vehicle")
                            person_trip_map[personId]["vehIdList"].append(v_id)
                            person_trip_map[personId]["vehicleTypeList"].append(vehtype_dict.get(v_id, "undefined"))

                    elif e_type == "actstart":
                        personId = elem.get("person")
                        if personId not in person_trip_map or personId.startswith("pt_") or elem.get("actType") == "pt interaction":
                            elem.clear()
                            continue
                        
                        # Tính toán các giá trị cuối
                        travel_time = float(elem.get("time")) - person_trip_map[personId]["startTime"]
                        xD, yD = float(elem.get("x")), float(elem.get("y"))
                        
                        person_location = Point(xD, yD)
                        d_zone_id = zone_finder.find_zone_id(person_location)

                        # 2. Append vào temp_data dưới dạng DICT
                        temp_data.append({
                            'vehIdList': ";".join(map(str, person_trip_map[personId]['vehIdList'])),
                            'vehicleTypeList': ";".join(map(str, person_trip_map[personId]['vehicleTypeList'])),
                            'mainMode': str(person_trip_map[personId]['mainMode']),
                            'travelTime': str(travel_time),
                            'startTime': str(person_trip_map[personId]['startTime']),
                            'actstart': str(person_trip_map[personId]['actstart']),
                            'actend': str(elem.get("actType")),
                            'OZone': str(person_trip_map[personId]['OZone']),
                            'DZone': str(d_zone_id),
                            'xO': str(person_trip_map[personId]['xO']),
                            'yO': str(person_trip_map[personId]['yO']),
                            'xD': str(xD),
                            'yD': str(yD)
                        })
                        # print("Đang làm việc")

                        # 3. Kiểm tra Batch Size để ghi ra Stream
                        if len(temp_data) >= batch_size:
                            batch_df = pd.DataFrame(temp_data)
                            # Đảm bảo thứ tự cột đúng với schema
                            table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                            print(f"Recorded batch of {len(temp_data)} trips...")
                            writer.write_table(table)
                            temp_data = [] # Giải phóng RAM
                        
                        del person_trip_map[personId]

                elem.clear()

            # 4. Ghi nốt phần dữ liệu còn dư cuối cùng
            if temp_data:
                batch_df = pd.DataFrame(temp_data)
                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                writer.write_table(table)

    print(f"--- Đã hoàn thành Streaming ra file Arrow IPC: {output_arrow_path} ---")

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.network.network import generate_nodes_and_links_dict
    from src.network.core_class import get_boundary_nodes_of_network
    from src.transit.transit_vehicle import get_transit_type_dict
    from src.od_mask.generator import ZoneGeneratorByGrid
    from src.plan.core_class import get_boundary_nodes_of_plans
    from src.plan.plan import generate_people_acts_coord_dict
    
    path = load_config(r"config/config_path.yaml")
    
    network = path.paths.network
    nodes_dict, links_dict = generate_nodes_and_links_dict(network)
    min_p_network, max_p_network = get_boundary_nodes_of_network(nodes_dict)

    plan_path = path.paths.plan
    people = generate_people_acts_coord_dict(plan_path)
    min_p_plan, max_p_plan = get_boundary_nodes_of_plans(people)

    # So sánh bound của plan với của network để tính bound cho zone
    min_p = Point(min(min_p_network.x, min_p_plan.x), min(min_p_network.y, min_p_plan.y))
    max_p = Point(max(max_p_network.x, max_p_plan.x), max(max_p_network.y, max_p_plan.y))

    zone_gen = ZoneGeneratorByGrid(max_p=max_p, min_p=min_p, rows=20, cols=20)
    # zones_list = zone_gen.generate()

    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)
    people_trip = path.data.interim.event.people_trip

    generate_personTrip_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        zone_finder=zone_gen,
        bus_hint_str="bus", 
        output_arrow_path=people_trip)

    #python -m src.events.person_trip

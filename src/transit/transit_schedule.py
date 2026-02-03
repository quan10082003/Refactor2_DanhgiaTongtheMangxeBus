from src.transit.transit_vehicle import get_transit_type_dict
from src.domain.logic import is_public_transport_bus
from src.domain.point import Point
from src.transit.core_class import TransitRoute, StopFacility

import lxml
import lxml.etree as etree

def generate_bus_routes_and_stops_dict(transit_schedule_path: str, bus_route_hint_str: str) -> (dict[str,TransitRoute], dict[str,StopFacility]):
    routes_dict: dict(str,TransitRoute) = {}
    full_stops_dict: dict(str,StopFacility) = {}
    bus_stops_dict: dict(str,StopFacility) = {}

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(transit_schedule_path, parser)
    root = tree.getroot()

    for stop in root.xpath("//transitSchedule/transitStops/stopFacility"):
        stop_id = stop.xpath("@id")[0]
        x = stop.xpath("@x")[0]
        y = stop.xpath("@y")[0]
        ref_linkid = stop.xpath("@linkRefId")[0]
        full_stops_dict[stop_id] = StopFacility(id=stop_id, coord=Point(x,y), ref_linkid=ref_linkid)

    for line in root.xpath("//transitSchedule/transitLine"):    
        line_id = line.xpath("@id")[0]
        for route in line.xpath("./transitRoute"):
            transit_mode = route.xpath("./transportMode/text()")[0]

            if is_public_transport_bus(vehicle_type=transit_mode, bus_hint_str=bus_route_hint_str) :
                route_id = route.xpath("@id")[0]

                stops_id: list = route.xpath("./routeProfile/stop/@refId")
                links_id: list = route.xpath("./route/link/@refId")
                routes_dict[route_id] = TransitRoute(id=route_id, line=line_id, links_id=links_id, stops_id=stops_id)
                for stop_id in stops_id:
                    if stop_id in full_stops_dict:
                        bus_stops_dict[stop_id] = full_stops_dict[stop_id]
    
    return routes_dict, bus_stops_dict



if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    schedule = path.paths.transit_schedule
    

        #### Thay the simple scenario
    # schedule = "scenario\simple_scenario\schedule.xml"
    # plan = "scenario\simple_scenario\plans.xml"


    routes, stops = generate_bus_routes_and_stops_dict(transit_schedule_path=schedule, bus_route_hint_str="bus")
    try:
        # --- PHẦN PRINT TEST ---
        print("-" * 50)
        print(f"[*] THỐNG KÊ CHUNG:")
        print(f"    - Tổng số trạm dừng (Stops): {len(stops)}")
        print(f"    - Tổng số tuyến xe buýt (Routes): {len(routes)}")
        print("-" * 50)

        # Kiểm tra mẫu một điểm dừng
        if stops:
            sample_stop_id = next(iter(stops))
            s = stops[sample_stop_id]
            print(f"[*] TEST STOP FACILITY (Mẫu: {sample_stop_id}):")
            print(f"    - Tọa độ: x={s.coord.x}, y={s.coord.y}")
            print(f"    - Link tham chiếu: {s.ref_linkid}")

        print("-" * 50)

        # Kiểm tra mẫu một tuyến xe buýt
        if routes:
            sample_route_id = next(iter(routes))
            r = routes[sample_route_id]
            print(f"[*] TEST TRANSIT ROUTE (Mẫu: {sample_route_id}):")
            print(f"    - Thuộc Line: {r.line}")
            print(f"    - Số lượng trạm dừng: {len(r.stops_id)}")
            print(f"    - Số lượng link trong lộ trình: {len(r.links_id)}")
            
            # Kiểm tra tính toàn vẹn: xem trạm đầu tiên của tuyến có trong stops_dict không
            if r.stops_id:
                first_stop = r.stops_id[0]
                status = "Hợp lệ" if first_stop in stops else "LỖI: Không tìm thấy stop này!"
                print(f"    - Kiểm tra trạm đầu tiên ({first_stop}): {status}")

        del stops, routes
    except Exception as e:
        print(f"[LỖI HỆ THỐNG] {e}")

    # python -m src.transit.transit_schedule
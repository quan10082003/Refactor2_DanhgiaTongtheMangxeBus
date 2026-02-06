import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
from lxml import etree
import os
from src.domain.logic import is_pt_driver

def generate_travelTimeVehicle_df(events_path: str, vehtype_dict: dict, bus_hint_str: str, output_arrow_path: str, schema: list = ['vehIdList', 'vehicleTypeList', 'mainMode' , 'startTime', 'travelTime'], prefix_pt_driver="pt", batch_size=50000):
    # 1. Định nghĩa Schema (Ép kiểu string để đồng nhất khi ghi file)
    arrow_schema = pa.schema([
        (name, pa.string()) for name in schema
    ])

    temp_data = []
    person_trip_map = {} # KHỞI TẠO: Trò thiếu dòng này nên code cũ sẽ báo lỗi NameError
    context = etree.iterparse(events_path, events=('end',))

    # 2. Mở Sink và Stream Writer của Arrow
    with pa.OSFile(output_arrow_path, 'wb') as sink:
        with ipc.new_stream(sink, arrow_schema) as writer:
            
            for event, elem in context:
                if elem.tag == "event":
                    e_type = elem.get("type")

                    # --- LOGIC DEPARTURE ---
                    if e_type == "departure":
                        personId = elem.get("person")
                        if personId in person_trip_map:
                            elem.clear()
                            continue
                        if personId.startswith("pt_"):
                            elem.clear()
                            continue

                        veh_id = elem.get("vehicle")
                        time = elem.get("time")
                        mainMode = elem.get("computationalRoutingMode")

                        person_trip_map[personId] = {
                            "vehIdList": [],
                            "vehicleTypeList": [],
                            "mainMode": mainMode,
                            "startTime": float(time),
                            "travelTime": 0
                        }

                    # --- LOGIC ENTER VEHICLE ---
                    elif e_type == "PersonEntersVehicle":
                        personId = elem.get("person")
                        veh_id = elem.get("vehicle")

                        if personId not in person_trip_map:
                            elem.clear()
                            continue
                        if personId.startswith("pt_"):
                            elem.clear()
                            continue
                            
                        person_trip_map[personId]["vehIdList"].append(veh_id)

                        if veh_id in vehtype_dict:
                            person_trip_map[personId]["vehicleTypeList"].append(vehtype_dict[veh_id])
                        else:
                            person_trip_map[personId]["vehicleTypeList"].append("undefined")

                    # --- LOGIC ACTSTART (KẾT THÚC TRIP) ---
                    elif e_type == "actstart":
                        personId = elem.get("person")
                        
                        if personId not in person_trip_map:
                            elem.clear()
                            continue
                        if personId.startswith("pt_"):
                            elem.clear()
                            continue
                        if elem.get("actType") == "pt interaction":
                            elem.clear()
                            continue
                    
                        time = elem.get("time")
                        travel_time = float(time) - person_trip_map[personId]["startTime"]
                        
                        # Giữ nguyên logic lọc người đi bộ của trò
                        if len(person_trip_map[personId]["vehIdList"]) == 0 or len(person_trip_map[personId]["vehicleTypeList"]) == 0:
                            del person_trip_map[personId]
                        else:
                            # THAY THẾ CSV WRITER BẰNG ARROW BUFFER
                            veh_ids = ";".join(map(str, person_trip_map[personId]['vehIdList']))
                            veh_types = ";".join(map(str, person_trip_map[personId]['vehicleTypeList']))
                            
                            # Đưa vào temp_data theo đúng schema
                            
                            temp_data.append({
                                'vehIdList': veh_ids,
                                'vehicleTypeList': veh_types,
                                'mainMode': str(person_trip_map[personId]['mainMode']),
                                'startTime': str(person_trip_map[personId]['startTime']),
                                'travelTime': str(travel_time)
                            })
                            
                            # Kiểm tra Batch Size để ghi ra Stream
                            if len(temp_data) >= batch_size:
                                batch_df = pd.DataFrame(temp_data)
                                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                                writer.write_table(table)
                                temp_data = [] # Giải phóng RAM
                                
                            del person_trip_map[personId]

                # Giải phóng bộ nhớ XML
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            # Ghi nốt phần dư cuối cùng
            if temp_data:
                batch_df = pd.DataFrame(temp_data)
                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                writer.write_table(table)
                del temp_data

    print(f"--- Đã hoàn thành Streaming ra file Arrow IPC: {output_arrow_path} ---")

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)
    generate_travelTimeVehicle_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=path.data.interim.event.travel_time_all_vehicle)


    # python -m src.events.travel_time


    

import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
from lxml import etree
import os

from src.domain.logic import is_public_transport_bus, is_pt_driver

def generate_personEnterBus_df(events_path: str, vehtype_dict: dict, bus_hint_str: str, output_arrow_path: str, schema: list = ['person_id', 'vehicle_id'], prefix_pt_driver="pt", batch_size=50000):
    arrow_schema = pa.schema([
        (name, pa.string()) for name in schema
    ])

    temp_data = []
    # Dùng 'rb' để iterparse chạy nhanh và ổn định hơn với dữ liệu lớn
    context = etree.iterparse(events_path, events=('end',))

    # 2. Mở Sink và Stream Writer
    with pa.OSFile(output_arrow_path, 'wb') as sink:
        with ipc.new_stream(sink, arrow_schema) as writer:
            
            for event, elem in context:
                if elem.tag == "event":
                    e_type = elem.get("type")
                    
                    if e_type == "PersonEntersVehicle":
                        veh_id = elem.get("vehicle")
                        person_id = elem.get("person")

                        if veh_id not in vehtype_dict.keys() or not is_public_transport_bus(vehicle_type=vehtype_dict[veh_id], bus_hint_str=bus_hint_str):
                            elem.clear()
                            continue
                        
                        if is_pt_driver(person_id=person_id, prefix_pt_driver=prefix_pt_driver):
                            elem.clear()
                            continue

                        temp_data.append({'person_id': person_id, 'vehicle_id': veh_id})
                        
                        if len(temp_data) >= batch_size:
                            # Chuyển list dict -> DataFrame -> Arrow Table
                            batch_df = pd.DataFrame(temp_data)
                            table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                            writer.write_table(table)
                            temp_data = [] 

                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            if temp_data:
                batch_df = pd.DataFrame(temp_data)
                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                writer.write_table(table)

    print(f"--- Đã hoàn thành Streaming ra file Arrow IPC: {output_arrow_path} ---")

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)
    generate_personEnterBus_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=path.data.interim.event.person_enter_bus)

    # python -m src.events.person_enter_bus

    

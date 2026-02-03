import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import lxml
import lxml.etree as etree

from src.transit.transit_vehicle import get_transit_type_dict
from src.domain.logic import is_pt_driver, is_public_transport_bus

def generate_busDelayAtFacilities_df(events_path: str, vehtype_dict: dict, bus_hint_str: str, output_arrow_path: str, schema: list = ['vehicleId', 'vehicleType', 'facility' ,  'arrDelay', 'depDelay', 'arrTime', 'depTime'], prefix_pt_driver="pt", batch_size=50000):
    
    arrow_schema = pa.schema([(name, pa.string()) for name in schema])
    temp_bus_map ={}
    temp_data = []


    with pa.OSFile(output_arrow_path, 'wb') as sink:
        with ipc.new_stream(sink, arrow_schema) as writer:
            context = etree.iterparse(events_path, events=('end',))
            for event, elem in context:
                if elem.tag == "event":
                    e_type = elem.get("type")

                    if e_type == "VehicleArrivesAtFacility":
                        veh_id = elem.get("vehicle")
                        delay = elem.get("delay")
                        time = elem.get("time")
                        facility = elem.get("facility")
                        veh_type = vehtype_dict[veh_id]

                        if is_public_transport_bus(vehicle_type=veh_id, bus_hint_str=bus_hint_str)==False:
                            continue           
                        if delay is None:
                            delay = "null"   
                        else: 
                            temp_bus_map[veh_id] = {
                                "vehicleId": str(veh_id),
                                "vehicleType": str(veh_type),
                                "facility": facility, # Sẽ cập nhật ở event Depart
                                "arrDelay": str(delay),
                                "depDelay": "0.0",
                                "arrTime": str(time),
                                "depTime": "0.0"
                            }

                    elif e_type == "VehicleDepartsAtFacility":
                        veh_id = elem.get("vehicle")
                        delay = elem.get("delay")
                        time = elem.get("time")
                        facility = elem.get("facility")

                        if veh_id not in temp_bus_map:
                            continue
                        if delay is None:
                            delay = "0.0"
                        else: 
                            temp_bus_map[veh_id]["depTime"] = str(time)
                            temp_bus_map[veh_id]["depDelay"] = str(delay)
                            temp_data.append(temp_bus_map[veh_id])
                            del temp_bus_map[veh_id]

                            if( len(temp_data)>batch_size ):
                                df = pd.DataFrame(temp_data)
                                table = pa.Table.from_pandas(df, schema=arrow_schema)
                                writer.write_table(table)
                                temp_data = []              
         
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            if temp_data:
                df = pd.DataFrame(temp_data)
                table = pa.Table.from_pandas(df, schema=arrow_schema)
                writer.write_table(table)
                temp_data =[]

        print(f"--- Đã hoàn thành Streaming ra file Arrow IPC: {output_arrow_path} ---")

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)
    generate_busDelayAtFacilities_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=path.data.interim.event.bus_delay_at_facilities)

    # python -m src.events.bus_delay
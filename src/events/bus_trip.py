import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
from lxml import etree
import os

from src.domain.logic import is_pt_driver, is_public_transport_bus

def generate_busTrip_df(
    events_path: str, 
    links_dict: dict, 
    vehtype_dict: dict, 
    bus_hint_str: str, 
    output_arrow_path: str, 
    schema: list = ['busId', 'linkId', 'linkLen', 'havePassenger', 'travelTime'], 
    batch_size=50000
):
    """
    Generates Bus Trip Data Arrow file from MATSim events.
    Logic ported from BusTripExtractor.kt.
    """
    
    # 1. Define Schema (All strings for consistency with existing modules)
    arrow_schema = pa.schema([
        (name, pa.string()) for name in schema
    ])

    temp_data = []
    link_length_dict = {k: v.length for k, v in links_dict.items()}
    
    # State maps
    # busTrips[busId] = {
    #   "busId": str, "currentLinkId": str, "passengers": int, 
    #   "enterTime": float, "pendingPassengers": int
    # }
    bus_trips = {}
    veh_driver_map = {}

    context = etree.iterparse(events_path, events=('end',))

    # 2. Open Sink and Stream Writer
    with pa.OSFile(output_arrow_path, 'wb') as sink:
        with ipc.new_stream(sink, arrow_schema) as writer:
            
            for event, elem in context:
                if elem.tag == "event":
                    e_type = elem.get("type")
                    time_str = elem.get("time")
                    time = float(time_str) if time_str else 0.0
                    attrs = dict(elem.attrib) # Get attributes

                    # --- TransitDriverStarts ---
                    if e_type == "TransitDriverStarts":
                        vehicle_id = attrs.get("vehicleId")
                        # Lookup vehicle type
                        if vehicle_id not in vehtype_dict.keys() or not is_public_transport_bus(vehicle_type=vehtype_dict[vehicle_id], bus_hint_str=bus_hint_str):
                            continue
                        veh_driver_map[vehicle_id] = attrs.get("driverId")

                    # --- vehicle enters traffic ---
                    elif e_type == "vehicle enters traffic":
                        vehicle_id = attrs.get("vehicle")
                        # Lookup vehicle type
                        if vehicle_id not in vehtype_dict.keys() or not is_public_transport_bus(vehicle_type=vehtype_dict[vehicle_id], bus_hint_str=bus_hint_str):
                           continue
                            
                        bus_trips[vehicle_id] = {
                            "busId": vehicle_id,
                            "currentLinkId": attrs.get("link"),
                            "passengers": 0,
                            "pendingPassengers": 0,
                            "enterTime": time
                        }

                    # --- entered link ---
                    elif e_type == "entered link":
                        vehicle_id = attrs.get("vehicle")
                        if vehicle_id in bus_trips:
                            trip = bus_trips[vehicle_id]
                            # Update state (copy behavior)
                            trip["currentLinkId"] = attrs.get("link")
                            trip["passengers"] = trip["pendingPassengers"]
                            trip["enterTime"] = time

                    # --- PersonEntersVehicle ---
                    elif e_type == "PersonEntersVehicle":
                        vehicle_id = attrs.get("vehicle")
                        person_id = attrs.get("person")
                        
                        if vehicle_id in bus_trips:
                            # If person is driver, ignore
                            if person_id != veh_driver_map.get(vehicle_id):
                                bus_trips[vehicle_id]["pendingPassengers"] += 1

                    # --- PersonLeavesVehicle ---
                    elif e_type == "PersonLeavesVehicle":
                        vehicle_id = attrs.get("vehicle")
                        person_id = attrs.get("person")
                        
                        if vehicle_id in bus_trips:
                            # If person is driver, ignore
                            if person_id != veh_driver_map.get(vehicle_id):
                                bus_trips[vehicle_id]["pendingPassengers"] -= 1

                    # --- left link ---
                    elif e_type == "left link":
                        vehicle_id = attrs.get("vehicle")
                        if vehicle_id in bus_trips:
                            trip = bus_trips[vehicle_id]
                            link_id = trip["currentLinkId"]
                            
                            # Calculate data
                            link_len = link_length_dict.get(link_id, 0.0)
                            have_passenger = trip["passengers"] > 0
                            travel_time = time - trip["enterTime"]
                            
                            # Push data
                            temp_data.append({
                                'busId': str(trip["busId"]),
                                'linkId': str(link_id),
                                'linkLen': str(link_len),
                                'havePassenger': str(have_passenger).lower(), # 'true'/'false'
                                'travelTime': str(travel_time)
                            })
                            
                            # Batch Write
                            if len(temp_data) >= batch_size:
                                batch_df = pd.DataFrame(temp_data)
                                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                                writer.write_table(table)
                                temp_data = []

                    # --- vehicle leaves traffic ---
                    elif e_type == "vehicle leaves traffic":
                        vehicle_id = attrs.get("vehicle")
                        if vehicle_id in bus_trips:
                            trip = bus_trips.pop(vehicle_id) # Remove and get
                            
                            # Final checks similar to Kotlin require(trip.pendingPassengers == 0)
                            # We won't crash, but won't record if logic is weird? 
                            # Actually we just replicate the write logic from Kotlin
                            
                            link_id = trip["currentLinkId"]
                            link_len = link_length_dict.get(link_id, 0.0)
                            have_passenger = trip["passengers"] > 0
                            travel_time = time - trip["enterTime"]

                            temp_data.append({
                                'busId': str(trip["busId"]),
                                'linkId': str(link_id),
                                'linkLen': str(link_len),
                                'havePassenger': str(have_passenger).lower(),
                                'travelTime': str(travel_time)
                            })

                            if len(temp_data) >= batch_size:
                                batch_df = pd.DataFrame(temp_data)
                                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                                writer.write_table(table)
                                temp_data = []
                            
                            if vehicle_id in veh_driver_map:
                                del veh_driver_map[vehicle_id]

                # Free memory
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            # Write remaining
            if temp_data:
                batch_df = pd.DataFrame(temp_data)
                table = pa.Table.from_pandas(batch_df, schema=arrow_schema)
                writer.write_table(table)
                del temp_data

    print(f"--- Đã hoàn thành Streaming ra file Arrow IPC: {output_arrow_path} ---")

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.network.network import generate_nodes_and_links_dict
    from src.transit.transit_vehicle import get_transit_type_dict
    
    # 1. Load Config
    path_config = load_config(r"config/config_path.yaml")
    bus_hint = "bus"
    
    # 2. Get Link Lengths
    print("Loading Network...")
    _, links_dict = generate_nodes_and_links_dict(path_config.paths.network)
    
    
    # 3. Get Bus IDs (using Transit Vehicle to find 'bus' types)
    print("Loading Vehicles...")
    vehtype_dict = get_transit_type_dict(path_config.paths.transit_vehicle)


    
    
    bus_trip_path = path_config.data.interim.event.bus_trip
    # Ensure folder exists
    if not os.path.exists(os.path.dirname(bus_trip_path)):
        os.makedirs(os.path.dirname(bus_trip_path))

    print("Generating Bus Trips...")
    generate_busTrip_df(
        events_path=path_config.paths.events,
        links_dict=links_dict,
        bus_hint_str=bus_hint,
        vehtype_dict=vehtype_dict,
        output_arrow_path=bus_trip_path
    )

    # python -m src.events.bus_trip
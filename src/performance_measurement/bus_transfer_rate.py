import pyarrow as pa
import pyarrow.ipc as ipc
import os
from src.domain.logic import is_public_transport_bus

def calculate_bus_transfer_rate(person_trip_arrow_path: str, veh_type_dict: dict, bus_hint_str: str) -> float:
    """
    Calculates the Average Bus-to-Bus Transfer Rate per PT Trip.
    
    Logic based on provided Kotlin:
    1. Filter for trips where main_mode == 'pt'
    2. Count adjacent vehicle pairs (prev, next) where BOTH are buses.
    3. Sum transfers / Total PT Trips.
    """
    
    if not os.path.exists(person_trip_arrow_path):
        print(f"File not found: {person_trip_arrow_path}")
        return 0.0

    total_transfers = 0
    total_trips = 0

    try:
        with pa.OSFile(person_trip_arrow_path, 'rb') as source:
            reader = ipc.open_stream(source)
            for batch in reader:
                main_modes = batch['mainMode'].to_pylist()
                veh_type_lists = batch['vehicleTypeList'].to_pylist()
                
                for mode, v_types_str in zip(main_modes, veh_type_lists):
                    if mode != 'pt':
                        continue
                        
                    total_trips += 1
                    
                    if not v_types_str:
                        continue
                        
                    # Split string to list
                    veh_types = v_types_str.split(';')

                    
                    trip_transfers = 0
                    for i in range(len(veh_types) - 1):
                        prev_type = veh_types[i]
                        next_type = veh_types[i+1]
                        
                        if (is_public_transport_bus(prev_type, bus_hint_str) and 
                            is_public_transport_bus(next_type, bus_hint_str)):
                            trip_transfers += 1
                            
                    total_transfers += trip_transfers
                    
    except Exception as e:
        print(f"Error calculating transfer rate: {e}")
        return 0.0

    if total_trips == 0:
        return 0.0
        
    return float(total_transfers) / total_trips


if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    
    person_trip_path = path.data.interim.event.people_trip
    # Assuming config for bus hint exists or hardcoded
    bus_hint = "bus" 
    
    print("Calculating Bus Transfer Rate...")
    rate = calculate_bus_transfer_rate(person_trip_path, bus_hint)
    print(f"[*] Bus-to-Bus Transfer Rate: {rate:.4f} transfers/trip")
def is_public_transport_bus(vehicle_type: str, bus_hint_str: str) -> bool:
    if bus_hint_str in vehicle_type.lower():
        return True
    else:
        return False

def is_pt_driver(person_id: str, prefix_pt_driver:str):
    if person_id.startswith(prefix_pt_driver):
        return True
    else: 
        return False

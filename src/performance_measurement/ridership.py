from src.transit.transit_vehicle import get_transit_type_dict
from src.events.person_enter_bus import generate_personEnterBus_df

import pyarrow as pa
import pyarrow.ipc as ipc

def calculte_ridership(person_enter_bus_arrow_path: str):
    ridership = 0

    with pa.OSFile(person_enter_bus_arrow_path, 'rb') as source:
        person_enter_bus_table = ipc.open_stream(source).read_all()     
    unique_person_ids = person_enter_bus_table.column('person_id').unique()
    ridership = len(unique_person_ids)

    return ridership


if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    from src.plan.plan import generate_people_acts_coord_dict

    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)


    people_number = len(generate_people_acts_coord_dict(path.paths.plan))
    person_enter_bus_path = path.data.interim.event.person_enter_bus
    generate_personEnterBus_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=person_enter_bus_path)

    ridership = calculte_ridership(person_enter_bus_path)
    print(f" Rider ship là: {ridership}, trên tổng số {people_number} dân. {ridership/people_number*100:.2f} %" )

    # python -m src.performance_measurement.ridership



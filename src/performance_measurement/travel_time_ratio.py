from src.transit.transit_vehicle import get_transit_type_dict
from src.events.travel_time import generate_travelTimeVehicle_df
from src.domain.logic import is_public_transport_bus

import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.compute as pc
import numpy as np

def calculate_average_bus_travel_time(travel_time_path: str, bus_hint_str: str) -> (float, int):
    with pa.OSFile(travel_time_path, 'rb') as source:
        table = ipc.open_stream(source).read_all()     

    bus_mask_list = [
        is_public_transport_bus(str(v), bus_hint_str) 
        for v in table['vehicleTypeList'].to_pylist()
    ]
    
    # Chuyển list boolean ngược lại thành Arrow Array để lọc
    bus_mask = pa.array(bus_mask_list)
    bus_table = table.filter(bus_mask)        
    bus_trip = len(bus_table)
    
    if len(bus_table) > 0:
        # Ép kiểu sang float để tính toán chính xác
        travel_times = pc.cast(bus_table['travelTime'], pa.float64())
        average_bus_travel_time = pc.mean(travel_times).as_py()
    else:
        average_bus_travel_time = 0.0

    return average_bus_travel_time, bus_trip


def calculate_average_car_travel_time(travel_time_path: str) -> (float, int):
    with pa.OSFile(travel_time_path, 'rb') as source:
        table = ipc.open_stream(source).read_all()     

    car_mask = pc.equal(table['mainMode'], 'car')
    car_table = table.filter(car_mask)
    car_trip = len(car_table)
    
    if len(car_table) > 0:
        travel_times = pc.cast(car_table['travelTime'], pa.float64())
        average_car_travel_time = pc.mean(travel_times).as_py()
    else:
        average_car_travel_time = 0.0
        
    return average_car_travel_time, car_trip


def calculate_travel_time_ratio_KPI(bus_avg_time: float, car_avg_time: float):
    """
    Công thức tính tỷ lệ thời gian di chuyển trung bình của 1 chuyến bus / car ( bus là tính cả thời gian đi bộ)
    """
    return np.exp(-bus_avg_time/car_avg_time)


def calculate_bus_travel_time_ratio_KPI(before_bus_avg_time: float, after_bus_avg_time: float):
    """
    Công thức tính tỷ lệ thời gian di chuyển trung bình của bus trước và sau ( bus là tính cả thời gian đi bộ)
    """
    return np.exp(-after_bus_avg_time/before_bus_avg_time)

if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)

    travel_time_arrow_path = path.data.interim.event.travel_time_all_vehicle
    generate_travelTimeVehicle_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=travel_time_arrow_path)

    average_bus_travel_time, bus_trip = calculate_average_bus_travel_time(travel_time_path=travel_time_arrow_path, bus_hint_str="bus")
    average_car_travel_time, car_trip = calculate_average_car_travel_time(travel_time_path=travel_time_arrow_path)
    bus_travel_time_ratio_KPI = calculate_bus_travel_time_ratio_KPI(before_bus_avg_time= 54.121 * 60, after_bus_avg_time=average_bus_travel_time)
    travel_time_ratio_KPI = calculate_travel_time_ratio_KPI(bus_avg_time=average_bus_travel_time, car_avg_time=average_car_travel_time)
        
    print(f"Average bus travel time: {average_bus_travel_time} seconds, in {bus_trip} trips")
    print(f"Average car travel time: {average_car_travel_time} seconds, in {car_trip} trips")
    print(f"Bus travel time ratio before and after: {bus_travel_time_ratio_KPI}")
    print(f"Travel time ratio between bus and car: {travel_time_ratio_KPI}")

    # python -m src.performance_measurement.travel_time_ratio
from src.transit.core_class import TransitRoute, StopFacility
from src.transit.transit_schedule import generate_bus_routes_and_stops_dict
from src.network.core_class import Node, Link
from src.network.network import generate_nodes_and_links_dict

import numpy as np
    
def calculate_avg_km_and_stop_in_bus_network( routes_dict: dict[str,TransitRoute], links_dict: dict[str,Link]) -> (float, float):
    stop_number_list = []
    km_route_list = []

    for route in routes_dict.values():
        stop_number_list.append(float(len(route.stops_id)))
        km_route = 0
        for link_id in route.links_id:
            km_route += links_dict[link_id].length
        km_route_list.append(km_route)
    
    mean_stop_per_route =np.mean(stop_number_list)
    mean_km_per_route = np.mean(km_route_list)

    return mean_km_per_route, mean_stop_per_route

if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    schedule = path.paths.transit_schedule
    network = path.paths.network

    routes_dict, _ = generate_bus_routes_and_stops_dict(transit_schedule_path=schedule, bus_route_hint_str="bus")
    _, links_dict = generate_nodes_and_links_dict(network_path=network)

    mean_km_per_route, mean_stop_per_route = calculate_avg_km_and_stop_in_bus_network(routes_dict=routes_dict, links_dict=links_dict)
    print(f" So tram dung trung binh cua 1 tuyen: {mean_stop_per_route}")
    print(f" So km di trung binh cua 1 tuyen: {mean_km_per_route/1000}")

    # python -m src.performance_measurement.bus_route_info



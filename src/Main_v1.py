from src.utils.folder_creator import create_folders
from src.data.load_config import load_config
from src.domain.point import Point
from src.network.network import generate_nodes_and_links_dict
from src.network.core_class import get_boundary_nodes_of_network
from src.plan.plan import generate_people_acts_coord_dict
from src.plan.core_class import get_boundary_nodes_of_plans
from src.transit.transit_schedule import generate_bus_routes_and_stops_dict
from src.transit.transit_vehicle import get_transit_type_dict
from src.od_mask.generator import ZoneGeneratorByGrid
from src.events.person_trip import generate_personTrip_df
from src.events.person_enter_bus import generate_personEnterBus_df
from src.events.travel_time import generate_travelTimeVehicle_df
from src.events.bus_delay import generate_busDelayAtFacilities_df
from src.performance_measurement.bus_route_info import calculate_avg_km_and_stop_in_bus_network
from src.performance_measurement.travel_time_ratio import calculate_average_bus_travel_time
from src.performance_measurement.travel_time_ratio import calculate_average_car_travel_time
from src.performance_measurement.travel_time_ratio import calculate_bus_travel_time_ratio_KPI
from src.performance_measurement.travel_time_ratio import calculate_travel_time_ratio_KPI
from src.performance_measurement.service_coverage import calculte_service_coverage
from src.performance_measurement.ridership import calculte_ridership
from src.performance_measurement.otp import calculte_otp
from src.visualize.busroute_heatmap import draw_busroute_heatmap
from src.visualize.od_heatmap import draw_od_heatmap
from src.visualize.person_trip_analysis import analyze_person_trips

def main():
    path = load_config(r"config/config_path.yaml")
    param = load_config(r"config/config_param.yaml")

    #param
    scenario_name = path.scenario
    bus_route_hint_str = param.bus_route_hint_str
    cols = param.zone.cols
    rows = param.zone.rows
    radia_m = param.zone.radia_m
    act_coveraged = param.service_coveraged.act_coveraged
    max_delay = param.otp.max_delay
    min_delay = param.otp.min_delay
    before_bus_avg_time = param.travel_time.before_bus_avg_time
    od_visualize_number = param.visualize.od_heatmap.od_visualize_number
    top_od_number = param.visualize.person_trip_analysis.od_visualize_number
    max_busroute_number_to_draw = param.visualize.bus_heatmap.max_busroute_number_to_draw

    #input
    events = path.paths.events
    plan = path.paths.plan
    network = path.paths.network
    schedule = path.paths.transit_schedule
    vehicle = path.paths.transit_vehicle

    #output interim
    bus_delay_at_facilities = path.data.interim.event.bus_delay_at_facilities
    person_enter_bus = path.data.interim.event.person_enter_bus
    travel_time_all_vehicle = path.data.interim.event.travel_time_all_vehicle
    people_trip = path.data.interim.event.people_trip
    create_folders(bus_delay_at_facilities,person_enter_bus,travel_time_all_vehicle,people_trip)         #create folder

    #output processed
    kpi_result = path.data.processed.kpi_result
    busroute_heatmap_image_path = path.data.interim.visualize.bus_heatmap
    od_heatmap_image_path = path.data.interim.visualize.od_heatmap
    person_trip_analysis_output_folder = path.data.interim.visualize.person_trip_analysis
    create_folders(kpi_result, busroute_heatmap_image_path, od_heatmap_image_path, person_trip_analysis_output_folder)


    #dict necessary for caculating performance measurement
    nodes_dict, links_dict = generate_nodes_and_links_dict(network)
    people_dict = generate_people_acts_coord_dict(plan)
    bus_route_dict, bus_stops_dict = generate_bus_routes_and_stops_dict(transit_schedule_path=schedule, bus_route_hint_str=bus_route_hint_str)
    pt_type_dict = get_transit_type_dict(vehicle)

    #generate zone
    min_p_network, max_p_network = get_boundary_nodes_of_network(nodes_dict)
    min_p_plan, max_p_plan = get_boundary_nodes_of_plans(people_dict)
    min_p = Point(min(min_p_network.x, min_p_plan.x), min(min_p_network.y, min_p_plan.y))
    max_p = Point(max(max_p_network.x, max_p_plan.x), max(max_p_network.y, max_p_plan.y))
    zone_gen = ZoneGeneratorByGrid(max_p=max_p, min_p=min_p, rows=rows, cols=cols)
    zone_list = zone_gen.generate()
    
    #generate imterim arrrow file
    generate_busDelayAtFacilities_df(
        events_path=path.paths.events, 
        vehtype_dict=pt_type_dict, 
        bus_hint_str=bus_route_hint_str, 
        output_arrow_path=bus_delay_at_facilities)
    generate_personEnterBus_df(
        events_path=path.paths.events, 
        vehtype_dict=pt_type_dict, 
        bus_hint_str=bus_route_hint_str, 
        output_arrow_path=person_enter_bus)
    generate_travelTimeVehicle_df(
        events_path=path.paths.events, 
        vehtype_dict=pt_type_dict, 
        bus_hint_str=bus_route_hint_str, 
        output_arrow_path=travel_time_all_vehicle)
    generate_personTrip_df(
        events_path=path.paths.events, 
        vehtype_dict=pt_type_dict, 
        zone_finder=zone_gen,
        bus_hint_str=bus_route_hint_str, 
        output_arrow_path=people_trip)

    #calculate performance measurement
    mean_km_per_route, mean_stop_per_route = calculate_avg_km_and_stop_in_bus_network(routes_dict=bus_route_dict, links_dict=links_dict)

    average_bus_travel_time, bus_trip = calculate_average_bus_travel_time(travel_time_path=travel_time_all_vehicle, bus_hint_str=bus_route_hint_str)
    average_car_travel_time, car_trip = calculate_average_car_travel_time(travel_time_path=travel_time_all_vehicle)
    bus_travel_time_ratio_KPI = calculate_bus_travel_time_ratio_KPI(before_bus_avg_time= before_bus_avg_time, after_bus_avg_time=average_bus_travel_time)
    travel_time_ratio_KPI = calculate_travel_time_ratio_KPI(bus_avg_time=average_bus_travel_time, car_avg_time=average_car_travel_time)
                
    service_coverage = calculte_service_coverage(
        people_dict=people_dict, 
        bus_stops_dict=bus_stops_dict, 
        radia_m=radia_m, 
        act_coveraged=act_coveraged
    )
    people_number = len(people_dict)
    
    ridership = calculte_ridership(person_enter_bus)
    ontime, total, otp_percent = calculte_otp(bus_delay_path=bus_delay_at_facilities, max_delay=max_delay, min_delay=min_delay)

    #visualize
    draw_busroute_heatmap(
        output_image_path=busroute_heatmap_image_path, 
        network_path=network, 
        bus_route_data=list(bus_route_dict.values()),
        max_freq_limit=max_busroute_number_to_draw)
    draw_od_heatmap(
        network_path=network, 
        schedule_path=schedule, 
        zones_list=zone_list,
        od_visualize_number=od_visualize_number,
        people_trip_arrow_path=people_trip,
        save_image_path=od_heatmap_image_path, 
        scenario_name=scenario_name, 
        grid_info=f"{rows}x{cols}")

    analyze_person_trips(
        people_trip_arrow_path=people_trip,
        network_path=network,
        schedule_path=schedule,
        zones_list=zone_list,
        output_folder=person_trip_analysis_output_folder,
        top_od_number=top_od_number,
        scenario_name=scenario_name,
        grid_info=f"{rows}x{cols}"
    )

    #delete variable to free memory
    del people_dict
    del bus_route_dict
    del bus_stops_dict
    del pt_type_dict
    del zone_gen
    del people_trip
    del person_enter_bus
    del travel_time_all_vehicle
    del bus_delay_at_facilities
    
    #write kpi result
    with open(kpi_result, "w", encoding="utf-8") as f:
        f.write(f"--- BÁO CÁO KẾT QUẢ KPI MÔ PHỎNG (Scenario: {scenario_name}) ---\n\n")
        f.write(f"1. THÔNG SỐ MẠNG LƯỚI XE BUÝT:\n")
        f.write(f"   - Số trạm dừng trung bình/tuyến: {mean_stop_per_route:.2f} trạm\n")
        f.write(f"   - Chiều dài trung bình/tuyến: {mean_km_per_route/1000:.2f} km\n\n")
        f.write(f"2. HIỆU SUẤT THỜI GIAN (TRAVEL TIME):\n")
        f.write(f"   - Bus (Trung bình): {average_bus_travel_time:.2f} s (trong {bus_trip} chuyến)\n")
        f.write(f"   - Car (Trung bình): {average_car_travel_time:.2f} s (trong {car_trip} chuyến)\n")
        f.write(f"   - Tỉ lệ Bus trước/sau: {bus_travel_time_ratio_KPI:.4f}\n")
        f.write(f"   - Tỉ lệ Bus/Car: {travel_time_ratio_KPI:.4f}\n\n")
        f.write(f"3. ĐỘ BAO PHỦ & NHU CẦU PHỤC VỤ:\n")
        f.write(f"   - Vùng phục vụ ({radia_m}m): {service_coverage} / {people_number} dân\n")
        f.write(f"   - Tỉ lệ bao phủ (Service Coverage): {service_coverage/people_number*100:.2f}%\n")
        ridership_percent = (ridership/people_number*100) if people_number > 0 else 0
        f.write(f"   - Ridership: {ridership} người ({ridership_percent:.2f}% dân số)\n\n")
        f.write(f"4. ĐỘ ĐÚNG GIỜ (ON-TIME PERFORMANCE):\n")
        f.write(f"   - On-time arrivals: {ontime} / {total} chuyến\n")
        f.write(f"   - Chỉ số OTP: {otp_percent:.2f}%\n")

    print(f"[*] Đã xuất kết quả KPI ra file: {kpi_result}")

    

if __name__ == "__main__":
    main()
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
from src.events.bus_trip import generate_busTrip_df
from src.performance_measurement.bus_route_info import calculate_avg_km_and_stop_in_bus_network
from src.performance_measurement.travel_time_ratio import calculate_average_bus_travel_time
from src.performance_measurement.travel_time_ratio import calculate_average_car_travel_time
from src.performance_measurement.travel_time_ratio import calculate_bus_travel_time_ratio_KPI
from src.performance_measurement.travel_time_ratio import calculate_travel_time_ratio_KPI
from src.performance_measurement.service_coverage import calculte_service_coverage
from src.performance_measurement.ridership import calculte_ridership
from src.performance_measurement.otp import calculte_otp
from src.performance_measurement.bus_productivity_effeciency import get_bus_service_metrics,calculate_effective_dist_ratio, calculate_productivity_index, calculate_bus_efficiency_index
from src.visualize.busroute_heatmap import draw_busroute_heatmap
from src.visualize.od_heatmap import draw_od_heatmap
from src.visualize.person_trip_analysis import analyze_person_trips
from src.visualize.compare import plot_scenario_comparison, load_data
from src.visualize.merge_image import merge_images_side_by_side
from omegaconf import OmegaConf
import pandas as pd
import os

def run_scenario(scenario_name: str, path: dict, param: dict):
    print(f"\n{'='*50}")
    print(f"RUNNING SCENARIO: {scenario_name}")
    print(f"{'='*50}\n")
    
    #param
    bus_route_hint_str = param.bus_route_hint_str
    cols = param.zone.cols
    rows = param.zone.rows
    radia_m = param.zone.radia_m
    act_coveraged = param.service_coveraged.act_coveraged
    max_delay = param.otp.max_delay
    min_delay = param.otp.min_delay
    baseline = param.productivity.coefficient

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
    bus_trip_path = path.data.interim.event.bus_trip
    create_folders(bus_delay_at_facilities,person_enter_bus,travel_time_all_vehicle,people_trip)         #create folder

    #output processed
    all_kpi_result = path.data.processed.all_kpi_result
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
    generate_busTrip_df(
        events_path=path.paths.events,
        links_dict=links_dict,
        bus_hint_str=bus_route_hint_str,
        vehtype_dict=pt_type_dict,
        output_arrow_path=bus_trip_path
    )

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

    bus_metrics = get_bus_service_metrics(bus_trip_path)
    prod_index = calculate_productivity_index(bus_metrics['service_hours'], ridership, baseline)
    eff_index = calculate_bus_efficiency_index(bus_metrics['total_km'], ridership)
    dist_ratio = calculate_effective_dist_ratio(bus_metrics['effective_km'], bus_metrics['total_km'])

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
    del person_enter_bus
    del travel_time_all_vehicle
    del bus_delay_at_facilities
    
    #write kpi result
    with open(kpi_result, "w", encoding="utf-8") as f:
        f.write(f"\n--- BÁO CÁO KẾT QUẢ KPI MÔ PHỎNG (Scenario: {scenario_name}) ---\n")
        f.write(f"1. THÔNG SỐ MẠNG LƯỚI XE BUÝT:\n")
        f.write(f"   - Số trạm dừng trung bình/tuyến: {mean_stop_per_route:.2f} trạm\n")
        f.write(f"   - Chiều dài trung bình/tuyến: {mean_km_per_route/1000:.2f} km\n\n")
        f.write(f"2. HIỆU SUẤT THỜI GIAN (TRAVEL TIME):\n")
        f.write(f"   - Tỉ lệ Bus trước/sau: {bus_travel_time_ratio_KPI:.4f}\n")
        f.write(f"   - Tỉ lệ Bus/Car: {travel_time_ratio_KPI:.4f}\n\n")
        f.write(f"   - Bus (Trung bình): {average_bus_travel_time:.2f} s (trong {bus_trip} chuyến)\n")
        f.write(f"   - Car (Trung bình): {average_car_travel_time:.2f} s (trong {car_trip} chuyến)\n\n")
        f.write(f"3. ĐỘ BAO PHỦ & NHU CẦU PHỤC VỤ:\n")
        ridership_percent = (ridership/people_number*100) if people_number > 0 else 0
        f.write(f"   - Ridership: {ridership} người ({ridership_percent:.2f}% dân số)\n")
        f.write(f"   - Service Coverage: {service_coverage/people_number*100:.2f}%\n")
        f.write(f"   - Vùng phục vụ ({radia_m}m): {service_coverage} / {people_number} dân\n\n")
        f.write(f"4. ĐỘ ĐÚNG GIỜ (ON-TIME PERFORMANCE):\n")
        f.write(f"   - OTP: {otp_percent:.2f}%\n")
        f.write(f"   - On-time arrivals: {ontime} / {total} chuyến\n\n")
        f.write(f"5. HIỆU SUẤT XE BUÝT:\n")
        f.write(f"   - Productivity Index: {prod_index:.6f}\n")
        f.write(f"   - Efficiency Index:   {eff_index:.6f}\n")
        f.write(f"   - Effective Dist Ratio: {dist_ratio:.4f}\n\n")
    
    with open(all_kpi_result, "a", encoding="utf-8") as f:
        f.write(f"\n--- BÁO CÁO KẾT QUẢ KPI MÔ PHỎNG (Scenario: {scenario_name}) ---\n")
        f.write(f"1. THÔNG SỐ MẠNG LƯỚI XE BUÝT:\n")
        f.write(f"   - Số trạm dừng trung bình/tuyến: {mean_stop_per_route:.2f} trạm\n")
        f.write(f"   - Chiều dài trung bình/tuyến: {mean_km_per_route/1000:.2f} km\n\n")
        f.write(f"2. HIỆU SUẤT THỜI GIAN (TRAVEL TIME):\n")
        f.write(f"   - Tỉ lệ Bus trước/sau: {bus_travel_time_ratio_KPI:.4f}\n")
        f.write(f"   - Tỉ lệ Bus/Car: {travel_time_ratio_KPI:.4f}\n\n")
        f.write(f"   - Bus (Trung bình): {average_bus_travel_time:.2f} s (trong {bus_trip} chuyến)\n")
        f.write(f"   - Car (Trung bình): {average_car_travel_time:.2f} s (trong {car_trip} chuyến)\n\n")
        f.write(f"3. ĐỘ BAO PHỦ & NHU CẦU PHỤC VỤ:\n")
        ridership_percent = (ridership/people_number*100) if people_number > 0 else 0
        f.write(f"   - Ridership: {ridership} người ({ridership_percent:.2f}% dân số)\n")
        f.write(f"   - Service Coverage: {service_coverage/people_number*100:.2f}%\n")
        f.write(f"   - Vùng phục vụ ({radia_m}m): {service_coverage} / {people_number} dân\n\n")
        f.write(f"4. ĐỘ ĐÚNG GIỜ (ON-TIME PERFORMANCE):\n")
        f.write(f"   - OTP: {otp_percent:.2f}%\n")
        f.write(f"   - On-time arrivals: {ontime} / {total} chuyến\n\n")
        f.write(f"5. HIỆU SUẤT XE BUÝT:\n")
        f.write(f"   - Productivity Index: {prod_index:.6f}\n")
        f.write(f"   - Efficiency Index:   {eff_index:.6f}\n")
        f.write(f"   - Effective Dist Ratio: {dist_ratio:.4f}\n\n")

    print(f"[*] Đã xuất kết quả KPI ra file: {kpi_result}")

    return {
        "scenario": scenario_name,
        "people_trip_path": people_trip,
        "output_folder": path.data.interim.visualize.od_heatmap # Folder for comparison outputs? Or store parent folder
    }

def main():
    # 1. Load basic configs
    base_path_config = load_config(r"config/config_path.yaml")
    base_param_config = load_config(r"config/config_param.yaml")
    
    scenario_list = base_path_config.scenario_list
    print(f"Scenarios to run: {scenario_list}")
    all_kpi_result = base_path_config.data.processed.all_kpi_result
    create_folders(all_kpi_result)
    with open(all_kpi_result, "w", encoding="utf-8") as f:
        f.write(f"")


    
    scenario_results = []
    
    # 2. Iterate and Run
    for sc_name in scenario_list:
        # Clone base config to avoid mutating global state weirdly
        # Note: load_config uses OmegaConf.load, so we just reload or use overrides.
        # Since we need to update paths based on ${scenario}, we must override it BEFORE resolving.
        # But load_config calls resolve(). So we manually load and resolve here.
        
        # Manually load to allow override
        raw_path_cfg = OmegaConf.load(r"config/config_path.yaml")
        
        # Override scenario variable
        # Assuming 'scenario' is a key in config_path.yaml that is used for interpolation
        raw_path_cfg.scenario = sc_name 
        
        # Resolve now
        OmegaConf.resolve(raw_path_cfg)
        
        # Run
        result = run_scenario(sc_name, raw_path_cfg, base_param_config)
        scenario_results.append(result)
        
    # 3. Compare Scenarios
    print(f"\n{'='*50}")
    print(f"STARTING COMPARISON FOR: {[r['scenario'] for r in scenario_results]}")
    print(f"{'='*50}\n")
    
    compare_list = []
    output_comparison_folder = base_path_config.data.comparasion.comparison_folder
    
    for res in scenario_results:
        p_path = res["people_trip_path"]
        s_name = res["scenario"]
        df = load_data(p_path)
        if not df.empty:
            compare_list.append((s_name, df))
            
    if compare_list:
        plot_scenario_comparison(compare_list, output_comparison_folder, top_k=10)
    else:
        print("No valid data found for comparison.")

    # 4. Merge Requested Images
    print(f"\n{'='*50}")
    print("MERGING IMAGES")
    print(f"{'='*50}\n")
    
    if len(scenario_list) >= 2:
        sc1_name = scenario_list[0]
        sc2_name = scenario_list[1]
        
        # Helper to resolve path for a specific scenario
        def get_resolved_config(sc_name):
            cfg = OmegaConf.load(r"config/config_path.yaml")
            cfg.scenario = sc_name
            OmegaConf.resolve(cfg)
            return cfg

        cfg1 = get_resolved_config(sc1_name)
        cfg2 = get_resolved_config(sc2_name)

        # 1. Bus OD Heatmap
        img1_a = cfg1.data.interim.visualize.bus_heatmap
        img1_b = cfg2.data.interim.visualize.bus_heatmap
        
        # 2. Global Summary (Appended filename to folder path)
        img2_a = os.path.join(cfg1.data.interim.visualize.person_trip_analysis, "00_global_summary.png")
        img2_b = os.path.join(cfg2.data.interim.visualize.person_trip_analysis, "00_global_summary.png")
        
        # Execute Merge
        merge_images_side_by_side(img1_a, img1_b, os.path.join(output_comparison_folder, "Merged_Bus_OD_Heatmap.png"))
        merge_images_side_by_side(img2_a, img2_b, os.path.join(output_comparison_folder, "Merged_Global_Summary.png"))

if __name__ == "__main__":
    main()
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.compute as pc
import numpy as np
import os

# --- PART 1: DATA EXTRACTION FUNCTIONS ---

def get_bus_service_metrics(bus_trip_arrow_path: str):
    total_service_time = 0.0
    revenue_service_time = 0.0
    total_distance = 0.0
    effective_distance = 0.0

    with pa.OSFile(bus_trip_arrow_path, 'rb') as source:
        reader = ipc.open_stream(source)
        for batch in reader:
            # Cast columns
            travel_times = pc.cast(batch['travelTime'], pa.float64())
            link_lens = pc.cast(batch['linkLen'], pa.float64())
            # 1. Total Service Time
            t_sum = pc.sum(travel_times).as_py()
            if t_sum: total_service_time += t_sum
            # 2. Total Distance
            d_sum = pc.sum(link_lens).as_py()
            if d_sum: total_distance += d_sum
            # Create Mask for 'havePassenger' == 'true'
            mask = pc.equal(batch['havePassenger'], 'true')
            # 3. Revenue Time (Filter then Sum)
            # Only sum travelTime where mask is true
            rev_time_sum = pc.sum(pc.filter(travel_times, mask)).as_py()
            if rev_time_sum: revenue_service_time += rev_time_sum
            # 4. Effective Distance (Filter then Sum)
            eff_dist_sum = pc.sum(pc.filter(link_lens, mask)).as_py()
            if eff_dist_sum: effective_distance += eff_dist_sum

    return {
        "service_hours": total_service_time / 3600.0,
        "revenue_hours": revenue_service_time / 3600.0,
        "total_km": total_distance/1000,
        "effective_km": effective_distance/1000  
    }


# --- PART 2: CALCULATION FUNCTIONS (PURE LOGIC) ---

def calculate_productivity_index(service_hours: float, unique_passengers: int, baseline: float) -> float:
    """
    Formula: exp( -baseline * (ServiceHours / UniquePassengers) )
    """
    if unique_passengers == 0:
        return 0.0
    ratio = service_hours / unique_passengers
    return np.exp(-baseline * ratio)

def calculate_bus_efficiency_index(total_distance: float, unique_passengers: int) -> float:
    """
    Formula: exp( - (TotalDistance / UniquePassengers) )
    """
    dist_val = total_distance if total_distance > 0 else 1e9
    if unique_passengers == 0:
        return 0.0
    ratio = dist_val / unique_passengers
    return np.exp(-ratio)

def calculate_effective_dist_ratio(effective_distance: float, total_distance: float) -> float:
    """
    Formula: EffectiveDistance / TotalDistance
    """
    if total_distance == 0:
        return 0.0
    return effective_distance / total_distance


if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.performance_measurement.ridership import calculte_ridership
    path = load_config(r"config/config_path.yaml")
    
    bus_trip_path = path.data.interim.event.bus_trip
    person_path = path.data.interim.event.person_enter_bus
    
    # 1. EXTRACT DATA
    print("Extracting Metrics...")
    
    # Check sync (Basic check: files exist)
    if not os.path.exists(bus_trip_path) or not os.path.exists(person_path):
        print("Creating missing Arrow files first...")
        # (Optional: Trigger generation logic if needed, or just warn)
    
    bus_metrics = get_bus_service_metrics(bus_trip_path)
    unique_pax = get_unique_passenger_count(person_path)
    
    print(f"[*] Total Service Hours: {bus_metrics['service_hours']:.2f} h")
    print(f"[*] Revenue Hours:       {bus_metrics['revenue_hours']:.2f} h")
    print(f"[*] Total Distance:      {bus_metrics['total_km']:.2f} m")
    print(f"[*] Effective Distance:  {bus_metrics['effective_km']:.2f} m")
    print(f"[*] Unique Passengers:   {unique_pax}")
    
    # 2. CALCULATE INDICES
    baseline = 1.0 # Param
    
    prod_index = calculate_productivity_index(bus_metrics['service_hours'], unique_pax, baseline)
    eff_index = calculate_efficiency_index(bus_metrics['total_km'], unique_pax)
    dist_ratio = calculate_effective_dist_ratio(bus_metrics['effective_km'], bus_metrics['total_km'])
    
    print("-" * 30)
    print(f"KPI: Productivity Index: {prod_index:.6f}")
    print(f"KPI: Efficiency Index:   {eff_index:.6f}")
    print(f"KPI: Effective Dist Ratio: {dist_ratio:.4f}")

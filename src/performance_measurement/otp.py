import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.compute as pc
from src.events.bus_delay import generate_busDelayAtFacilities_df

def calculte_otp(bus_delay_path: str, max_delay: float, min_delay: float):
    with pa.OSFile(bus_delay_path, 'rb') as source:
        table = ipc.open_stream(source).read_all()
    
    delays = pc.cast(table['arrDelay'], pa.float64())
    mask = pc.and_(
        pc.less_equal(delays, max_delay),
        pc.greater_equal(delays, min_delay)
    )
    
    ontime = len(table.filter(mask))
    total = table.num_rows  
    if total > 0:
        otp_percent = (ontime / total) * 100.0
    else:
        otp_percent = 0.0

    return ontime, total, otp_percent


if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.transit.transit_vehicle import get_transit_type_dict
    path = load_config(r"config/config_path.yaml")
    veh_type_dict = get_transit_type_dict(path.paths.transit_vehicle)

    bus_delay_path = path.data.interim.event.bus_delay_at_facilities
    generate_busDelayAtFacilities_df(
        events_path=path.paths.events, 
        vehtype_dict=veh_type_dict, 
        bus_hint_str="bus", 
        output_arrow_path=bus_delay_path)

    ontime, total, otp_percent = calculte_otp(bus_delay_path=bus_delay_path, max_delay=3*60, min_delay=-3*60)
    print(f"On-time arrivals: {ontime} / {total}  --> OTP: {otp_percent:.2f} %")

    # python -m src.performance_measurement.otp
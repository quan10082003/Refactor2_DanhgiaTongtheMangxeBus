import os
import shutil
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
from matplotlib.path import Path
from matplotlib.path import Path
from lxml import etree
import pyarrow as pa
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from src.od_mask.core_class import Zone

def draw_od_heatmap(network_path: str, schedule_path: str, zones_list: list[Zone], people_trip_arrow_path: str, od_visualize_number: pd.DataFrame, save_image_path: str, scenario_name: str = "", grid_info="20x20"):
    """
    Draws a map showing the network, bus routes, zones, and top 25 OD flows.
    Arrows are colored and sized based on trip volume.
    """
    with pa.ipc.open_stream(people_trip_arrow_path) as reader:
        people_trip_df = reader.read_all().to_pandas()
        print(f"Loaded {len(people_trip_df)} records (IPC Stream).")
    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)
        
    print(f"Generating Top {od_visualize_number} OD Heatmap for {scenario_name}...")
    
    # 1. Parse Network
    tree = etree.parse(network_path)
    root = tree.getroot()
    nodes = {}
    for node in root.xpath('//network/nodes/node'):
        nodes[node.get('id')] = (float(node.get('x')), float(node.get('y')))
    links = {}
    for link in root.xpath('//network/links/link'):
        links[link.get('id')] = (link.get('from'), link.get('to'))

    # 2. Parse Bus Links
    bus_link_ids = set()
    if os.path.exists(schedule_path):
        try:
            tree_sched = etree.parse(schedule_path)
            root_sched = tree_sched.getroot()
            for route in root_sched.xpath('//transitRoute'):
                mode = route.find('transportMode')
                if mode is not None and mode.text.strip().lower() == 'bus':
                     r_path = route.find('route')
                     if r_path is not None:
                         for link_ref in r_path.xpath('link'):
                             bus_link_ids.add(link_ref.get('refId'))
        except Exception:
            pass # Suppress for now

    # 3. Data Prep
    valid_df = people_trip_df.copy()
    for col in ['xO', 'yO', 'xD', 'yD']:
        if col in valid_df.columns:
            valid_df[col] = pd.to_numeric(valid_df[col], errors='coerce')
    
    ranking_df = valid_df[(valid_df['OZone'] != 'undefined') & (valid_df['DZone'] != 'undefined')]
    top_od_counts = ranking_df.groupby(['OZone', 'DZone']).size().reset_index(name='count').sort_values('count', ascending=False).head(od_visualize_number)

    if top_od_counts.empty:
        print("No valid OD pairs found.")
        return

    # Normalize counts for visual mapping
    max_count = top_od_counts['count'].max()
    min_count = top_od_counts['count'].min()
    norm = mcolors.Normalize(vmin=min_count, vmax=max_count)
    cmap = plt.colormaps['plasma']

    # 4. Setup Plot
    fig, ax = plt.subplots(figsize=(24, 24), facecolor='black')
    ax.set_facecolor('black')
    ax.set_aspect('equal')

    # Z-Orders
    Z_BASE = 1
    Z_BUS = 2
    Z_ZONES = 3
    Z_ARROWS = 4
    Z_TEXT = 5

    # Layer 1: Background Network
    base_lines = []
    for l_id, (u, v) in links.items():
        if u in nodes and v in nodes:
            base_lines.append([nodes[u], nodes[v]])
    lc_base = LineCollection(base_lines, colors='#999999', linewidths=0.5, alpha=0.5, zorder=Z_BASE)
    ax.add_collection(lc_base)

    # Layer 2: Bus Network
    bus_lines_coords = []
    for l_id in bus_link_ids:
        if l_id in links:
            u, v = links[l_id]
            if u in nodes and v in nodes:
                bus_lines_coords.append([nodes[u], nodes[v]])
    if bus_lines_coords:
        lc_bus = LineCollection(bus_lines_coords, colors='#00FFFF', linewidths=1.2, alpha=0.8, zorder=Z_BUS)
        ax.add_collection(lc_bus)

    # Zone Map
    zone_map = {str(z.id): z for z in zones_list}
    unique_zones = set(top_od_counts['OZone'].astype(str)).union(set(top_od_counts['DZone'].astype(str)))
    
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    # Layer 3: Zones
    for z_id in unique_zones:
        zone = zone_map.get(z_id)
        if not zone: continue
        
        # Calculate bounds
        xs = [p.x for p in zone.boundary_points]
        ys = [p.y for p in zone.boundary_points]
        if xs and ys:
            min_x, max_x = min(min_x, min(xs)), max(max_x, max(xs))
            min_y, max_y = min(min_y, min(ys)), max(max_y, max(ys))
            
        poly = patches.Polygon([(p.x, p.y) for p in zone.boundary_points], closed=True, 
                               facecolor='#1a1a1a', edgecolor='#ffffff', alpha=0.3, linewidth=1.0, zorder=Z_ZONES)
        ax.add_patch(poly)
        
        # Centroid for label
        if xs:
            cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
            ax.text(cx, cy, z_id, color='white', fontsize=8, ha='center', va='center', alpha=0.7, zorder=Z_TEXT)

    # Layer 4: Arrows
    for idx, (i, row) in enumerate(top_od_counts.iterrows()):
        count = row['count']
        o_id, d_id = str(row['OZone']), str(row['DZone'])
        o_z, d_z = zone_map.get(o_id), zone_map.get(d_id)
        if not o_z or not d_z: continue
        
        color = cmap(norm(count))
        # Width scaling: min 2, max 10
        width_ratio = (count - min_count) / (max_count - min_count) if max_count > min_count else 1
        lw = 2 + (8 * width_ratio)
        
        ox = sum(p.x for p in o_z.boundary_points)/len(o_z.boundary_points)
        oy = sum(p.y for p in o_z.boundary_points)/len(o_z.boundary_points)
        dx = sum(p.x for p in d_z.boundary_points)/len(d_z.boundary_points)
        dy = sum(p.y for p in d_z.boundary_points)/len(d_z.boundary_points)
        
        if o_id == d_id:
             # Self loop
             z_xs = [p.x for p in o_z.boundary_points]
             z_width = max(z_xs) - min(z_xs)
             r = z_width * 0.4 
             theta = np.linspace(np.radians(0), np.radians(300), 50)
             arc_xs = ox + r * np.cos(theta)
             arc_ys = oy + r * np.sin(theta)
             verts = list(zip(arc_xs, arc_ys))
             p = Path(verts)
             arrow = patches.FancyArrowPatch(path=p, arrowstyle='-|>', color=color, lw=lw, mutation_scale=20+lw, zorder=Z_ARROWS, alpha=0.9)
             ax.add_patch(arrow)
        else:
            arrow = patches.FancyArrowPatch((ox, oy), (dx, dy), connectionstyle=f"arc3,rad=0.2", 
                                            arrowstyle='-|>', color=color, lw=lw, mutation_scale=20+lw, zorder=Z_ARROWS, alpha=0.9)
            ax.add_patch(arrow)

    if min_x != float('inf'):
        pad_x = (max_x - min_x) * 0.2
        pad_y = (max_y - min_y) * 0.2
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('Trip Count', color='white', size=14)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    ax.set_title(f"TOP {od_visualize_number} OD FLOW HEATMAP: {scenario_name}", fontsize=24, color='white', pad=20)
    ax.text(0.02, 0.98, f"Grid: {grid_info}\nLines: Base (Gray), Bus (Cyan)\nArrows: OD Flow (Width/Color = Volume)", transform=ax.transAxes, 
            color='white', fontsize=12, fontweight='bold', va='top', 
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))
    ax.axis('off')

    plt.savefig(save_image_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"Heatmap saved to: {save_image_path}")

if __name__ == "__main__":
    from src.utils.folder_creator import create_folders
    from src.data.load_config import load_config
    from src.network.network import generate_nodes_and_links_dict
    from src.network.core_class import get_boundary_nodes_of_network
    from src.plan.core_class import get_boundary_nodes_of_plans
    from src.plan.plan import generate_people_acts_coord_dict
    from src.od_mask.generator import ZoneGeneratorByGrid, Point
    from src.events.person_trip import generate_personTrip_df
    from src.transit.transit_vehicle import get_transit_type_dict

    # 0. Configuration
    path = load_config(r"config/config_path.yaml")

    #param
    scenario_name = path.scenario
    ROWS, COLS = 20, 20
    od_visualize_number = 25
    bus_route_hint_str = "bus"
    
    # Paths
    network_path = path.paths.network
    schedule_path = path.paths.transit_schedule
    plan_path = path.paths.plan
    events = path.paths.events
    vehicle = path.paths.transit_vehicle

    #output
    people_trip_arrow_path = path.data.interim.event.people_trip
    od_heatmap_image_path = path.data.interim.visualize.od_heatmap
    create_folders(od_heatmap_image_path, people_trip_arrow_path)
    
    
    # 2. Generate Zones (Replicate logic from src/events/person_trip.py)
    nodes_dict, links_dict = generate_nodes_and_links_dict(network_path)
    people = generate_people_acts_coord_dict(plan_path)

    min_p_network, max_p_network = get_boundary_nodes_of_network(nodes_dict)
    min_p_plan, max_p_plan = get_boundary_nodes_of_plans(people)
    
    min_p = Point(min(min_p_network.x, min_p_plan.x), min(min_p_network.y, min_p_plan.y))
    max_p = Point(max(max_p_network.x, max_p_plan.x), max(max_p_network.y, max_p_plan.y))
    
    zone_gen = ZoneGeneratorByGrid(max_p=max_p, min_p=min_p, rows=ROWS, cols=COLS)
    zones_list = zone_gen.generate()

    
    pt_type_dict = get_transit_type_dict(vehicle)
    generate_personTrip_df(
        events_path=events, 
        vehtype_dict=pt_type_dict, 
        zone_finder=zone_gen,
        bus_hint_str=bus_route_hint_str, 
        output_arrow_path=people_trip_arrow_path)


    draw_od_heatmap(
        network_path=network_path, 
        schedule_path=schedule_path, 
        zones_list=zones_list,
        od_visualize_number=od_visualize_number,
        people_trip_arrow_path=people_trip_arrow_path,
        save_image_path=od_heatmap_image_path, 
        scenario_name=scenario_name, 
        grid_info=f"{ROWS}x{COLS}")
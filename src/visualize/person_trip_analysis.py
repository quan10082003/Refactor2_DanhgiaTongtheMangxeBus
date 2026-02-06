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

def generate_final_report(data_df: pd.DataFrame, output_folder: str, scenario_name: str = "", filename: str = "00_global_summary.png", title_prefix: str = "BÁO CÁO TỔNG QUAN HỆ THỐNG"):
    """
    Generates a combined report with multiple charts (Pie, Bar, Boxplot, Hist, Line)
    analyzing mode share, travel times, etc.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    subset = data_df.copy() # Avoid SettingWithCopyWarning
    
    # --- C. PREPARE DATA FOR TIME ANALYSIS ---
    if 'startTime' in subset.columns:
        subset['startTime'] = pd.to_numeric(subset['startTime'], errors='coerce')
        subset['start_hour'] = subset['startTime'] / 3600
    else:
            subset['start_hour'] = 0 # Fallback

    if 'travelTime' in subset.columns:
        subset['travelTime'] = pd.to_numeric(subset['travelTime'], errors='coerce')

    # Mapping 'mainMode' or 'vehicleTypeList' to 'drawmode' for consistency with notebook logic
    # The Arrow file has 'mainMode'. Let's use that.
    # Note: Notebook uses 'drawmode'. We need to derive it if not present.
    # Logic from notebook/context implies 'drawmode' distinguishes car vs bus.
    # In person_trip.py, 'mainMode' is captured.
    # Let's assume 'mainMode' is relevant. Or 'vehicleTypeList'.
    # If 'drawmode' is not in columns, create it.
    if 'drawmode' not in subset.columns:
        # Simple heuristic: if 'bus' string in vehicleTypeList, maybe it's bus? 
        # But 'mainMode' from MATSim events (departure) is usually 'car', 'pt', 'walk'.
        # If 'pt', it involves bus.
        # Let's map 'mainMode' to 'drawmode'.
        subset['drawmode'] = subset['mainMode'] 

    # UPDATE: Change layout to 3x2 to include Time analysis (Item C)
    fig, axes = plt.subplots(3, 2, figsize=(18, 20)) 
    fig.suptitle(f"{title_prefix} {scenario_name}\n(Tổng cộng: {len(subset)} Trip)", fontsize=22, fontweight='bold', y=0.98)
    
    # 1. Tỷ lệ phương tiện
    mode_counts = subset['drawmode'].value_counts()
    axes[0, 0].pie(mode_counts, labels=mode_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    axes[0, 0].set_title("Tỷ lệ phương tiện", fontsize=16)
    
    # 2. Thời gian trung bình (Modified for Item A & B.1)
    avg_times = subset.groupby('drawmode')['travelTime'].mean().sort_values(ascending=False)
    
    # Fix Item A: Added hue and legend=False to silence warning
    # Ensure index is treated as categorical for hue if needed, but here simple usage works
    sns.barplot(x=avg_times.index, y=avg_times.values, ax=axes[0, 1], palette='viridis', hue=avg_times.index, legend=False)
    
    for i, mode in enumerate(avg_times.index):
        v = avg_times[mode]
        count = mode_counts.get(mode, 0) 
        # Item B.1: Add n=... to text
        axes[0, 1].text(i, v, f'{v:.1f}\n(n={count})', ha='center', va='bottom', fontweight='bold')
    axes[0, 1].set_title("Thời gian di chuyển trung bình (giây)", fontsize=16)
    
    # 3 & 4. Boxplots
    # We will try to plot generic boxplots for available modes instead of hardcoded 'bus'/'car'
    # But to match notebook layout (row 1 has 2 plots), let's see. 
    # Notebook creates axes[1,0] and axes[1,1] for specific modes.
    # Let's adapt to dynamic modes if possible, or stick to top 2 modes.
    top_modes = mode_counts.index[:2] if len(mode_counts) >= 2 else mode_counts.index
    
    for idx, (r, c) in enumerate([(1,0), (1,1)]):
        ax = axes[r, c]
        if idx < len(top_modes):
            mode_name = top_modes[idx]
            color = 'skyblue' if idx == 0 else 'salmon'
            
            m_data = subset[subset['drawmode'] == mode_name]['travelTime']
            if not m_data.empty:
                sns.boxplot(y=m_data, ax=ax, color=color, showfliers=False)
                q1, med, q3 = np.percentile(m_data, [25, 50, 75])
                ax.text(0, med, f'Med: {med:.1f}', ha='center', fontweight='bold', bbox=dict(facecolor='white', alpha=0.5))
                ax.text(0.1, q1, f'25%: {q1:.1f}', color='blue', fontweight='bold')
                ax.text(0.1, q3, f'75%: {q3:.1f}', color='red', fontweight='bold')
                ax.set_title(f"Phân vị: {str(mode_name).upper()} (N={len(m_data)})", fontsize=16)
            else:
                ax.text(0.5, 0.5, f"Không có dữ liệu {mode_name}", ha='center')
        else:
             ax.axis('off')

    # --- C. ITEM SUGGESTION: DEPARTURE TIME PLOTS ---
    # 5. Departure Time Distribution (Histogram)
    ax_hist = axes[2, 0]
    sns.histplot(data=subset, x='start_hour', hue='drawmode', kde=True, ax=ax_hist, element="step", common_norm=False)
    ax_hist.set_title("Phân bố giờ khởi hành (Departure Time)", fontsize=16)
    ax_hist.set_xlabel("Hour of Day")
    ax_hist.set_ylabel("Count")
    
    # 6. Average Travel Time by Hour (Line Plot)
    ax_line = axes[2, 1]
    if 'hour_int' not in subset.columns:
        subset['hour_int'] = subset['start_hour'].fillna(0).astype(int)
        
    # Group by hour and mode
    time_trend = subset.groupby(['hour_int', 'drawmode'])['travelTime'].mean().reset_index()
    if not time_trend.empty:
        sns.lineplot(data=time_trend, x='hour_int', y='travelTime', hue='drawmode', ax=ax_line, marker='o')
    ax_line.set_title("Biến động thời gian di chuyển theo giờ", fontsize=16)
    ax_line.set_xlabel("Hour of Day")
    ax_line.set_ylabel("Avg Travel Time (s)")
    ax_line.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_path = os.path.join(output_folder, filename)
    plt.savefig(save_path)
    plt.close()
    print(f"Final report saved to {save_path}")

def draw_all_zones_map(network_path: str, zones_list: list[Zone], output_folder: str, scenario_name: str, nodes: dict = None, links: dict = None):
    """
    Draws a map showing the network and all defined zones.
    """
    print(f"Generating All Zones Map for {scenario_name}...")
    
    # 1. Parse Network if not provided
    if nodes is None or links is None:
        print(f"Parsing network: {network_path}")
        tree = etree.parse(network_path)
        root = tree.getroot()
        nodes = {}
        for node in root.xpath('//network/nodes/node'):
            nodes[node.get('id')] = (float(node.get('x')), float(node.get('y')))
        links = {}
        for link in root.xpath('//network/links/link'):
            links[link.get('id')] = (link.get('from'), link.get('to'))

    # 4. Setup Plot
    fig, ax = plt.subplots(figsize=(24, 24), facecolor='black')
    ax.set_facecolor('black')
    ax.set_aspect('equal')

    # Z-Orders
    Z_BASE = 1
    Z_ZONES = 2
    Z_TEXT = 3



    # Layer 2: Zones
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for zone in zones_list:
        if not zone.boundary_points:
            continue
            
        # Draw Polygon
        poly = patches.Polygon([(p.x, p.y) for p in zone.boundary_points], closed=True, 
                               facecolor='#222222', edgecolor='gray', alpha=0.4, linewidth=1.5, zorder=Z_ZONES)
        ax.add_patch(poly)
        
        # Calculate bounds
        xs = [p.x for p in zone.boundary_points]
        ys = [p.y for p in zone.boundary_points]
        min_x, max_x = min(min_x, min(xs)), max(max_x, max(xs))
        min_y, max_y = min(min_y, min(ys)), max(max_y, max(ys))

        # Add Label
        centroid_x = sum(xs) / len(xs)
        centroid_y = sum(ys) / len(ys)
        ax.text(centroid_x, centroid_y, str(zone.id), color='white', fontsize=5, ha='center', va='top', zorder=Z_TEXT)

    # Layer 1: Background Network
    base_lines = []
    for l_id, (u, v) in links.items():
        if u in nodes and v in nodes:
            base_lines.append([nodes[u], nodes[v]])
    if base_lines:
        lc_base = LineCollection(base_lines, colors='#bd0000', linewidths=3, alpha=1, zorder=Z_BASE)
        ax.add_collection(lc_base)

    # Set Bounds
    if min_x != float('inf'):
        pad_x = (max_x - min_x) * 0.1
        pad_y = (max_y - min_y) * 0.1
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)

    ax.set_title(f"ALL ZONES MAP: {scenario_name}", fontsize=24, color='white', pad=20)
    ax.axis('off')

    save_path = os.path.join(output_folder, f"All_Zones_Map_{scenario_name}.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"All Zones Map saved to: {save_path}")


def draw_top_od_map(network_path: str, schedule_path: str, zones_list: list[Zone], data_df: pd.DataFrame, output_folder: str, top_n: int = 5, scenario_name: str = "", grid_info="20x20"):
    """
    Draws a map showing the network, bus routes, zones, and top N OD flows.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    print(f"Generating Top {top_n} OD Map for {scenario_name}...")
    
    # 1. Parse Network
    print(f"Parsing network: {network_path}")
    tree = etree.parse(network_path)
    root = tree.getroot()
    nodes = {}
    for node in root.xpath('//network/nodes/node'):
        nodes[node.get('id')] = (float(node.get('x')), float(node.get('y')))
    links = {}
    for link in root.xpath('//network/links/link'):
        links[link.get('id')] = (link.get('from'), link.get('to'))

    # --- Call draw_all_zones_map here ---
    draw_all_zones_map(network_path, zones_list, output_folder, scenario_name, nodes, links)


    # 2. Parse Bus Links
    bus_link_ids = set()
    if os.path.exists(schedule_path):
        print(f"Parsing schedule: {schedule_path}")
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
        except Exception as e:
            print(f"Error parsing schedule: {e}")
    print(f"Found {len(bus_link_ids)} unique bus links.")

    # 3. Data Prep
    valid_df = data_df.copy()
    for col in ['xO', 'yO', 'xD', 'yD']:
        if col in valid_df.columns:
            valid_df[col] = pd.to_numeric(valid_df[col], errors='coerce')
    
    # Ensure rows with valid coords
    plot_df = valid_df.dropna(subset=['xO', 'yO', 'xD', 'yD'])
    
    # Group OD
    ranking_df = valid_df[(valid_df['OZone'] != 'undefined') & (valid_df['DZone'] != 'undefined')]
    top_od_counts = ranking_df.groupby(['OZone', 'DZone']).size().reset_index(name='count').sort_values('count', ascending=False).head(top_n)

    if top_od_counts.empty:
        print("No valid OD pairs found.")
        return

    # 4. Setup Plot
    fig, ax = plt.subplots(figsize=(24, 24), facecolor='black')
    ax.set_facecolor('black')
    ax.set_aspect('equal')

    # Z-Orders
    Z_BASE = 1
    Z_POINTS = 2
    Z_BUS = 3
    Z_ZONES = 4
    Z_ARROWS = 5

    # Layer 1: Background Network
    base_lines = []
    for l_id, (u, v) in links.items():
        if u in nodes and v in nodes:
            base_lines.append([nodes[u], nodes[v]])
    lc_base = LineCollection(base_lines, colors='#cccccc', linewidths=0.5, alpha=0.3, zorder=Z_BASE)
    ax.add_collection(lc_base)

    # Layer 2: Trip Points (Refined Colors)
    # Origin: Light Blue (#4ec6ed)
    # Destination: Medium Pink (#f03793)
    ax.scatter(plot_df['xO'], plot_df['yO'], c='#4ec6ed', s=10, alpha=0.6, label='Origins', edgecolors='none', zorder=Z_POINTS)
    ax.scatter(plot_df['xD'], plot_df['yD'], c='#f03793', s=10, alpha=0.6, label='Destinations', edgecolors='none', zorder=Z_POINTS)

    # Layer 3: Bus Network (Red/Yellow)
    bus_lines_coords = []
    for l_id in bus_link_ids:
        if l_id in links:
            u, v = links[l_id]
            if u in nodes and v in nodes:
                bus_lines_coords.append([nodes[u], nodes[v]])
    if bus_lines_coords:
        lc_bus = LineCollection(bus_lines_coords, colors='#f2f218', linewidths=2.5, alpha=1, zorder=Z_BUS)
        ax.add_collection(lc_bus)

    # Bounds
    rank_colors = ['#FF3333', '#FF9933', '#FFFF33', '#33FF33', '#33FFFF']
    
    # Map zone objects by ID
    zone_map = {str(z.id): z for z in zones_list}
    unique_zones = set(top_od_counts['OZone'].astype(str)).union(set(top_od_counts['DZone'].astype(str)))
    
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    # Calculate bounds of relevant zones
    for z_id in unique_zones:
        zone = zone_map.get(z_id)
        if zone:
            xs = [p.x for p in zone.boundary_points]
            ys = [p.y for p in zone.boundary_points]
            if xs and ys:
                min_x, max_x = min(min_x, min(xs)), max(max_x, max(xs))
                min_y, max_y = min(min_y, min(ys)), max(max_y, max(ys))

    # Layer 4: Zones
    for z_id in unique_zones:
        zone = zone_map.get(z_id)
        if not zone: continue
        
        poly = patches.Polygon([(p.x, p.y) for p in zone.boundary_points], closed=True, 
                               facecolor='#222222', edgecolor='white', alpha=0.6, linewidth=2.0, zorder=Z_ZONES)
        ax.add_patch(poly)
        
        xs = [p.x for p in zone.boundary_points]
        ys = [p.y for p in zone.boundary_points]
        if xs and ys:
            ax.text(min(xs)+50, max(ys)-50, z_id, color='white', fontsize=11, fontweight='bold', ha='left', va='top', zorder=Z_ZONES+0.1)

    # Layer 5: Arrows
    cell_text = []
    table_colors = []
    
    for idx, (i, row) in enumerate(top_od_counts.iterrows()):
        color = rank_colors[idx % 5]
        o_id, d_id = str(row['OZone']), str(row['DZone'])
        
        o_z, d_z = zone_map.get(o_id), zone_map.get(d_id)
        if not o_z or not d_z: continue
        
        # Centroid
        ox = sum(p.x for p in o_z.boundary_points)/len(o_z.boundary_points)
        oy = sum(p.y for p in o_z.boundary_points)/len(o_z.boundary_points)
        dx = sum(p.x for p in d_z.boundary_points)/len(d_z.boundary_points)
        dy = sum(p.y for p in d_z.boundary_points)/len(d_z.boundary_points)
        
        if o_id == d_id:
            z_xs = [p.x for p in o_z.boundary_points]
            z_width = max(z_xs) - min(z_xs)
            r = z_width * 0.25 
            theta = np.linspace(np.radians(30), np.radians(330), 50)
            arc_xs = ox + r * np.cos(theta)
            arc_ys = oy + r * np.sin(theta)
            verts = list(zip(arc_xs, arc_ys))
            p = Path(verts)
            arrow = patches.FancyArrowPatch(path=p, arrowstyle='-|>', color=color, lw=3, mutation_scale=20, zorder=Z_ARROWS)
            ax.add_patch(arrow)
        else:
            rad = 0.2 + (0.05 * idx)
            arrow = patches.FancyArrowPatch((ox, oy), (dx, dy), connectionstyle=f"arc3,rad={rad}", 
                                            arrowstyle='-|>', color=color, lw=3, mutation_scale=25, zorder=Z_ARROWS)
            ax.add_patch(arrow)
        
        cell_text.append([o_id, d_id, str(row['count'])])
        table_colors.append([color, color, '#333333'])

    if min_x != float('inf'):
        pad_x = (max_x - min_x) * 0.2
        pad_y = (max_y - min_y) * 0.2
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)
        
    ax.set_title(f"TOP {top_n} OD FLOW: {scenario_name}", fontsize=24, color='white', pad=20)
    ax.text(0.02, 0.98, f"Grid: {grid_info}\nYellow: Bus Routes\nPoints: O=Light Blue, D=Medium Pink", transform=ax.transAxes, 
            color='white', fontsize=12, fontweight='bold', va='top', 
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))
    ax.axis('off')

    if cell_text:
        the_table = ax.table(cellText=cell_text,
                             colLabels=["Origin", "Destination", "Trips"],
                             cellColours=table_colors,
                             cellLoc='center',
                             loc='upper right',
                             bbox=[0.74, 0.87, 0.25, 0.13],
                             zorder=10) 
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(9)
        for (r, c), cell in the_table.get_celld().items():
             cell.set_edgecolor('white')
             cell.set_linewidth(0.5)
             if r == 0:
                 cell.set_facecolor('#dddddd')
                 cell.set_text_props(weight='bold', color='black')
             else:
                 if c < 2:
                     cell.set_text_props(weight='bold', color='black')
                 else:
                     cell.set_text_props(color='white')

    save_path = os.path.join(output_folder, f"Top{top_n}_OD_Vis_{scenario_name}.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"Map saved to: {save_path}")




def analyze_person_trips(people_trip_arrow_path: str, network_path: str, schedule_path: str, zones_list: list[Zone], output_folder: str, top_od_number: int = 5, scenario_name: str = "", grid_info="20x20"):
    """
    Main function to analyze person trips, generating global reports, top OD reports, and top N OD map.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"--- STARTING PERSON TRIP ANALYSIS for {scenario_name} ---")

    # 1. Load Data
    print(f"Loading data from {people_trip_arrow_path}...")
    try:
        with pa.ipc.open_stream(people_trip_arrow_path) as reader:
            df = reader.read_all().to_pandas()
        print(f"Loaded {len(df)} records (IPC Stream).")
    except Exception as e_stream:
        print(f"IPC Stream read failed: {e_stream}")
        try:
            df = pd.read_feather(people_trip_arrow_path)
            print(f"Loaded {len(df)} records (Feather/IPC File).")
        except Exception as e_feather:
            print(f"Error loading Arrow file: {e_feather}")
            return # or raise

    # 2. Generate Global Report
    print("Generating Global Report...")
    generate_final_report(df, output_folder, scenario_name=scenario_name)

    # 3. Generate Top 10 OD Reports
    print("Generating Top 10 OD Reports...")
    valid_od = df[(df['OZone'] != 'undefined') & (df['DZone'] != 'undefined')]
    od_counts = valid_od.groupby(['OZone', 'DZone']).size().reset_index(name='n').sort_values('n', ascending=False)
    
    for i, (_, row) in enumerate(od_counts.head(top_od_number).iterrows(), 1):
        o, d = row['OZone'], row['DZone']
        od_subset = valid_od[(valid_od['OZone'] == o) & (valid_od['DZone'] == d)]
        
        report_filename = f"top_{i}_OD_{o}_{d}_{scenario_name}.png"
        title = f"TOP {i} OD: {o} -> {d}"
        print(f"  Generating report for Top {i}: {o} -> {d} ...")
        
        generate_final_report(
            od_subset, 
            output_folder, 
            scenario_name=scenario_name, 
            filename=report_filename,
            title_prefix=title
        )

    # 4. Generate Top OD Map
    draw_top_od_map(network_path, schedule_path, zones_list, df, output_folder, top_n=top_od_number, scenario_name=scenario_name, grid_info=grid_info)
    
    print("--- PERSON TRIP ANALYSIS DONE ---")


if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.network.network import generate_nodes_and_links_dict
    from src.network.core_class import get_boundary_nodes_of_network
    from src.plan.core_class import get_boundary_nodes_of_plans
    from src.plan.plan import generate_people_acts_coord_dict
    from src.od_mask.generator import ZoneGeneratorByGrid, Point

    # 0. Configuration
    path = load_config(r"config/config_path.yaml")
    
    # Paths
    people_trip_arrow_path = path.data.interim.event.people_trip 
    network_path = path.paths.network
    schedule_path = path.paths.transit_schedule
    plan_path = path.paths.plan
    
    scenario_name = "BASELINE"
    output_visualize_folder = r"data/visualize/baseline/person_trip_analysis"
    
    # Generate Zones Locally for testing
    print("Generating Zones...")
    nodes_dict, links_dict = generate_nodes_and_links_dict(network_path)
    min_p_network, max_p_network = get_boundary_nodes_of_network(nodes_dict)
    
    people = generate_people_acts_coord_dict(plan_path)
    min_p_plan, max_p_plan = get_boundary_nodes_of_plans(people)
    
    min_p = Point(min(min_p_network.x, min_p_plan.x), min(min_p_network.y, min_p_plan.y))
    max_p = Point(max(max_p_network.x, max_p_plan.x), max(max_p_network.y, max_p_plan.y))

    ROWS, COLS = 20, 20
    zone_gen = ZoneGeneratorByGrid(max_p=max_p, min_p=min_p, rows=ROWS, cols=COLS)
    zones_list = zone_gen.generate()

    analyze_person_trips(
        people_trip_arrow_path=people_trip_arrow_path,
        network_path=network_path,
        schedule_path=schedule_path,
        zones_list=zones_list,
        output_folder=output_visualize_folder,
        scenario_name=scenario_name,
        grid_info=f"{ROWS}x{COLS}"
    )
    #python -m src.visualize.person_trip_analysis
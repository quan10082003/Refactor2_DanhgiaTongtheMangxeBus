import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import colors as mcolors
from matplotlib import cm
from lxml import etree
import os
import numpy as np
from collections import Counter
from src.transit.core_class import TransitRoute

def get_offset_coords(p1, p2, offset):
    """Shift line p1-p2 to the right by offset amount"""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx*dx + dy*dy)
    if length == 0:
        return p1, p2
    
    # Normalized perpendicular vector (right hand side)
    nx = dy / length
    ny = -dx / length
    
    # Apply offset
    ox = nx * offset
    oy = ny * offset
    
    return [(x1 + ox, y1 + oy), (x2 + ox, y2 + oy)]

def map_bus_network_advanced(output_image_path: str, network_path: str, bus_route_data: list[TransitRoute]):
    print("Starting Visualization V4 (Full Network Base Layer)...\n")
    

    print(f"Parsing network data from {network_path}...")
    network_tree = etree.parse(network_path)
    network_root = network_tree.getroot()
    
    nodes_xy = {}
    for node in network_root.xpath("//network/nodes/node"):
        nodes_xy[node.get('id')] = (float(node.get('x')), float(node.get('y')))
        
    all_links_geom = {}
    for link in network_root.xpath("//network/links/link"):
        lid = link.get('id')
        fid = link.get('from')
        tid = link.get('to')
        if fid in nodes_xy and tid in nodes_xy:
            all_links_geom[lid] = [nodes_xy[fid], nodes_xy[tid]]
    print(f"Loaded {len(all_links_geom)} links from network.")


    # 2. Count Bus Link Frequency
    bus_link_counts = Counter()

    for route in bus_route_data:
        link_list = route.links_id
        bus_link_counts.update(link_list)
    
    # 3. Prepare Plot Layers
    base_lines = []
    bus_lines = []
    bus_widths = []
    bus_colors = []
    
    focus_x = []
    focus_y = []
    
    # -- Configuration --
    # Offset scaling
    offset_base_meters = 12.0 # Minimum separation for base traffic
    # Bus width logic
    def get_width(freq):
        return 1.8 + (np.log(freq + 1) * 3) # Width scaling
    
    offset_multiplier = 2.0 
    cmap = plt.get_cmap('turbo')
    max_freq = max(bus_link_counts.values()) if bus_link_counts else 1
    norm = plt.Normalize(0, max_freq)

    # 3a. Process Base Links (ALL LINKS)
    # User request: "vẽ các link của cả bản đồ mạng lưới... ở giữu background với lớp vẽ bus"
    print("Processing Base Network Layout...")
    for lid, coords in all_links_geom.items():
        p1, p2 = coords
        # Apply small offset to base links too so bidirectional roads don't look like one line
        # and to ensure they sit 'under' the bus lanes correctly if aligned
        p_new = get_offset_coords(p1, p2, 5.0) 
        base_lines.append(p_new)

    # 3b. Process Bus Links
    sorted_bus_links = sorted(bus_link_counts.items(), key=lambda x: x[1])
    print(f"Processing {len(sorted_bus_links)} Bus Segments...")
    
    for lid, freq in sorted_bus_links:
        if lid in all_links_geom:
            p1, p2 = all_links_geom[lid]
            
            width = get_width(freq)
            # Offset further out to not overlap the base link or opposing bus link
            current_offset = offset_base_meters + (width * offset_multiplier)
            
            p_new = get_offset_coords(p1, p2, current_offset)
            
            bus_lines.append(p_new)
            bus_widths.append(width)
            bus_colors.append(cmap(norm(freq)))
            
            focus_x.extend([p1[0], p2[0]])
            focus_y.extend([p1[1], p2[1]])

    # 4. Plotting
    print("Generating plot...")
    fig, ax = plt.subplots(figsize=(24, 24))
    
    # Background
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    # Layer 1: Base Network (Gray-White)
    # "màu xám trắng" -> #EEEEEE or #DDDDDD
    lc_base = LineCollection(base_lines, colors='#DDDDDD', linewidths=0.5, alpha=0.4)
    ax.add_collection(lc_base)
    
    # Layer 2: Bus Network
    lc_bus = LineCollection(bus_lines, colors=bus_colors, linewidths=bus_widths, alpha=0.9)
    ax.add_collection(lc_bus)
    
    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('Bus Trips Frequency', color='white', fontsize=14)
    cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    # Focus Focus
    if focus_x and focus_y:
        min_x, max_x = min(focus_x), max(focus_x)
        min_y, max_y = min(focus_y), max(focus_y)
        margin = 1000.0
        ax.set_xlim(min_x - margin, max_x + margin)
        ax.set_ylim(min_y - margin, max_y + margin)
        print(f"Focused on active area: [{min_x}, {max_x}] x [{min_y}, {max_y}]")
    else:
        ax.autoscale()
        
    ax.axis('off')
    title_text = f"Bus Network Map ({network_path}) - Full Network Context"
    plt.title(title_text, color='white', fontsize=20)


    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor='black')
    print(f"Saved to {output_image_path}")
    plt.show()


if __name__ == "__main__":
    from src.data.load_config import load_config
    from src.network.network import generate_nodes_and_links_dict
    from src.network.core_class import get_boundary_nodes_of_network
    from src.transit.transit_schedule import generate_bus_routes_and_stops_dict
    from src.transit.core_class import TransitRoute
    
    path = load_config(r"config/config_path.yaml")
    
    network = path.paths.network

    schedule = path.paths.transit_schedule
    bus_routes_dict, _ = generate_bus_routes_and_stops_dict(transit_schedule_path=schedule, bus_route_hint_str="bus")
    map_bus_network_advanced(output_image_path="test.png", network_path=network, bus_route_data=bus_routes_dict)

    #python -m src.visualize.bus_tempature_map

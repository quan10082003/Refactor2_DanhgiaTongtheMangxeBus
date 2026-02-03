from src.transit.transit_vehicle import get_transit_type_dict
from src.domain.point import Point
from src.network.core_class import Node, Link

import lxml
import lxml.etree as etree

def generate_nodes_and_links_dict(network_path: str) -> (dict[str,Node], dict[str,Link]):
    nodes_dict: dict(str,Node) = {}
    links_dict: dict(str,Link) = {}

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(network_path, parser)
    root = tree.getroot()

    for link in root.xpath("//network/links/link"):
        link_id = link.xpath("@id")[0]
        length = link.xpath("@length")[0]
        from_node = link.xpath("@from")[0]
        to_node = link.xpath("@to")[0]
        links_dict[link_id] = Link(link_id, from_node, to_node, length)

    for node in root.xpath("//network/nodes/node"):
        node_id = node.xpath("@id")[0]
        x = node.xpath("@x")[0]
        y = node.xpath("@y")[0]
        nodes_dict[node_id] = Node(node_id, Point(x,y))
    
    return nodes_dict, links_dict

if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    network_path = path.paths.network
    nodes_dict, links_dict = generate_nodes_and_links_dict(network_path)

    print("--- ĐANG BẮT ĐẦU ĐỌC NETWORK ---")
    try:
        nodes, links = generate_nodes_and_links_dict(network_path)
        
        # 1. Kiểm tra số lượng
        print(f"[*] Tổng số Node: {len(nodes)}")
        print(f"[*] Tổng số Link: {len(links)}")
        print("-" * 30)

        # 2. Kiểm tra dữ liệu Node đầu tiên
        if nodes:
            first_node_id = next(iter(nodes))
            print(f"[Node Test] ID: {first_node_id}")
            print(f"   Tọa độ: ({nodes[first_node_id].coord.x}, {nodes[first_node_id].coord.y})")

        # 3. Kiểm tra dữ liệu Link đầu tiên và tính kết nối
        if links:
            first_link_id = next(iter(links))
            sample_link = links[first_link_id]
            print(f"[Link Test] ID: {sample_link.id}")
            print(f"   Từ Node: {sample_link.from_node} -> Đến Node: {sample_link.to_node}")
            print(f"   Chiều dài: {sample_link.length} m")
            
            # Kiểm tra xem Node của Link này có tồn tại trong nodes_dict không
            if sample_link.from_node in nodes:
                print(f"   => Xác nhận: Node gốc '{sample_link.from_node}' tồn tại trong danh sách.")

    except Exception as e:
        print(f"[LỖI] Có vấn đề khi chạy: {e}")

    # python -m src.network.network
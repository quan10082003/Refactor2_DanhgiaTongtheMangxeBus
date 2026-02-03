from lxml import etree

def get_transit_type_dict(transit_vehicle_path: str) -> dict[str,str]:
    tree = etree.parse(transit_vehicle_path)
    root = tree.getroot()
    ns = {'m': 'http://www.matsim.org/files/dtd'}

    pt_type_dict = {}
    for node in root.xpath("//m:vehicleDefinitions/m:vehicle", namespaces=ns):
        id = node.xpath("@id")[0]
        type = node.xpath("@type")[0]
        pt_type_dict[id] = type
    
    return pt_type_dict

if __name__ == "__main__":
    from src.data.load_config import load_config
    path = load_config(r"config/config_path.yaml")
    pt_type_dict = get_transit_type_dict(path.paths.transit_vehicle)
    print(pt_type_dict)
    #python -m src.transit.transit_vehicle
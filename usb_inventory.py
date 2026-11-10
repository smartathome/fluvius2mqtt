import os

# Global counters for the summary report
stats = {"available_slots": 0, "occupied_slots": 0, "ethernet_found": False}

def get_sys_attr(path, attr):
    try:
        with open(os.path.join(path, attr), 'r') as f:
            return f.read().strip()
    except:
        return None

def find_extra_info(path):
    tty_nodes = []
    is_ethernet = False
    try:
        for entry in os.scandir(path):
            if entry.is_dir() and ':' in entry.name:
                for root, dirs, files in os.walk(entry.path):
                    for d in dirs:
                        if d.startswith('ttyUSB') or d.startswith('ttyACM'):
                            tty_nodes.append(f"/dev/{d}")
                if os.path.exists(os.path.join(entry.path, 'net')):
                    is_ethernet = True
                    stats["ethernet_found"] = True
    except:
        pass
    
    tty_str = f" ➜ \033[92m{', '.join(sorted(list(set(tty_nodes))))}\033[0m" if tty_nodes else ""
    eth_str = " ➜ \033[94m[ETHERNET ADAPTER]\033[0m" if is_ethernet else ""
    return tty_str + eth_str

def print_usb_tree(base_path, sys_name, indent="", is_last=True):
    path = os.path.join(base_path, sys_name)
    vendor = get_sys_attr(path, 'manufacturer') or ""
    product = get_sys_attr(path, 'product') or ""
    speed = get_sys_attr(path, 'speed') or "?"
    max_ports = int(get_sys_attr(path, 'maxchild') or 0)
    extra_info = find_extra_info(path)

    port_label = ""
    if '-' in sys_name:
        port_num = sys_name.split('.')[-1].split('-')[-1]
        port_label = f"[Port {port_num}]: "

    # Check if this is a leaf device (not a hub)
    if max_ports == 0:
        stats["occupied_slots"] += 1

    marker = "└─" if is_last else "├─"
    desc = f"{vendor} {product}".strip() or "USB Hub"
    print(f"{indent}{marker} {port_label}{desc} ({sys_name}, {speed}M){extra_info}")

    new_indent = indent + ("    " if is_last else "│   ")
    for port in range(1, max_ports + 1):
        if '-' not in sys_name:
            child_name = f"{sys_name[3:]}-{port}"
        else:
            child_name = f"{sys_name}.{port}"

        child_path = os.path.join(base_path, child_name)
        is_last_port = (port == max_ports)
        
        if os.path.exists(child_path):
            print_usb_tree(base_path, child_name, new_indent, is_last_port)
        else:
            stats["available_slots"] += 1
            p_marker = "└─" if is_last_port else "├─"
            print(f"{new_indent}{p_marker} [Port {port}]: \033[90mEMPTY\033[0m")

def main():
    base = "/sys/bus/usb/devices/"
    root_hubs = sorted([d for d in os.listdir(base) if d.startswith('usb') and d[3:].isdigit()])
    
    print(f"\n\033[1m{'USB Topology & Hardware Mapping':<50}\033[0m")
    print("=" * 75)
    
    for hub in root_hubs:
        print_usb_tree(base, hub, is_last=True)
    
    # New logic: Total end-points = empty ports + occupied non-hub devices
    total_endpoints = stats["available_slots"] + stats["occupied_slots"]
    
    print("=" * 75)
    print(f"\033[1mSUMMARY (End-user ports):\033[0m")
    print(f"  • Total usable ports:             {total_endpoints}")
    print(f"  • Occupied by devices:            {stats['occupied_slots']}")
    print(f"  • Available / Free:               \033[1m{stats['available_slots']}\033[0m")
    if stats["ethernet_found"]:
        print(f"  • USB Ethernet Adapter:           \033[34mDetected (Occupies 1 port)\033[0m")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()


import re
import subprocess
from collections import defaultdict

# Constants
MIN_HEADER_LINES = 2
MIN_PARTS_COUNT = 3


def get_sinfo():
    result = subprocess.run(  # noqa: S603
        ["sinfo", "-lNe"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = result.stdout
    lines = stdout.strip().split("\n")
    # Drop the headers before returning the lines
    if len(lines) <= MIN_HEADER_LINES:
        return []
    return lines[MIN_HEADER_LINES:]


def parse_sinfo(sinfo_lines, node_parser):
    node_info = defaultdict(lambda: {"nodes": set(), "partitions": set()})
    partition_info = defaultdict(set)
    # Regex to extract node type (letters) and id (numbers)
    for line in sinfo_lines:
        parts = line.strip().split()
        # aggregate gpu node info only
        if len(parts) < MIN_PARTS_COUNT or "nvidia" not in parts[-2]:
            continue
        node_list = parts[0]
        partition = parts[2]
        type_parsed = node_parser.match(node_list)
        if type_parsed:
            node_type = type_parsed.group(1)
            node_info[node_type]["nodes"].add(node_list)
            node_info[node_type]["partitions"].add(partition)
        partition_info[partition].add(node_list)
    return node_info, partition_info


def print_idle_gpu_by_node_type(node_info):
    print("Idle GPU Node Information (Grouped by Node Type):")
    if not node_info:
        print(
            "  No idle GPU nodes with 'nvidia' found or no nodes "
            "matched the type pattern."
        )
    else:
        for node_type, info in sorted(node_info.items()):
            node_count = len(info["nodes"])
            partitions_list = sorted(info["partitions"])
            partitions_str = ", ".join(partitions_list) if partitions_list else "N/A"
            print(
                f"  {node_type}: {node_count} unique node(s) "
                f"(Associated Partitions: {partitions_str})"
            )


def print_idle_gpu_by_partition_type(partition_info, node_parser):
    print("\nIdle GPU Node Information (Grouped by Partition):")
    if not partition_info:
        print("  No idle GPU nodes with 'nvidia' found to group by partition.")
    else:
        for partition_name, nodes_in_partition_set in sorted(partition_info.items()):
            # Count of unique nodes in this partition
            node_count = len(nodes_in_partition_set)

            # Extract unique node types from the node names in this partition
            node_types_in_this_partition = set()
            for node_name in nodes_in_partition_set:
                match_node_type = node_parser.match(node_name)
                if match_node_type:
                    node_types_in_this_partition.add(match_node_type.group(1))

            node_types_str = (
                ", ".join(sorted(node_types_in_this_partition))
                if node_types_in_this_partition
                else "N/A"
            )
            print(
                f"  {partition_name}: {node_count} unique node(s) "
                f"(Node Types: {node_types_str})"
            )


def get_idle_gpu_node_info():
    sinfo_lines = get_sinfo()
    if len(sinfo_lines) == 0:
        print("No data found from sinfo command after headers.")
        return
    node_parser = re.compile(r"^([a-zA-Z]+)(\d+)$")
    node_info, partition_info = parse_sinfo(sinfo_lines, node_parser)
    print_idle_gpu_by_node_type(node_info)
    print_idle_gpu_by_partition_type(partition_info, node_parser)


if __name__ == "__main__":
    get_idle_gpu_node_info()

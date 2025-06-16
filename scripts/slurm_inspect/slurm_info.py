import re
import subprocess


def see_qos():
    """Show available QOS rules using sacctmgr command."""
    cmd = ["sacctmgr", "show", "qos", "format=Name,MaxTRESPU"]
    print(f">> Show what QOS Rules Exist: '{' '.join(cmd)}'")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Stderr: {e.stderr}")
    print("-" * 30)


def see_jobs_in_qos(qos_name):
    """Show jobs associated with a specific QOS.

    Args:
        qos_name (str): Name of the QOS to filter jobs by.
    """
    # Validate QOS name to prevent command injection
    if not re.match(r"^[a-zA-Z0-9_-]+$", qos_name):
        print(
            f"Invalid QOS name: {qos_name}. "
            f"Only alphanumeric, underscore, and dash allowed."
        )
        return

    cmd = ["squeue", "-o", "%.8i %.8u %.15P %.15q %T"]
    print(f">> See jobs associated with QOS: '{' '.join(cmd)}'")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        stdout_lines = [line for line in result.stdout.split("\n") if qos_name in line]
        print("\n".join(stdout_lines))
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Stderr: {e.stderr}")
    print("-" * 30)


def see_partition_info(partition):
    """Show information about a specific partition.

    Args:
        partition (str): Name of the partition to show information for.
    """
    # Validate partition name to prevent command injection
    if not re.match(r"^[a-zA-Z0-9_-]+$", partition):
        print(
            f"Invalid partition name: {partition}. "
            f"Only alphanumeric, underscore, and dash allowed."
        )
        return

    cmd = ["scontrol", "show", "partition", partition]
    print(f">> See Partition Info: '{' '.join(cmd)}'")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Stderr: {e.stderr}")
    print("-" * 30)


if __name__ == "__main__":
    see_qos()
    see_jobs_in_qos("gpu48")
    see_partition_info("mi250")

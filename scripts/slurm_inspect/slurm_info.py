import subprocess


def see_qos():
    cmd = ["sacctmgr", "show", "qos", "format=Name,MaxTRESPU"]
    print(f">> Show what QOS Rules Exist: '{' '.join(cmd)}'")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    print(stdout)
    print("-"*30)

def see_jobs_in_qos(qos_name):
    cmd = ["squeue", '-o "%.8i %.8u %.15P %.15q %T"']
    print(f">> See jobs associated with QOS: '{' '.join(cmd)}'")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    stdout_lines = [l for l in stdout.split("\n") if qos_name in l]
    print("\n".join(stdout_lines))
    print("-"*30)

def see_partition_info(partition):
    cmd = ["scontrol", "show", "partition", partition]
    print(f">> See Partiiton Info: '{' '.join(cmd)}'")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    print(stdout)
    print("-"*30)

if __name__ == "__main__":
    see_qos()
    see_jobs_in_qos("gpu48")
    see_partition_info("mi250")

import os
import subprocess
import re
import time
import sys

# Try to import matplotlib, if not available, we will just save CSV
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("matplotlib not found. Graphs will not be generated, only CSV data.")
    MATPLOTLIB_AVAILABLE = False

# Import generator
# We need to add the current directory to sys.path to import generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from generator import generar_textos_español
except ImportError:
    # Fallback if generator.py is not importable for some reason
    print("Could not import generator.py. Make sure it is in the same directory.")
    sys.exit(1)

# Configuration
TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
ABS_TARGET_DIR = os.path.abspath(TARGET_DIR)

# Docker Images
MPI_IMAGE = "augustosalazar/slim-mpi"
DASK_IMAGE = "daskdev/dask:latest"

def clean_txt_files():
    print("Cleaning old .txt files...")
    for f in os.listdir(TARGET_DIR):
        if f.endswith(".txt") and f.startswith("file_"):
            try:
                os.remove(os.path.join(TARGET_DIR, f))
            except Exception as e:
                print(f"Error deleting {f}: {e}")

def run_command(cmd, cwd=None):
    # print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Stderr: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        print(f"Exception running command: {e}")
        return None

def parse_time(output, type_):
    if not output: return None
    if type_ == "seq":
        match = re.search(r"Tiempo de ejecuci.n: (\d+\.\d+) segundos", output)
    elif type_ == "mpi":
        # Match "Tiempo de <anything>: <number> segundos" to handle encoding issues
        match = re.search(r"Tiempo de .*?: (\d+\.\d+) segundos", output)
    elif type_ == "dask":
        match = re.search(r"Tiempo total \(aprox\): (\d+\.\d+) s", output)
    
    if match:
        return float(match.group(1))
    else:
        # Debug: print output if regex fails
        # print(f"Regex failed for {type_}. Output snippet: {output[:200]}...")
        pass
    return None

def run_benchmark():
    results = [] # List of dicts: {files, procs, seq, mpi, dask}

    file_counts = [10, 50, 100, 200, 500, 1000]
    proc_counts = [2, 3, 4, 5]
    
    print("Starting Full Factorial Benchmark")

    for count in file_counts:
        print(f"\n=== Testing with {count} files ===")
        clean_txt_files()
        
        print(f"Generating {count} files...")
        generar_textos_español(num_files=count, min_words=50000, max_words=60000) 
        
        # 1. Sequential (Run once per file count)
        print("Running Sequential...")
        cmd_seq = f"python wordFreq.py"
        out_seq = run_command(cmd_seq, cwd=TARGET_DIR)
        t_seq = parse_time(out_seq, "seq")
        if t_seq is None: t_seq = 0.0
        print(f"Sequential Time: {t_seq:.3f}s")

        for p in proc_counts:
            print(f"\n--- Procs/Workers: {p} ---")
            
            # 2. MPI
            print(f"Running MPI (n={p})...")
            cmd_mpi = f'docker run --rm -v "{ABS_TARGET_DIR}:/app" {MPI_IMAGE} mpiexec --allow-run-as-root --oversubscribe -n {p} python /app/wordFreqMPI.py'
            out_mpi = run_command(cmd_mpi)
            t_mpi = parse_time(out_mpi, "mpi")
            if t_mpi is None: t_mpi = 0.0
            print(f"MPI Time: {t_mpi:.3f}s")

            # 3. Dask
            print(f"Running Dask (w={p})...")
            cmd_dask = f'docker run --rm -v "{ABS_TARGET_DIR}:/app" --network host {DASK_IMAGE} python /app/wordFreqDask.py {p}'
            out_dask = run_command(cmd_dask)
            t_dask = parse_time(out_dask, "dask")
            if t_dask is None: t_dask = 0.0
            print(f"Dask Time: {t_dask:.3f}s")

            results.append({
                "Files": count,
                "Procs": p,
                "Sequential": t_seq,
                "MPI": t_mpi,
                "Dask": t_dask
            })

    # Save Data to CSV
    csv_path = os.path.join(TARGET_DIR, "benchmark_results.csv")
    with open(csv_path, "w") as f:
        f.write("Files,Procs,Sequential,MPI,Dask\n")
        for r in results:
            f.write(f"{r['Files']},{r['Procs']},{r['Sequential']},{r['MPI']},{r['Dask']}\n")
    print(f"\nResults saved to {csv_path}")

    # Plotting is handled by create_report.py now


if __name__ == "__main__":
    run_benchmark()

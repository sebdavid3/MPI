import subprocess
import re
import os
import sys
import glob
import time
import contextlib
import io
import csv

# Ensure we can import generator
# Assuming this script is in target/ and generator is in target/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import generator

def run_command(command):
    """Runs a shell command and returns the stdout. Prints error if fails."""
    try:
        # Shell=True for windows to handle command string properly
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"\n[ERROR] Command failed with return code {result.returncode}")
            print(f"[ERROR] Command: {command}")
            print(f"[ERROR] Stderr: {result.stderr}")
            return ""
        return result.stdout
    except Exception as e:
        print(f"\n[EXCEPTION] Error running command: {command}")
        print(e)
        return ""

def extract_time(output):
    """Extracts execution time from output using a flexible regex."""
    if not output:
        return None
    # Regex flexible to handle potential encoding issues (e.g. ejecuciÃ³n vs ejecución)
    # Matches "Tiempo de" followed by anything until ": " and the number
    match = re.search(r"Tiempo de .*: (\d+\.\d+) segundos", output)
    if match:
        return float(match.group(1))
    return None

def clean_files(target_dir):
    """Removes generated text files."""
    files = glob.glob(os.path.join(target_dir, "file_*.txt"))
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error deleting {f}: {e}")

def main():
    # --- Configuration ---
    file_counts = [10, 50, 100, 500]
    # Configuración para PC con 4 núcleos físicos / 8 hilos lógicos
    # 1: Línea base (overhead del framework)
    # 4: Núcleos físicos (Punto óptimo teórico para CPU-bound puro)
    # 8: Hilos lógicos (Uso de Hyper-threading)
    worker_counts = [1, 4, 8]
    
    # --- Paths ---
    # We assume the script is run from the root MPI directory
    current_dir = os.getcwd() 
    target_dir = os.path.join(current_dir, "target")
    
    # Check if we are in the right place
    if not os.path.exists(target_dir):
        print("Error: 'target' directory not found. Please run from the root 'MPI' directory.")
        return

    # Structure to hold results
    results = {}
    
    # List to store rows for CSV
    csv_rows = []

    print("Starting Benchmark...")
    print(f"Target Directory: {target_dir}")

    # Initial cleanup
    print("Cleaning up old files before starting...")
    clean_files(target_dir)
    
    files_generated_so_far = 0

    for count in file_counts:
        print(f"\n" + "="*40)
        print(f" Testing with {count} files ")
        print("="*40)
        
        results[count] = {
            "Sequential": None,
            "MPI": {},
            "Dask": {}
        }
        
        # 1. Incremental Generation
        needed = count - files_generated_so_far
        if needed > 0:
            print(f"Generating {needed} new files (starting from {files_generated_so_far + 1})...")
            # Suppress generator output to keep console clean
            with contextlib.redirect_stdout(io.StringIO()):
                generator.generar_textos_español(num_files=needed, start_index=files_generated_so_far + 1)
            files_generated_so_far = count
        else:
            print(f"Files already generated ({files_generated_so_far}). Skipping generation.")
        
        # 2. Run Sequential (Once per file count)
        print("Running Sequential...")
        cmd_seq = f"python target/wordFreq.py"
        out_seq = run_command(cmd_seq)
        time_seq = extract_time(out_seq)
        results[count]["Sequential"] = time_seq
        print(f"  -> Sequential Time: {time_seq} s")
        
        # Add to CSV rows
        csv_rows.append({
            "Files": count,
            "Type": "Sequential",
            "Workers": 1,
            "Time": time_seq
        })

        # Loop over worker counts for Parallel implementations
        for n in worker_counts:
            # 3. Run MPI
            print(f"Running MPI with {n} processes...")
            # --oversubscribe is crucial for running more processes than physical cores
            cmd_mpi = f'docker run --rm -v "{target_dir}:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root --oversubscribe -n {n} python /app/wordFreqMPI.py'
            out_mpi = run_command(cmd_mpi)
            time_mpi = extract_time(out_mpi)
            
            if time_mpi is None:
                print(f"  [WARN] Could not extract time from MPI output.")
            
            results[count]["MPI"][n] = time_mpi
            print(f"  -> MPI ({n}) Time: {time_mpi} s")
            
            csv_rows.append({
                "Files": count,
                "Type": "MPI",
                "Workers": n,
                "Time": time_mpi
            })

            # 4. Run Dask
            print(f"Running Dask with {n} workers...")
            cmd_dask = f'docker run --rm -v "{target_dir}:/app" --network host daskdev/dask:latest python /app/wordFreqDask.py {n}'
            out_dask = run_command(cmd_dask)
            time_dask = extract_time(out_dask)
            
            if time_dask is None:
                print(f"  [WARN] Could not extract time from Dask output.")
            
            results[count]["Dask"][n] = time_dask
            print(f"  -> Dask ({n}) Time: {time_dask} s")
            
            csv_rows.append({
                "Files": count,
                "Type": "Dask",
                "Workers": n,
                "Time": time_dask
            })

    # --- Print Summary Table ---
    print("\n\n" + "="*120)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*120)
    
    # Header
    header = f"{'Files':<8} | {'Sequential':<12}"
    for n in worker_counts:
        header += f" | {'MPI ('+str(n)+')':<10}"
    for n in worker_counts:
        header += f" | {'Dask ('+str(n)+')':<10}"
    print(header)
    print("-" * len(header))

    # Rows
    for count in file_counts:
        row = f"{count:<8} | "
        
        # Sequential
        t_seq = results[count]["Sequential"]
        row += f"{t_seq:.3f} s      " if t_seq is not None else "Fail        "
        
        # MPI
        for n in worker_counts:
            t = results[count]["MPI"].get(n)
            val = f"{t:.3f} s" if t is not None else "Fail"
            row += f" | {val:<10}"
            
        # Dask
        for n in worker_counts:
            t = results[count]["Dask"].get(n)
            val = f"{t:.3f} s" if t is not None else "Fail"
            row += f" | {val:<10}"
            
        print(row)
    print("="*120)
    
    # --- Write CSV ---
    csv_file = os.path.join(target_dir, "benchmark_results.csv")
    print(f"\nWriting results to {csv_file}...")
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Files", "Type", "Workers", "Time"])
            writer.writeheader()
            writer.writerows(csv_rows)
        print("CSV write successful.")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == "__main__":
    main()

import sys
import os
import time
from collections import Counter
from dask import delayed, compute
from dask.distributed import Client, LocalCluster

def get_word_counts(filepath, words_to_count, case_sensitive=False):
    """
    Counts occurrences of specified words in a file.
    """
    c = Counter()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                words = line.split()
                if not case_sensitive:
                    words = [w.lower() for w in words]
                
                for w in words:
                    if w in words_to_count:
                        c[w] += 1
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return c

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python wordFreqDask.py <n_workers>")
        sys.exit(1)
    
    try:
        n_workers = int(sys.argv[1])
    except ValueError:
        print("Error: n_workers must be an integer")
        sys.exit(1)

    # Setup Dask Client
    # We use LocalCluster to simulate multiple workers locally
    # processes=True ensures we use processes instead of threads, similar to MPI
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1, processes=True)
    client = Client(cluster)
    
    # Determine directory path
    # If /app exists (Docker), use it. Otherwise use current directory.
    dir_path = "/app" if os.path.exists("/app") else os.path.dirname(os.path.abspath(__file__))
    file1_name = "file_01.txt"
    case_sensitive = False
    top_n = 5

    path1 = os.path.join(dir_path, file1_name)
    if not os.path.exists(path1):
        print(f"Error: {path1} not found.")
        client.close()
        return

    # 1. Read target words from file_01.txt
    with open(path1, 'r', encoding='utf-8') as f:
        words1 = f.read().split()
    
    if not case_sensitive:
        words1 = [w.lower() for w in words1]
    
    words_to_count = set(words1)

    # 2. List all other files
    files_to_process = []
    if os.path.exists(dir_path):
        for fname in os.listdir(dir_path):
            if fname.endswith(".txt") and fname != file1_name:
                files_to_process.append(os.path.join(dir_path, fname))
    
    if not files_to_process:
        print("No files to process found.")
        client.close()
        return

    print(f"Processing {len(files_to_process)} files with {n_workers} workers...")

    t0 = time.perf_counter()

    # 3. Create delayed tasks
    # We broadcast words_to_count implicitly by passing it to the function. 
    # Dask handles pickling and sending it to workers.
    tasks = []
    for fp in files_to_process:
        task = delayed(get_word_counts)(fp, words_to_count, case_sensitive)
        tasks.append(task)

    # 4. Compute
    results = compute(*tasks)

    # 5. Aggregate results
    total_counts = Counter()
    for res in results:
        total_counts.update(res)

    t1 = time.perf_counter()
    elapsed = t1 - t0

    # Output results
    print(f"Tiempo de ejecución: {elapsed:.3f} segundos\n")
    print(f"Top {top_n} palabras de {file1_name} en otros archivos:")
    for word, count in total_counts.most_common(top_n):
        print(f"  {word}: {count}")

    client.close()

if __name__ == "__main__":
    main()

import sys
import os
import time
from collections import Counter
from dask import delayed, compute
from dask.distributed import Client, LocalCluster

def process_file(path, vocab):
    counts = Counter()
    with open(path, 'r', encoding='utf-8') as f:
        # Leemos todo el contenido, pasamos a minusculas y dividimos
        words = f.read().lower().split()
        for w in words:
            if w in vocab:
                counts[w] += 1
    return counts

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python wordFreqDask.py <n_workers>")
        sys.exit(1)

    n_workers = int(sys.argv[1])
    
    # Iniciamos el cluster local
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1, processes=True)
    client = Client(cluster)
    
    # Detectar si estamos en docker o local
    work_dir = "/app" if os.path.exists("/app") else os.path.dirname(os.path.abspath(__file__))
    ref_file = "file_01.txt"
    
    ref_path = os.path.join(work_dir, ref_file)
    if not os.path.exists(ref_path):
        print(f"No se encontro {ref_file}")
        sys.exit(1)

    # Cargar palabras de referencia
    with open(ref_path, 'r', encoding='utf-8') as f:
        vocab = set(f.read().lower().split())

    # Buscar archivos .txt
    files = []
    for f in os.listdir(work_dir):
        if f.endswith(".txt") and f != ref_file:
            files.append(os.path.join(work_dir, f))

    print(f"Procesando {len(files)} archivos...")

    t_start = time.perf_counter()

    # Generar grafo de tareas
    tasks = [delayed(process_file)(f, vocab) for f in files]
    
    # Ejecutar
    results = compute(*tasks)

    # Unificar resultados
    final_counts = Counter()
    for res in results:
        final_counts.update(res)

    t_end = time.perf_counter()

    print(f"Tiempo de ejecución: {t_end - t_start:.3f} segundos\n")
    print(f"Top 5 palabras de {ref_file} en otros archivos:")
    for w, c in final_counts.most_common(5):
        print(f"  {w}: {c}")

    client.close()

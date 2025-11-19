import os
import re
import time
import argparse
from collections import Counter
from dask.distributed import Client, LocalCluster


def contar_palabras_en_archivo(ruta, palabras_buscar, case_sensitive=False):
    """Cuenta ocurrencias de las palabras indicadas en un archivo.

    Usa una tokenización simple basada en \w para evitar puntuación.
    """
    contador = Counter()
    palabra_pat = re.compile(r"\w+", flags=re.UNICODE)
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            tokens = palabra_pat.findall(linea)
            if not case_sensitive:
                tokens = [t.lower() for t in tokens]
            for t in tokens:
                if t in palabras_buscar:
                    contador[t] += 1
    return contador


def main():
    """Script Dask para calcular top-N basado en apariciones en los otros archivos.

    Uso (posicional o con --workers):
      python wordFreqDask.py 5
      python wordFreqDask.py --workers 5
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("workers", nargs="?", type=int, help="Número de workers (posicional)")
    parser.add_argument("-w", "--workers", dest="wopt", type=int, help="Número de workers (opcional)")
    parser.add_argument("-d", "--dir", dest="directorio", default=None, help="Directorio con .txt (por defecto /app o cwd)")
    parser.add_argument("-t", "--top", dest="topn", type=int, default=5, help="Top N palabras")
    parser.add_argument("--case-sensitive", dest="case", action="store_true", help="Mantener mayúsculas/minúsculas")
    args = parser.parse_args()

    # Elegir número de workers: preferir la opción larga si se proporcionó
    n_workers = args.wopt if args.wopt is not None else (args.workers if args.workers is not None else 2)

    dir_path = args.directorio if args.directorio else ("/app" if os.path.exists("/app") else os.path.abspath("."))
    file1 = "file_01.txt"

    # Leer file_01
    t0 = time.perf_counter()
    ruta1 = os.path.join(dir_path, file1)
    if not os.path.isfile(ruta1):
        print(f"Error: no encuentro {file1} en {dir_path}")
        return
    with open(ruta1, "r", encoding="utf-8") as f:
        texto = f.read()
    if not args.case:
        texto = texto.lower()
    palabras1 = set(re.findall(r"\w+", texto, flags=re.UNICODE))
    t1 = time.perf_counter()

    # Lista de archivos a procesar
    archivos = [os.path.join(dir_path, a) for a in os.listdir(dir_path) if a.endswith(".txt") and a != file1]

    # Poner en marcha el cluster local de Dask
    t0_cluster = time.perf_counter()
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1)
    client = Client(cluster)
    t1_cluster = time.perf_counter()

    # Mapear la función sobre los archivos
    t0_sched = time.perf_counter()
    futures = client.map(lambda p: contar_palabras_en_archivo(p, palabras1, args.case), archivos)
    resultados = client.gather(futures)
    t1_sched = time.perf_counter()

    # Agregar resultados
    t0_agg = time.perf_counter()
    total = Counter()
    for c in resultados:
        total.update(c)
    t1_agg = time.perf_counter()

    # Cerrar
    client.close()
    cluster.close()

    # Mostrar tiempos y resultados
    print("Tiempos (s):")
    print(f"  lectura file_01: {t1 - t0:.3f}")
    print(f"  cluster setup: {t1_cluster - t0_cluster:.3f}")
    print(f"  scheduling+compute: {t1_sched - t0_sched:.3f}")
    print(f"  agregación: {t1_agg - t0_agg:.3f}")
    print(f"Tiempo total (aprox): {(t1_agg - t0):.3f} s\n")

    print(f"Top {args.topn} palabras de {file1} en los otros archivos:")
    for palabra, cuenta in total.most_common(args.topn):
        print(f"  {palabra}: {cuenta}")


if __name__ == "__main__":
    main()

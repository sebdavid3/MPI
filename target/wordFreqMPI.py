from mpi4py import MPI
import os
from collections import Counter

def contar_palabras(archivos, palabras_buscar, case_sensitive=False):
    contador = Counter()
    
    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            texto = f.read().split()
            if not case_sensitive:
                texto = [p.lower() for p in texto]
            for palabra in texto:
                if palabra in palabras_buscar:
                    contador[palabra] += 1
    
    return contador


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    # Determine directory path
    # If /app exists (Docker), use it. Otherwise use the directory where the script is located.
    dir_path = "/app" if os.path.exists("/app") else os.path.dirname(os.path.abspath(__file__))
    file1_name = "file_01.txt"
    case_sensitive = False
    top_n = 5
    
    palabras_buscar = None
    mis_archivos = []
    
    if rank == 0:
        t_inicio = MPI.Wtime()
        
        # Leer file_01.txt
        path1 = os.path.join(dir_path, file1_name)
        with open(path1, "r", encoding="utf-8") as f:
            palabras1 = f.read().split()
        
        if not case_sensitive:
            palabras1 = [p.lower() for p in palabras1]
        palabras_buscar = set(palabras1)
        
        # Listar archivos a procesar
        archivos = []
        for fname in os.listdir(dir_path):
            if fname.endswith(".txt") and fname != file1_name:
                archivos.append(os.path.join(dir_path, fname))
        
        # Dividir archivos entre procesos
        for i, archivo in enumerate(archivos):
            if i % size == 0:
                mis_archivos.append(archivo)
        
        # Enviar a workers
        for dest in range(1, size):
            archivos_worker = [a for i, a in enumerate(archivos) if i % size == dest]
            comm.send(palabras_buscar, dest=dest)
            comm.send(archivos_worker, dest=dest)
    
    else:
        palabras_buscar = comm.recv(source=0)
        mis_archivos = comm.recv(source=0)
    
    # Procesar archivos
    contador_local = contar_palabras(mis_archivos, palabras_buscar, case_sensitive)
    
    if rank == 0:
        contador_global = contador_local.copy()
        
        # Recibir de workers
        for _ in range(1, size):
            contador_parcial = comm.recv(source=MPI.ANY_SOURCE)
            for palabra, cuenta in contador_parcial.items():
                contador_global[palabra] += cuenta
        
        t_fin = MPI.Wtime()
        
        # Resultados
        print(f"Tiempo de ejecución: {t_fin - t_inicio:.3f} segundos\n")
        print(f"Top {top_n} palabras de {file1_name} en otros archivos:")
        for palabra, cuenta in contador_global.most_common(top_n):
            print(f"  {palabra}: {cuenta}")
    
    else:
        comm.send(contador_local, dest=0)


if __name__ == "__main__":
    main()

# MPI & Dask Examples

Use augustosalazar/slim-mpi or augustosalazar/slim-mpi:2 (for macOS and windows) or augustosalazar/un_mpi_image:v5

Start the container with one of the following commands:

```bash
docker run -d -it --name mpicont -v "%cd%\target:/app" augustosalazar/slim-mpi

docker run -d -it --name mpicont -v "$(pwd)"/target:/app augustosalazar/slim-mpi
```

To run the container interactively, use:

```bash 
docker exec -it mpicont mpiexec --allow-run-as-root -n 3 python /app/code0.py
```

or run and delete the container after execution:
```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 3 python /app/code0.py

docker run --rm -v "$(pwd)"/target:/app augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 3 python /app/code0.py
```


## Prime example

### Serial version
Busqueda de los primos con 5 dígitos
```bash
docker run --rm -v "$(pwd)"/target:/app augustosalazar/slim-mpi:2 mpiexec python /app/primeChecker.py 5
```

### MPI version
Busqueda de los primos con 5 dígitos usando MPI con 4 workers (con un batch size de 10)
```bash
docker run --rm -v "$(pwd)"/target:/app augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root -n 4 python /app/primeCheckerMPI.py 5
```

###  Dask version
Busqueda de los primos con 5 dígitos usando Dask con 4 workers (con un batch size de 10)
```bash
docker run --rm -v "$(pwd)"/target:/app --network host daskdev/dask:latest python /app/primeCheckerDask.py 5 4
```

To install nano on Play with Docker:
apk --update add nano


## Shared Memory

```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 3 python /app/shared01.py
Proceso 2 de 3 iniciado.
Proceso 0 de 3 iniciado.
Proceso 1 de 3 iniciado.
Contenido del array compartido:
[ 0 10 20]
```

## Word Frequency Analysis

### Generate test files

Primero genera archivos de prueba con palabras en español:

```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi python /app/generator.py
```

### Serial word frequency version

Análisis secuencial de frecuencia de palabras:

```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi python /app/wordFreq.py
```

### MPI word frequency version

Análisis paralelo de frecuencia de palabras usando MPI con 3 procesos:

```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 3 python /app/wordFreqMPI.py
```

Para usar más procesos (recomendado con muchos archivos):

```bash
docker run --rm -v "%cd%\target:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 4 python /app/wordFreqMPI.py
```

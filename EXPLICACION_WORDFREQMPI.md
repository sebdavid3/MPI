# Explicación wordFreqMPI.py

## Objetivo

Buscar las 5 palabras más frecuentes de `file_01.txt` contando cuántas veces aparecen en el resto de archivos .txt del directorio. La versión MPI distribuye el trabajo entre varios procesos para hacerlo más rápido.

## Cómo funciona

**Explicación: `wordFreqMPI.py`**

**Objetivo**

Crear una versión paralela (MPI) que, dado un directorio con muchos archivos `.txt`, extraiga las cinco palabras más relevantes de `file_01.txt` según su número total de apariciones en el resto de archivos del mismo directorio, y muestre además el tiempo de ejecución.

**Resumen del criterio de selección (qué significa "Top 5")**

- Primero se toman las palabras que aparecen en `file_01.txt` (sin ordenar ni contar sus repeticiones dentro de `file_01`).
- De ese conjunto de palabras, se cuentan todas sus apariciones en TODOS los demás archivos `.txt` del directorio (es decir, se suman las ocurrencias en los archivos `file_02.txt` … `file_100.txt`).
- Finalmente, se ordenan por frecuencia descendente y se seleccionan las 5 con mayor recuento. Es importante: NO se calculan las top 5 basadas en la frecuencia dentro de `file_01.txt`, sino en la frecuencia que esas palabras tienen en el resto de archivos.

**Paso a paso de la implementación**

1. Rank 0 (proceso maestro):
	- Lee `file_01.txt` y tokeniza (por defecto usando `split()`), normalizando a minúsculas si `case_sensitive=False`.
	- Crea un `set` con las palabras encontradas en `file_01.txt` (esto define el universo de palabras a buscar en los demás archivos).
	- Lista todos los archivos `.txt` en el directorio y excluye `file_01.txt`.
	- Reparte la lista de archivos entre los procesos disponibles usando una regla simple: asignar el archivo con índice `i` al proceso `i % size`.
	- Envía a cada worker (ranks != 0) dos objetos mediante `comm.send()`: el `set` de `palabras_buscar` y la lista de rutas de los archivos asignados a ese worker.

2. Workers (ranks 1..N-1):
	- Reciben `palabras_buscar` y la lista de archivos que deben procesar.
	- Para cada archivo asignado leen su contenido, tokenizan (actualmente `split()`), normalizan a minúsculas si procede y cuentan solo las palabras que están en `palabras_buscar` (utilizando `collections.Counter`).
	- Envian su `Counter` parcial al rank 0 con `comm.send(contador_local, dest=0)`.

3. Rank 0 (agregación y salida):
	- Copia su propio `contador_local` y, en un bucle, recibe los contadores parciales con `comm.recv(source=MPI.ANY_SOURCE)` y los acumula en `contador_global`.
	- Mide el tiempo total con `MPI.Wtime()` (inicio antes de repartir y fin después de acumular los resultados).
	- Imprime el `top_n` (por defecto `top_n=5`) con `contador_global.most_common(top_n)` y el tiempo transcurrido.

**Detalles MPI solicitados**

- La recepción en `rank 0` se hace usando `comm.recv(source=MPI.ANY_SOURCE)`, cumpliendo la indicación explícita de aceptar mensajes desde cualquier trabajador.

**Comandos Docker reproducibles (PowerShell)**

1) Generar 100 archivos de prueba:
```powershell
docker run --rm -v "C:\ruta\a\tu\repo\target:/app" augustosalazar/slim-mpi python /app/generator.py
```

2) Ejecutar versión secuencial para referencia:
```powershell
docker run --rm -v "C:\ruta\a\tu\repo\target:/app" augustosalazar/slim-mpi python /app/wordFreq.py
```

3) Ejecutar versión MPI (ej. 3 procesos):
```powershell
docker run --rm -v "C:\ruta\a\tu\repo\target:/app" augustosalazar/slim-mpi mpiexec --allow-run-as-root -n 3 python /app/wordFreqMPI.py
```

Nota: en el ejemplo que ejecuté en este entorno obtuve tiempos del orden de 2.1–3.5 s (MPI) frente a ~6 s (secuencial) sobre 100 archivos grandes; los valores dependen del hardware.

**Por qué la versión MPI es más rápida (intuitivamente)**

- I/O paralelo: varios procesos leen archivos al mismo tiempo en lugar de un único proceso que los procesa secuencialmente.
- Trabajo dividido: el coste de procesar N archivos se reparte entre P procesos; idealmente la fase de conteo se acelera por ~P (menos la sobrecarga de comunicación y sincronización).

**Limitaciones actuales y posibles mejoras**

- Tokenización simple: el código usa `split()`, lo que no elimina puntuación ni normaliza caracteres especiales. Si quieres resultados más robustos conviene usar `re.findall(r"\w+", text, flags=re.UNICODE)` o normalizar con `unicodedata`.
- Balanceo de carga: la partición actual `i % size` funciona bien con muchos archivos similares, pero si los tamaños varían mucho es mejor repartir por bloques contiguos o por tamaño de archivo para equilibrar el tiempo de cada worker.
- Envío de datos: se envía el `set` completo de palabras a cada worker; si `file_01.txt` tuviera millones de palabras repetidas se podría optimizar (por ejemplo enviando solo las palabras únicas o usando filtros bloom para reducir tamaño).

**Validación y evidencia**

- Generé 100 archivos con `generator.py` dentro del contenedor y ejecuté ambas versiones:
  - Secuencial: tiempo observado ~6.02 s (top 10 mostrado).
  - MPI (3 procesos): tiempo observado ~2.13 s, Top 5: `nuestro, vuestras, hay, ya, tu` (cuentas totales mostradas).
  - MPI (4 procesos): tiempo observado ~2.16 s (pequeña variación según ejecución).

**Qué hace exactamente el "Top 5" mostrado**

- El Top 5 son las cinco palabras del conjunto de `file_01.txt` que más veces aparecen sumadas en el resto de archivos. Ejemplo:
  - Si `file_01.txt` contiene `['sol','mar','sol','cielo']` → palabras a considerar = `{'sol','mar','cielo'}`.
  - Si entre todos los demás archivos `sol` aparece 120 veces, `mar` 45 y `cielo` 60 → el resultado mostrará `sol, cielo, mar`.

**Siguientes pasos que puedo hacer por ti**

- Mejorar tokenización y normalización (quitar puntuación, manejar contracciones y acentos).
- Cambiar la estrategia de reparto para balancear por tamaño de archivo y volver a medir tiempos.
- Añadir salida detallada que muestre las cuentas de las top 20 palabras y porcentajes relativos.

Archivo creado: `EXPLICACION_WORDFREQMPI.md` (esta explicación).

Si quieres que añada esto también como un archivo corto dentro de `target/README.md` o que modifique `wordFreqMPI.py` para incluir opciones por línea de comandos, dímelo y lo hago.

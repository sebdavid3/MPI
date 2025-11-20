import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def generate_graphs():
    print("Iniciando generación de gráficos mejorados...")
    
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "benchmark_results.csv")
    output_dir = current_dir
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Load Data
    df = pd.read_csv(csv_path)
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    # Convert to milliseconds
    df['Time'] = df['Time'] * 1000
    
    # Global Style Settings
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.titlesize': 18,
        'lines.linewidth': 2.5,
        'lines.markersize': 8,
        'grid.alpha': 0.6,
        'grid.linestyle': '--'
    })

    # --- Helpers ---
    def get_categorical_x(files_series, all_files):
        return [all_files.index(f) for f in files_series]

    file_counts = sorted(df['Files'].unique())
    x_indices = range(len(file_counts))

    # --- 1. Comparison Bar Chart (500 Files) ---
    print("Generando: comparison_500_files.png")
    plt.figure(figsize=(12, 7))
    
    subset = df[df['Files'] == 500].sort_values(['Type', 'Workers'])
    labels = subset.apply(lambda x: f"{x['Type']} ({int(x['Workers'])})" if x['Type'] != 'Sequential' else 'Secuencial', axis=1)
    
    # Colors
    colors = []
    for _, row in subset.iterrows():
        if row['Type'] == 'Sequential': colors.append('#555555') # Gray
        elif row['Type'] == 'MPI': colors.append('#1f77b4')      # Blue
        elif row['Type'] == 'Dask': colors.append('#ff7f0e')     # Orange
    
    bars = plt.bar(labels, subset['Time'], color=colors, edgecolor='black', alpha=0.8)
    
    plt.title('Tiempo de Ejecución (500 Archivos)')
    plt.ylabel('Tiempo (ms)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    
    # Annotate bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                 f'{height:.0f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')
                 
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'comparison_500_files.png'), dpi=300)
    plt.close()

    # --- 2. Scalability Summary (Categorical X) ---
    print("Generando: scalability.png")
    plt.figure(figsize=(12, 7))
    
    # Find best configurations
    df_500 = df[df['Files'] == 500]
    best_mpi_w = df_500[df_500['Type'] == 'MPI'].sort_values('Time').iloc[0]['Workers']
    best_dask_w = df_500[df_500['Type'] == 'Dask'].sort_values('Time').iloc[0]['Workers']
    
    # Sequential
    seq_data = df[df['Type'] == 'Sequential'].sort_values('Files')
    plt.plot(get_categorical_x(seq_data['Files'], file_counts), seq_data['Time'], 
             marker='o', color='#555555', label='Secuencial', linestyle=':')
    
    # Best MPI
    mpi_data = df[(df['Type'] == 'MPI') & (df['Workers'] == best_mpi_w)].sort_values('Files')
    plt.plot(get_categorical_x(mpi_data['Files'], file_counts), mpi_data['Time'], 
             marker='s', color='#1f77b4', label=f'Mejor MPI ({int(best_mpi_w)} procs)')
             
    # Best Dask
    dask_data = df[(df['Type'] == 'Dask') & (df['Workers'] == best_dask_w)].sort_values('Files')
    plt.plot(get_categorical_x(dask_data['Files'], file_counts), dask_data['Time'], 
             marker='^', color='#ff7f0e', label=f'Mejor Dask ({int(best_dask_w)} workers)')
    
    plt.title('Escalabilidad Resumida: Archivos vs Tiempo')
    plt.xlabel('Número de Archivos')
    plt.ylabel('Tiempo (ms)')
    plt.xticks(x_indices, file_counts)
    plt.legend()
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'scalability.png'), dpi=300)
    plt.close()

    # --- 3. Detailed Scalability (All Lines) ---
    print("Generando: scalability_detailed.png")
    plt.figure(figsize=(14, 8))
    
    # Sequential
    plt.plot(get_categorical_x(seq_data['Files'], file_counts), seq_data['Time'], 
             marker='o', label='Secuencial', color='black', linestyle=':', linewidth=3)
    
    # MPI Gradients
    mpi_workers = sorted(df[df['Type'] == 'MPI']['Workers'].unique())
    mpi_colors = plt.cm.Blues(np.linspace(0.4, 1.0, len(mpi_workers)))
    for i, w in enumerate(mpi_workers):
        data = df[(df['Type'] == 'MPI') & (df['Workers'] == w)].sort_values('Files')
        plt.plot(get_categorical_x(data['Files'], file_counts), data['Time'], 
                 marker='s', label=f'MPI ({int(w)})', color=mpi_colors[i])

    # Dask Gradients
    dask_workers = sorted(df[df['Type'] == 'Dask']['Workers'].unique())
    dask_colors = plt.cm.Oranges(np.linspace(0.4, 1.0, len(dask_workers)))
    for i, w in enumerate(dask_workers):
        data = df[(df['Type'] == 'Dask') & (df['Workers'] == w)].sort_values('Files')
        plt.plot(get_categorical_x(data['Files'], file_counts), data['Time'], 
                 marker='^', label=f'Dask ({int(w)})', color=dask_colors[i], linestyle='--')

    plt.title('Escalabilidad Detallada (Todas las Configuraciones)')
    plt.xlabel('Número de Archivos')
    plt.ylabel('Tiempo (ms)')
    plt.xticks(x_indices, file_counts)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'scalability_detailed.png'), dpi=300)
    plt.close()

    # --- 4. Workers Impact (100 & 500 Files) ---
    print("Generando: workers_impact.png")
    plt.figure(figsize=(12, 7))
    
    for files in [100, 500]:
        # MPI
        mpi_data = df[(df['Type'] == 'MPI') & (df['Files'] == files)].sort_values('Workers')
        plt.plot(mpi_data['Workers'], mpi_data['Time'], 
                 marker='s', label=f'MPI ({files} files)', linestyle='-', linewidth=2)
        
        # Dask
        dask_data = df[(df['Type'] == 'Dask') & (df['Files'] == files)].sort_values('Workers')
        plt.plot(dask_data['Workers'], dask_data['Time'], 
                 marker='^', label=f'Dask ({files} files)', linestyle='--', linewidth=2)

    plt.title('Impacto de la Cantidad de Procesos')
    plt.xlabel('Número de Procesos/Workers')
    plt.ylabel('Tiempo (ms)')
    plt.legend()
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'workers_impact.png'), dpi=300)
    plt.close()

    # --- 5. Speedup ---
    print("Generando: speedup.png")
    plt.figure(figsize=(12, 7))
    
    seq_time_500 = df[(df['Files'] == 500) & (df['Type'] == 'Sequential')]['Time'].iloc[0]
    mpi_500 = df[(df['Files'] == 500) & (df['Type'] == 'MPI')].sort_values('Workers')
    dask_500 = df[(df['Files'] == 500) & (df['Type'] == 'Dask')].sort_values('Workers')
    
    mpi_speedup = seq_time_500 / mpi_500['Time']
    dask_speedup = seq_time_500 / dask_500['Time']
    
    plt.plot(mpi_500['Workers'], mpi_speedup, marker='s', label='MPI Speedup', color='#1f77b4')
    plt.plot(dask_500['Workers'], dask_speedup, marker='^', label='Dask Speedup', color='#ff7f0e')
    
    # Ideal Line
    plt.plot([1, 8], [1, 8], 'g--', label='Ideal (Lineal)', alpha=0.5)
    
    plt.title('Speedup (Aceleración) con 500 Archivos')
    plt.xlabel('Número de Procesos')
    plt.ylabel('Speedup (X veces más rápido)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'speedup.png'), dpi=300)
    plt.close()

    # --- 6. Efficiency ---
    print("Generando: efficiency.png")
    plt.figure(figsize=(12, 7))
    
    mpi_eff = mpi_speedup / mpi_500['Workers']
    dask_eff = dask_speedup / dask_500['Workers']
    
    plt.plot(mpi_500['Workers'], mpi_eff, marker='s', label='MPI Eficiencia', color='#1f77b4')
    plt.plot(dask_500['Workers'], dask_eff, marker='^', label='Dask Eficiencia', color='#ff7f0e')
    
    plt.axhline(y=1.0, color='g', linestyle='--', label='Eficiencia Ideal (1.0)', alpha=0.5)
    
    plt.title('Eficiencia Paralela con 500 Archivos')
    plt.xlabel('Número de Procesos')
    plt.ylabel('Eficiencia (Speedup / N)')
    plt.ylim(0, 1.2)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'efficiency.png'), dpi=300)
    plt.close()

    print("¡Generación de gráficos completada!")

if __name__ == "__main__":
    generate_graphs()

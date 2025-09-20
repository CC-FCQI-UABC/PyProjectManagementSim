# Contenido completo y actualizado de analysis/visualize_results.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def analyze_and_visualize(csv_filepath: str):
    """
    Carga los resultados de una simulación desde un archivo CSV y genera gráficos.

    Args:
        csv_filepath: La ruta al archivo CSV con los resultados.
    """
    if not os.path.exists(csv_filepath):
        print(f"Error: El archivo no fue encontrado en la ruta: {csv_filepath}")
        return

    print(f"\nCargando resultados desde: {os.path.basename(csv_filepath)}")
    df = pd.read_csv(csv_filepath)

    if df.empty:
        print("El archivo CSV está vacío. No se pueden generar gráficos.")
        return

    base_filename = os.path.splitext(os.path.basename(csv_filepath))[0]
    output_dir = os.path.join(os.path.dirname(csv_filepath), f"charts_{base_filename}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Los gráficos se guardarán en: {output_dir}")

    # --- Gráfico 1: Métricas de Rendimiento del Proyecto (CON VARIANZA) ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig1, ax1 = plt.subplots(figsize=(14, 8))

    # MODIFICADO: Calculamos promedio (mean) y desviación estándar (std)
    # Filtramos valores de CPI y SPI infinitos o muy grandes que pueden distorsionar la gráfica
    df_filtered = df[df['CPI'] < 5]
    evm_stats = df_filtered.groupby('Time')[['CPI', 'SPI']].agg(['mean', 'std']).fillna(0)

    # Datos para la línea de completitud promedio
    completion_data = df.groupby('Time')['Completion'].mean()

    # --- Graficar CPI con su desviación estándar ---
    cpi_mean = evm_stats[('CPI', 'mean')]
    cpi_std = evm_stats[('CPI', 'std')]
    ax1.plot(cpi_mean.index, cpi_mean, label='CPI Promedio', color='green', linewidth=2)
    ax1.fill_between(cpi_mean.index, cpi_mean - cpi_std, cpi_mean + cpi_std, color='green', alpha=0.15,
                     label='Desviación Estándar CPI')

    # --- Graficar SPI con su desviación estándar ---
    spi_mean = evm_stats[('SPI', 'mean')]
    spi_std = evm_stats[('SPI', 'std')]
    ax1.plot(spi_mean.index, spi_mean, label='SPI Promedio', color='blue', linewidth=2)
    ax1.fill_between(spi_mean.index, spi_mean - spi_std, spi_mean + spi_std, color='blue', alpha=0.15,
                     label='Desviación Estándar SPI')

    # --- Graficar una sola simulación para ver una trayectoria individual ---
    single_run_df = df[df['simulation_id'] == 1]
    if not single_run_df.empty:
        ax1.plot(single_run_df['Time'], single_run_df['CPI'], label='CPI (Ej. Sim #1)', color='darkgreen',
                 linestyle=':', alpha=0.7)

    ax1.axhline(y=1.0, color='gray', linestyle='--', label='Línea Base (1.0)')

    ax2 = ax1.twinx()
    ax2.plot(completion_data.index, completion_data, label='% Completado Promedio', color='orange', linestyle='--')

    ax1.set_title('Rendimiento del Proyecto (Promedio y Desviación Estándar)', fontsize=16)
    ax1.set_xlabel('Tiempo (Pasos de Simulación)', fontsize=12)
    ax1.set_ylabel('Índices de Rendimiento (CPI/SPI)', fontsize=12)
    ax2.set_ylabel('% Completado', fontsize=12)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='best')

    fig1.tight_layout()
    chart_path1 = os.path.join(output_dir, "project_performance_summary_variance.png")
    fig1.savefig(chart_path1)
    print(f" -> Gráfico 1 (con varianza) guardado: {os.path.basename(chart_path1)}")
    plt.close(fig1)

    # --- Gráfico 2: Dinámicas de Equipo (Moral y Cohesión) ---
    if 'AvgTeamMorale' in df.columns and 'AvgTeamCohesion' in df.columns:
        fig2, ax = plt.subplots(figsize=(12, 7))

        team_data = df.groupby('Time')[['AvgTeamMorale', 'AvgTeamCohesion']].mean()

        ax.plot(team_data.index, team_data['AvgTeamMorale'], label='Moral Promedio del Equipo', color='purple')
        ax.plot(team_data.index, team_data['AvgTeamCohesion'], label='Cohesión Promedio del Equipo', color='red',
                linestyle='--')

        ax.set_title('Dinámicas de Equipo a lo largo del Tiempo (Promedio)', fontsize=16)
        ax.set_xlabel('Tiempo (Pasos de Simulación)', fontsize=12)
        ax.set_ylabel('Nivel de Moral / Factor de Cohesión', fontsize=12)
        ax.legend()
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        fig2.tight_layout()
        chart_path2 = os.path.join(output_dir, "team_dynamics_summary.png")
        fig2.savefig(chart_path2)
        print(f" -> Gráfico 2 guardado: {os.path.basename(chart_path2)}")
        plt.close(fig2)
    else:
        print("Advertencia: No se encontraron las columnas 'AvgTeamMorale' o 'AvgTeamCohesion' para el gráfico 2.")


def find_and_select_results_file():
    # ... (Esta función no necesita cambios)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__));
        project_root = os.path.normpath(os.path.join(script_dir, '..'))
        results_folder = os.path.join(project_root, 'core', 'generated')
        if not os.path.isdir(results_folder): print(f"Error: No se encuentra la carpeta '{results_folder}'"); return
        csv_files = sorted([f for f in os.listdir(results_folder) if f.endswith('.csv')],
                           key=lambda f: os.path.getmtime(os.path.join(results_folder, f)), reverse=True)
        if not csv_files: print(f"No se encontraron archivos .csv en '{results_folder}'."); return
        print("\n--- Analizador de Resultados de Simulación ---");
        print("Selecciona el archivo a analizar:")
        for i, filename in enumerate(csv_files): print(f"  [{i + 1}] {filename}")
        while True:
            try:
                choice = input(f"\nIntroduce un número (1-{len(csv_files)}): ")
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(csv_files):
                    selected_file = os.path.join(results_folder, csv_files[choice_index]);
                    analyze_and_visualize(selected_file);
                    break
                else:
                    print("Selección inválida.")
            except (ValueError, IndexError):
                print("Entrada no válida.")
            except KeyboardInterrupt:
                print("\nAnálisis cancelado."); break
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")


if __name__ == "__main__":
    find_and_select_results_file()
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math
import argparse
import sys
import os

def assign_confidence_category(confidence):
    """Assigns confidence to categories for stacking."""
    if confidence >= 0.5:
        return 'Confidence >= 0.5'
    elif confidence >= 0.4:
        return '0.4 <= Confidence < 0.5'
    else: # confidence >= 0.3 (or whatever the lower chart threshold is)
        return '0.3 <= Confidence < 0.4' # Label might need adjustment based on input param

def main():
    parser = argparse.ArgumentParser(description="Generate species detection summary charts from BirdNet CSV.")
    parser.add_argument('--input-csv', type=str, required=True, help="Path to the birdnet_classification.csv file.")
    parser.add_argument('--output-prefix', type=str, required=True, help="Prefix for saving output plot PNG files (e.g., 'job_dir/plot').")
    parser.add_argument('--min-confidence-chart', type=float, default=0.3, help="Minimum confidence threshold to include in the chart.")
    parser.add_argument('--species-per-plot', type=int, default=50, help="Maximum number of species per plot.")
    
    args = parser.parse_args()

    # --- 1. Load Data ---
    try:
        results_df = pd.read_csv(args.input_csv)
        print(f"Loaded {len(results_df)} records from {args.input_csv}")
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at {args.input_csv}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Calculate counts for each confidence level ---
    # Filter based on the CHART confidence threshold
    results_df_filtered = results_df[results_df['confidence'] >= args.min_confidence_chart].copy()

    # Dynamic confidence category assignment (adjust labels based on threshold)
    def assign_dynamic_confidence_category(confidence):
        if confidence >= 0.5:
            return 'Conf >= 0.5'
        elif confidence >= 0.4:
            return '0.4 <= Conf < 0.5'
        else: # Should match args.min_confidence_chart if it's 0.3
            return f"{args.min_confidence_chart:.1f} <= Conf < 0.4" # Dynamic label

    results_df_filtered['conf_category'] = results_df_filtered['confidence'].apply(assign_dynamic_confidence_category)

    # --- 3. Prepare data for plotting ---
    plot_data = results_df_filtered.pivot_table(index='common_name', columns='conf_category', aggfunc='size', fill_value=0)

    # Define categories dynamically based on threshold
    categories = ['Conf >= 0.5']
    if args.min_confidence_chart <= 0.4:
        categories.append('0.4 <= Conf < 0.5')
    if args.min_confidence_chart <= 0.3: # Assuming lowest possible is 0.3 for this category
         categories.append(f"{args.min_confidence_chart:.1f} <= Conf < 0.4")

    # Ensure all expected columns exist, even if empty
    for category in categories:
        if category not in plot_data.columns:
            plot_data[category] = 0

    # Order columns correctly
    plot_data = plot_data[categories]
    plot_data['total_detections'] = plot_data.sum(axis=1)
    plot_data = plot_data.sort_values(by='total_detections', ascending=False).drop(columns=['total_detections'])

    if plot_data.empty:
        print("No data remaining after filtering. Cannot generate plots.", file=sys.stderr)
        sys.exit(0) # Exit gracefully, not an error

    # --- 4. Generate Multiple Plots ---
    species_per_plot = args.species_per_plot
    total_species = len(plot_data)
    num_plots = math.ceil(total_species / species_per_plot)

    print(f"\nTotal species to plot: {total_species}")
    print(f"Generating {num_plots} separate plots with up to {species_per_plot} species each.")

    # Use a backend that doesn't require a GUI
    plt.switch_backend('Agg')

    for i in range(num_plots):
        start_index = i * species_per_plot
        end_index = start_index + species_per_plot
        data_slice = plot_data.iloc[start_index:end_index]

        sns.set_style("whitegrid")
        fig, ax = plt.subplots(figsize=(16, 10))

        data_slice.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color=sns.color_palette("viridis", len(categories)) # Dynamic palette size
        )

        plot_number = i + 1
        ax.set_title(f'Cumulative Bird Detections (Part {plot_number} of {num_plots})', fontsize=20, pad=20)
        ax.set_xlabel('Bird Species', fontsize=14, labelpad=15)
        ax.set_ylabel('Number of Detections', fontsize=14, labelpad=15)
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        ax.legend(title='Confidence Threshold', fontsize=12, title_fontsize=14)
        plt.tight_layout()

        output_filename = f'{args.output_prefix}_{plot_number}.png'
        try:
            plt.savefig(output_filename)
            print(f"Saved chart to {output_filename}")
        except Exception as e:
            print(f"Error saving plot {output_filename}: {e}", file=sys.stderr)
        plt.close(fig) # Close the figure to free up memory

if __name__ == "__main__":
    main()
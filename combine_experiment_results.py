#!/usr/bin/env python3
"""
Script to combine all experiment CSV results into a single summary table
"""

import pandas as pd
import glob
import sys
import os
from datetime import datetime

def combine_results(pattern="results_*.csv"):
    """
    Combine all CSV files matching the pattern into a summary
    """
    print("Combining Experiment Results")
    print("=" * 60)
    
    # Find all CSV files
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f"No files found matching pattern: {pattern}")
        return None
    
    print(f"Found {len(csv_files)} result files:")
    for f in csv_files:
        print(f"  - {f}")
    
    # Dictionary to store summary data
    summary_data = []
    
    for csv_file in csv_files:
        # Extract experiment name from filename
        # Format: results_EXPNAME_TIMESTAMP.csv
        filename = os.path.basename(csv_file)
        parts = filename.replace("results_", "").replace(".csv", "").rsplit("_", 2)
        if len(parts) >= 1:
            exp_name = parts[0]
        else:
            exp_name = filename
        
        try:
            # Read the CSV
            df = pd.read_csv(csv_file)
            
            # Extract key metrics for each event type
            for _, row in df.iterrows():
                summary_data.append({
                    'Experiment': exp_name,
                    'Event': row['Event'],
                    'GPU Configuration': row['GPU Configuration'],
                    'Imbalance test': row['Imbalance test'],
                    'Avg Bandwidth [GB/s]': row['avg bandwidth [GB/s]'],
                    'Avg Time [us]': row['avg_t [us]'],
                    'Std Dev [GB/s]': row['Std deviation [GB/s]']
                })
                
        except Exception as e:
            print(f"  Error reading {csv_file}: {e}")
    
    if summary_data:
        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_data)
        
        # Create pivot table for bandwidth comparison
        print("\n" + "=" * 60)
        print("BANDWIDTH SUMMARY BY EXPERIMENT")
        print("=" * 60)
        
        # Filter for main events only
        main_events = ['dispatch + combine', 'dispatch', 'combine']
        
        for event in main_events:
            event_df = summary_df[summary_df['Event'] == event]
            if not event_df.empty:
                print(f"\n{event.upper()}:")
                print("-" * 40)
                
                pivot = event_df.pivot_table(
                    values='Avg Bandwidth [GB/s]',
                    index='Experiment',
                    aggfunc='first'
                )
                print(pivot.to_string())
        
        # Save combined results
        output_file = f"combined_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        summary_df.to_csv(output_file, index=False, float_format='%.2f')
        print(f"\n✓ Combined results saved to: {output_file}")
        
        # Create comparison table
        comparison_file = f"comparison_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create a cleaner comparison focusing on dispatch+combine
        dispatch_combine_df = summary_df[summary_df['Event'] == 'dispatch + combine']
        if not dispatch_combine_df.empty:
            comparison = dispatch_combine_df[['Experiment', 'GPU Configuration', 
                                             'Imbalance test', 'Avg Bandwidth [GB/s]']]
            comparison.to_csv(comparison_file, index=False, float_format='%.2f')
            print(f"✓ Comparison table saved to: {comparison_file}")
            
            print("\n" + "=" * 60)
            print("EXPERIMENT COMPARISON (Dispatch + Combine)")
            print("=" * 60)
            print(comparison.to_string(index=False))
        
        return summary_df
    else:
        print("No data could be extracted from the CSV files")
        return None


def create_latex_table(df, output_file="results_table.tex"):
    """
    Create a LaTeX table from the results
    """
    if df is None or df.empty:
        return
    
    # Filter for dispatch + combine only
    table_df = df[df['Event'] == 'dispatch + combine'].copy()
    
    if table_df.empty:
        print("No 'dispatch + combine' data found for LaTeX table")
        return
    
    # Simplify column names for LaTeX
    table_df = table_df[['Experiment', 'GPU Configuration', 'Imbalance test', 'Avg Bandwidth [GB/s]']]
    
    # Convert to LaTeX
    latex = table_df.to_latex(index=False, float_format='%.2f', escape=False)
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(latex)
    
    print(f"\n✓ LaTeX table saved to: {output_file}")


if __name__ == "__main__":
    # Check for custom pattern
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
    else:
        pattern = "results_*.csv"
    
    # Combine results
    combined_df = combine_results(pattern)
    
    # Create LaTeX table if requested
    if combined_df is not None and "--latex" in sys.argv:
        create_latex_table(combined_df)

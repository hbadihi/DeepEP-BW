#!/usr/bin/env python3
"""
Standalone script to create combined CSV tables from experiment results
Can be used to regenerate tables from existing result files
"""

import pandas as pd
import glob
import os
import sys
from datetime import datetime


def create_combined_tables_from_pattern(pattern="results_*.csv"):
    """
    Create 5 combined CSV tables from result files matching the pattern
    
    Args:
        pattern: Glob pattern to match result files
    
    Returns:
        List of created files
    """
    # Find all matching CSV files
    result_files = glob.glob(pattern)
    
    if not result_files:
        print(f"No files found matching pattern: {pattern}")
        return []
    
    print(f"Found {len(result_files)} result files:")
    for f in result_files:
        print(f"  - {f}")
    
    # Read all result files
    all_data = []
    
    for filename in result_files:
        # Extract experiment name from filename
        # Format: results_EXPNAME_TIMESTAMP.csv
        basename = os.path.basename(filename)
        parts = basename.replace("results_", "").replace(".csv", "")
        
        # Try to extract experiment name (everything before the timestamp)
        # Assuming timestamp format is YYYYMMDD_HHMMSS
        import re
        match = re.match(r'(.+?)_\d{8}_\d{6}', parts)
        if match:
            exp_name = match.group(1)
        else:
            exp_name = parts.split('_')[0] if '_' in parts else parts
        
        try:
            df = pd.read_csv(filename)
            # Add experiment name if not already present
            if 'Experiment' not in df.columns:
                df['Experiment'] = exp_name
            all_data.append(df)
            print(f"  ✓ Loaded {exp_name}: {len(df)} rows")
        except Exception as e:
            print(f"  ✗ Error reading {filename}: {e}")
    
    if not all_data:
        print("No data could be loaded")
        return []
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal combined rows: {len(combined_df)}")
    
    # Create timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define the 5 tables to create
    tables = [
        ("dispatch_combine", "dispatch + combine", "Dispatch + Combine Performance"),
        ("combine_only", "combine", "Combine Only Performance"),
        ("dispatch_only", "dispatch", "Dispatch Only Performance"),
        ("combine_send_recv", ["combine send", "combine recv"], "Combine Send/Recv Times"),
        ("dispatch_send_recv", ["dispatch send", "dispatch recv"], "Dispatch Send/Recv Times")
    ]
    
    print("\n" + "=" * 80)
    print("CREATING COMBINED TABLES")
    print("=" * 80)
    
    created_files = []
    
    for table_name, event_filter, description in tables:
        print(f"\n{description}:")
        print("-" * 40)
        
        # Filter data for specific events
        if isinstance(event_filter, list):
            # Multiple events (for send/recv tables)
            filtered_df = combined_df[combined_df['Event'].isin(event_filter)]
        else:
            # Single event
            filtered_df = combined_df[combined_df['Event'] == event_filter]
        
        if not filtered_df.empty:
            # Common columns to keep
            base_columns = ['Experiment', 'Event', 'GPU Configuration', 'Imbalance test',
                           'avg bandwidth [GB/s]', 'avg_t [us]', 'Std deviation [GB/s]']
            
            # Add send/recv columns if they exist
            if 'avg_t_send [us]' in filtered_df.columns:
                base_columns.insert(6, 'avg_t_send [us]')
            if 'avg_t_recv [us]' in filtered_df.columns:
                base_columns.insert(7, 'avg_t_recv [us]')
            
            # Add rank columns if they exist
            rank_columns = []
            for i in range(8):
                col = f'Avg. rank{i} BW [GB/s]'
                if col in filtered_df.columns:
                    rank_columns.append(col)
            
            all_columns = base_columns + rank_columns
            
            # Select only available columns
            available_cols = [col for col in all_columns if col in filtered_df.columns]
            filtered_df = filtered_df[available_cols]
            
            # Sort appropriately
            if isinstance(event_filter, list):
                filtered_df = filtered_df.sort_values(['Experiment', 'Event'])
            else:
                filtered_df = filtered_df.sort_values(['Imbalance test', 'Experiment'])
            
            # Save main table
            output_file = f"combined_{table_name}_{timestamp}.csv"
            filtered_df.to_csv(output_file, index=False, float_format='%.2f')
            created_files.append(output_file)
            
            print(f"✓ Created: {output_file}")
            print(f"  Rows: {len(filtered_df)}")
            print(f"  Experiments: {filtered_df['Experiment'].nunique()}")
            
            # For single event tables, create a comparison matrix
            if not isinstance(event_filter, list):
                create_comparison_matrix(filtered_df, table_name, timestamp, description)
            
            # Print preview
            if len(filtered_df) > 0:
                print("\n  Preview (first 3 rows):")
                preview_cols = ['Experiment', 'GPU Configuration', 'Imbalance test', 
                               'avg bandwidth [GB/s]', 'avg_t [us]']
                preview_cols = [c for c in preview_cols if c in filtered_df.columns]
                print(filtered_df[preview_cols].head(3).to_string(index=False))
        else:
            print(f"⚠ No data found for {description}")
    
    # Create master file with all events
    master_file = f"combined_all_events_{timestamp}.csv"
    combined_df.to_csv(master_file, index=False, float_format='%.2f')
    created_files.append(master_file)
    
    print("\n" + "=" * 80)
    print("MASTER FILE")
    print("=" * 80)
    print(f"✓ Created: {master_file}")
    print(f"  Total rows: {len(combined_df)}")
    print(f"  Event types: {combined_df['Event'].nunique()}")
    print(f"  Experiments: {combined_df['Experiment'].nunique()}")
    
    # Create summary statistics
    create_summary_report(combined_df, timestamp)
    
    return created_files


def create_comparison_matrix(df, table_name, timestamp, description):
    """
    Create a comparison matrix showing bandwidth across experiments
    """
    # Create pivot table
    comparison_file = f"comparison_{table_name}_{timestamp}.csv"
    
    # Separate by imbalance test
    comparison_data = []
    
    for imbalance in [False, True]:
        subset = df[df['Imbalance test'] == imbalance]
        if not subset.empty:
            for _, row in subset.iterrows():
                comparison_data.append({
                    'Experiment': row['Experiment'],
                    'GPU Config': row['GPU Configuration'],
                    'Imbalanced': 'Yes' if imbalance else 'No',
                    'Bandwidth [GB/s]': row['avg bandwidth [GB/s]'],
                    'Time [us]': row['avg_t [us]'],
                    'Std Dev [GB/s]': row['Std deviation [GB/s]']
                })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_csv(comparison_file, index=False, float_format='%.2f')
        print(f"  ✓ Comparison matrix: {comparison_file}")


def create_summary_report(df, timestamp):
    """
    Create a comprehensive summary report
    """
    report_file = f"performance_summary_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PERFORMANCE SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 40 + "\n")
        
        dispatch_combine = df[df['Event'] == 'dispatch + combine']
        if not dispatch_combine.empty:
            f.write(f"Average Bandwidth (all experiments): {dispatch_combine['avg bandwidth [GB/s]'].mean():.2f} GB/s\n")
            f.write(f"Std Dev Bandwidth: {dispatch_combine['avg bandwidth [GB/s]'].std():.2f} GB/s\n")
            f.write(f"Min Bandwidth: {dispatch_combine['avg bandwidth [GB/s]'].min():.2f} GB/s\n")
            f.write(f"Max Bandwidth: {dispatch_combine['avg bandwidth [GB/s]'].max():.2f} GB/s\n")
            
            # Compare with and without imbalance
            normal = dispatch_combine[dispatch_combine['Imbalance test'] == False]
            imbalanced = dispatch_combine[dispatch_combine['Imbalance test'] == True]
            
            if not normal.empty and not imbalanced.empty:
                f.write(f"\nWithout Imbalance: {normal['avg bandwidth [GB/s]'].mean():.2f} GB/s\n")
                f.write(f"With Imbalance: {imbalanced['avg bandwidth [GB/s]'].mean():.2f} GB/s\n")
                
                perf_impact = ((normal['avg bandwidth [GB/s]'].mean() - imbalanced['avg bandwidth [GB/s]'].mean()) 
                              / normal['avg bandwidth [GB/s]'].mean() * 100)
                f.write(f"Imbalance Impact: {perf_impact:.1f}% degradation\n")
        
        # Per-event summary
        f.write("\n\nPER-EVENT SUMMARY\n")
        f.write("-" * 40 + "\n")
        
        for event in df['Event'].unique():
            event_data = df[df['Event'] == event]
            f.write(f"\n{event}:\n")
            f.write(f"  Avg Bandwidth: {event_data['avg bandwidth [GB/s]'].mean():.2f} GB/s\n")
            f.write(f"  Avg Time: {event_data['avg_t [us]'].mean():.2f} us\n")
            
            # Check for send/recv specific times
            if 'avg_t_send [us]' in event_data.columns and event_data['avg_t_send [us]'].sum() > 0:
                f.write(f"  Avg Send Time: {event_data['avg_t_send [us]'].mean():.2f} us\n")
            if 'avg_t_recv [us]' in event_data.columns and event_data['avg_t_recv [us]'].sum() > 0:
                f.write(f"  Avg Recv Time: {event_data['avg_t_recv [us]'].mean():.2f} us\n")
        
        # Per-experiment summary
        f.write("\n\nPER-EXPERIMENT SUMMARY (Dispatch + Combine)\n")
        f.write("-" * 40 + "\n")
        
        if not dispatch_combine.empty:
            for exp in sorted(dispatch_combine['Experiment'].unique()):
                exp_data = dispatch_combine[dispatch_combine['Experiment'] == exp]
                f.write(f"\n{exp}:\n")
                for _, row in exp_data.iterrows():
                    imb_status = "Imbalanced" if row['Imbalance test'] else "Normal"
                    f.write(f"  {imb_status}: {row['avg bandwidth [GB/s]']:.2f} GB/s, ")
                    f.write(f"{row['avg_t [us]']:.2f} us\n")
    
    print(f"\n✓ Performance summary report: {report_file}")


def main():
    """
    Main function
    """
    print("=" * 80)
    print("COMBINED TABLE GENERATOR")
    print("=" * 80)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        print(f"Using pattern: {pattern}")
    else:
        pattern = "results_*.csv"
        print(f"Using default pattern: {pattern}")
    
    # Create combined tables
    created_files = create_combined_tables_from_pattern(pattern)
    
    if created_files:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Successfully created {len(created_files)} files:")
        for f in created_files:
            if os.path.exists(f):
                size = os.path.getsize(f) / 1024  # KB
                print(f"  - {f} ({size:.1f} KB)")
    else:
        print("\nNo files were created.")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pyarrow as pa

def load_data(path: str) -> pd.DataFrame:
    """Loads people_trip data from Arrow (Stream or File)."""
    print(f"Loading data from {path}...")
    try:
        with pa.ipc.open_stream(path) as reader:
            df = reader.read_all().to_pandas()
        print(f"Loaded {len(df)} rows (Stream).")
        if 'drawmode' not in df.columns and 'mainMode' in df.columns:
            df['drawmode'] = df['mainMode']
        return df
    except Exception:
        try:
            df = pd.read_feather(path)
            print(f"Loaded {len(df)} rows (File).")
            if 'drawmode' not in df.columns and 'mainMode' in df.columns:
                df['drawmode'] = df['mainMode']
            return df
        except Exception as e:
            print(f"Failed to load {path}: {e}")
            return pd.DataFrame()

def prepare_od_metrics(df: pd.DataFrame, top_od_pairs: list = None, top_k: int = 10) -> pd.DataFrame:
    """
    Calculates metrics for OD pairs:
    - Total Trips
    - Bus Trips, Car Trips
    - Bus Share (%)
    - Avg Travel Time Bus
    - Avg Travel Time Car
    """
    # Ensure cols
    if 'drawmode' not in df.columns:
        df['drawmode'] = df['mainMode'] if 'mainMode' in df.columns else 'unknown'
        
    if 'travelTime' in df.columns:
        df['travelTime'] = pd.to_numeric(df['travelTime'], errors='coerce')

    # Filter valid OD
    valid_df = df[(df['OZone'] != 'undefined') & (df['DZone'] != 'undefined')].copy()
    
    # 1. Identify Top OD if not provided
    if top_od_pairs is None:
        od_counts = valid_df.groupby(['OZone', 'DZone']).size().reset_index(name='count').sort_values('count', ascending=False)
        top_od_pairs = list(zip(od_counts['OZone'], od_counts['DZone']))[:top_k]
    
    # 2. Calculate Metrics per OD
    metrics = []
    for o, d in top_od_pairs:
        subset = valid_df[(valid_df['OZone'] == o) & (valid_df['DZone'] == d)]
        total = len(subset)
        if total == 0:
            continue
            
        # Modes
        modes = subset['drawmode'].value_counts()
        bus_count = modes.get('bus', 0) + modes.get('pt', 0) # Handle 'pt' as bus if needed
        car_count = modes.get('car', 0)
        
        bus_share = (bus_count / total) * 100
        car_share = (car_count / total) * 100
        
        # Times
        avg_time_bus = subset[subset['drawmode'].isin(['bus', 'pt'])]['travelTime'].mean()
        avg_time_car = subset[subset['drawmode'] == 'car']['travelTime'].mean()
        
        metrics.append({
            'OD': f"{o}->{d}",
            'Total Trips': total,
            'Bus Trips': bus_count,
            'Car Trips': car_count,
            'Bus Share (%)': bus_share,
            'Avg Time Bus (s)': avg_time_bus,
            'Avg Time Car (s)': avg_time_car,
            'Car Share (%)': car_share
        })
        
    return pd.DataFrame(metrics)

def plot_scenario_comparison(scenarios: list, output_folder: str, top_k: int = 10):
    """
    scenarios: List of tuples (ScenarioName, DataFrame)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Determine Top OD pairs from the BASELINE (first scenario)
    base_name, base_df = scenarios[0]
    print(f"Identifying Top {top_k} OD pairs based on '{base_name}'...")
    
    # Helper to get OD list
    temp_valid = base_df[(base_df['OZone'] != 'undefined') & (base_df['DZone'] != 'undefined')]
    od_counts = temp_valid.groupby(['OZone', 'DZone']).size().reset_index(name='count').sort_values('count', ascending=False)
    top_od_tuples = list(zip(od_counts['OZone'], od_counts['DZone']))[:top_k]
    
    # 2. Compute Metrics for ALL scenarios using these OD pairs
    combined_data = []
    
    for name, df in scenarios:
        metrics_df = prepare_od_metrics(df, top_od_pairs=top_od_tuples)
        metrics_df['Scenario'] = name
        combined_data.append(metrics_df)
        
    final_df = pd.concat(combined_data, ignore_index=True)
    
    # 3. Plotting
    # Set style
    sns.set_style("whitegrid")
    
    # Figure: 3 Subplots (Bus Share, Avg Time Bus, Avg Time Car)
    # Figure: 4 Subplots - Added Bus/(Bus+Car) Share
    fig, axes = plt.subplots(4, 1, figsize=(14, 24))
    fig.suptitle(f"COMPARISON ANALYSIS: TOP {top_k} OD PAIRS", fontsize=20, fontweight='bold', y=0.99)

    
    # A. Bus Share (%)
    sns.barplot(data=final_df, x='OD', y='Bus Share (%)', hue='Scenario', ax=axes[0], palette='viridis')
    axes[0].set_title("Bus Mode Share (%) per OD Pair", fontsize=15)
    axes[0].set_ylabel("Share (%)")
    axes[0].legend(loc='upper right')
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt='%.1f', padding=3)

    # D. Car Share (%)
    sns.barplot(data=final_df, x='OD', y='Car Share (%)', hue='Scenario', ax=axes[1], palette='cubehelix')
    axes[1].set_title("Car Mode Share (%) per OD Pair", fontsize=15)
    axes[1].set_ylabel("Share (%)")
    for container in axes[1].containers:
         axes[1].bar_label(container, fmt='%.1f', padding=3)

    # B. Avg Travel Time (Bus)
    sns.barplot(data=final_df, x='OD', y='Avg Time Bus (s)', hue='Scenario', ax=axes[2], palette='magma')
    axes[2].set_title("Average Travel Time: BUS (s)", fontsize=15)
    axes[2].set_ylabel("Time (seconds)")
    for container in axes[2].containers:
         axes[2].bar_label(container, fmt='%.0f', padding=3)
    
    # C. Avg Travel Time (Car)
    sns.barplot(data=final_df, x='OD', y='Avg Time Car (s)', hue='Scenario', ax=axes[3], palette='coolwarm')
    axes[3].set_title("Average Travel Time: CAR (s)", fontsize=15)
    axes[3].set_ylabel("Time (seconds)")
    for container in axes[3].containers:
         axes[3].bar_label(container, fmt='%.0f', padding=3)


   

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    
    out_file = os.path.join(output_folder, "OD_Scenario_Comparison.png")
    plt.savefig(out_file, dpi=150)
    plt.close()
    print(f"Comparison plot saved to: {out_file}")



if __name__ == "__main__":
    from src.data.load_config import load_config
    
    # Config
    path_config = load_config(r"config/config_path.yaml")
    
    # Example: User only has ONE arrow file right now.
    # To demonstrate, we will load the SAME file twice but label them differently 
    # (e.g., "Baseline" vs "Mock Optimized").
    # In a real run, you would point `path2` to the new arrow file.
    
    path1 = path_config.data.interim.event.people_trip
    # path2 = "path/to/optimized/people_trip.arrow" 
    
    # Load
    df1 = load_data(path1)
    
    # Creating a Mock Data for demonstration if DF1 loaded
    # (Delete this block in production and load actul 2nd file)
    scenarios_list = []
    if not df1.empty:
        scenarios_list.append(("Baseline", df1))
        
        # MOCKING 2nd Scenario for DEMO: Reduce car time by 10%, increase bus share arbitrarily
        df2 = df1.copy()
        df2['travelTime'] = pd.to_numeric(df2['travelTime'], errors='coerce')
        
        # Reduce car travel time
        mask_car = df2['drawmode'] == 'car'
        df2.loc[mask_car, 'travelTime'] = df2.loc[mask_car, 'travelTime'] * 0.9
        
        # Artificial Bus Mode Shift (change some car to bus)
        # Randomly sample 10% of rows and force them to bus
        df2.loc[df2.sample(frac=0.1).index, 'drawmode'] = 'bus'
        
        scenarios_list.append(("Optimized (Demo)", df2))
        
    output_folder = r"data/visualize/comparison"
    
    plot_scenario_comparison(scenarios_list, output_folder, top_k=10)
    
    # python -m src.visualize.od_compare

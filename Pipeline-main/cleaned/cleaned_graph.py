import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score

# --- Configuration ---
DETECTION_FILES = [
    r"E:\processed_data\acoustic_biodiversity\analysis\audio_raw_spot_1_original_spot_20072025-29072025_2R4W_birdnet_classification.csv",
    r"E:\processed_data\acoustic_biodiversity\analysis\audio_raw_spot_2_peacock_spot_20072025-03082025_2R4W_birdnet_classification.csv",
    r"E:\processed_data\acoustic_biodiversity\analysis\audio_raw_spot_3_investigation_spot_20072025-03082025_2R4W_birdnet_classification.csv",
    r"E:\processed_data\acoustic_biodiversity\analysis\audio_raw_spot_4_yoga_spot_20072025-03082025_2R4W_birdnet_classification.csv"
]
INDEX_FILES = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\results.csv"
]
COMBINED_INDICES_SAVE_PATH = r"E:\processed_data\acoustic_biodiversity\analysis\combined_indices.csv"

# --- Helper Functions ---
def compute_shannon_simpson(labels):
    counts = labels.value_counts()
    props = counts / len(labels)
    shannon = -np.sum(props[props > 0] * np.log2(props[props > 0]))

    n = len(labels)
    if n < 2:
        return shannon, np.nan
    simpson = 1 - (np.sum(counts * (counts - 1)) / (n * (n - 1)))
    return shannon, simpson

def bootstrap_spearman(df, col_x, col_y, n_iterations=1000):
    r_values = []
    for _ in range(n_iterations):
        sample = df.sample(frac=1, replace=True)
        r, _ = spearmanr(sample[col_x], sample[col_y])
        r_values.append(r)
    r_values = np.array(r_values)
    return np.mean(r_values), np.percentile(r_values, 2.5), np.percentile(r_values, 97.5)

# --- 1. Data Loading and Preprocessing ---
def load_and_preprocess_data(detection_files, index_files):
    detections_df = pd.concat([pd.read_csv(f) for f in detection_files], ignore_index=True)
    indices_df = pd.concat([pd.read_csv(f) for f in index_files], ignore_index=True)

    detections_df['filename'] = detections_df['filename'].str.replace("STOP", "SPOT", regex=False)
    indices_df.rename(columns={'Filename': 'filename'}, inplace=True)

    detections_df['Spot'] = detections_df['filename'].str.extract(r'(SPOT\d+)', expand=False).str.lower().str.replace('spot', 'spot_')
    date_info = detections_df['filename'].str.extract(r'_(\d{8})_')
    detections_df['Date'] = pd.to_datetime(date_info[0], format='%Y%m%d')
    detections_df.dropna(subset=['Spot', 'Date'], inplace=True)

    return detections_df, indices_df

# --- 2. Behavioral Stickiness Analysis ---
def analyze_stickiness(df):
    activity_df = df[(df['confidence'] >= 0.5) & (df['hour'].between(5, 19))].copy()
    species_list = activity_df['label'].unique()
    spot_list = sorted(activity_df['Spot'].unique())
    date_list = sorted(activity_df['Date'].unique())
    num_days = activity_df['Date'].nunique()

    # Temporal Stickiness
    temporal_stickiness = {}
    for species in species_list:
        corrs = []
        for spot in spot_list:
            spot_day_corrs = []
            for i in range(len(date_list) - 1):
                series_k = activity_df[(activity_df['label'] == species) & (activity_df['Spot'] == spot) & (activity_df['Date'] == date_list[i])]['hour'].value_counts().reindex(range(5, 20), fill_value=0)
                series_k1 = activity_df[(activity_df['label'] == species) & (activity_df['Spot'] == spot) & (activity_df['Date'] == date_list[i+1])]['hour'].value_counts().reindex(range(5, 20), fill_value=0)
                if series_k.sum() > 0 and series_k1.sum() > 0:
                    corr, _ = spearmanr(series_k, series_k1)
                    spot_day_corrs.append(corr)
            if spot_day_corrs:
                corrs.append(np.mean(spot_day_corrs))
        if corrs:
            temporal_stickiness[species] = np.mean(corrs)
    temporal_df = pd.DataFrame(list(temporal_stickiness.items()), columns=['label', 'Temporal_Stickiness']).sort_values('Temporal_Stickiness', ascending=False)

    # Spatial Stickiness
    spatial_stickiness = {}
    if len(spot_list) >= 2:
        for species in species_list:
            daily_corrs = []
            for i in range(len(date_list) - 1):
                counts_k = activity_df[(activity_df['label'] == species) & (activity_df['Date'] == date_list[i])].groupby('Spot').size().reindex(spot_list, fill_value=0)
                counts_k1 = activity_df[(activity_df['label'] == species) & (activity_df['Date'] == date_list[i+1])].groupby('Spot').size().reindex(spot_list, fill_value=0)
                if counts_k.nunique() > 1 and counts_k1.nunique() > 1:
                    corr, _ = spearmanr(counts_k, counts_k1)
                    if not np.isnan(corr):
                        daily_corrs.append(corr)
            if daily_corrs:
                spatial_stickiness[species] = np.mean(daily_corrs)
    spatial_df = pd.DataFrame(list(spatial_stickiness.items()), columns=['label', 'Spatial_Stickiness']).sort_values('Spatial_Stickiness', ascending=False)
    
    return temporal_df, spatial_df, activity_df, num_days

# --- 3. Index Calculation & Merging ---
def calculate_and_merge_indices(detections_df, indices_df, save_path):
    diversity_df = detections_df[detections_df['confidence'] >= 0.5].groupby('filename').agg(
        Shannon_Simpson=('label', lambda x: compute_shannon_simpson(x)),
        Spot=('Spot', 'first'),
        Date=('Date', 'first')
    ).reset_index()
    diversity_df[['Shannon', 'Simpson']] = pd.DataFrame(diversity_df['Shannon_Simpson'].tolist(), index=diversity_df.index)
    diversity_df.drop(columns=['Shannon_Simpson'], inplace=True)
    
    agg_indices_df = indices_df.groupby('filename').agg(
        ADI_mean=('ADI', 'mean'), ADI_std=('ADI', 'std'),
        ACI_mean=('ACI', 'mean'), ACI_std=('ACI', 'std'),
        AEI_mean=('AEI', 'mean'), AEI_std=('AEI', 'std'),
        NDSI_mean=('NDSI', 'mean'), NDSI_std=('NDSI', 'std'),
        MFC_mean=('MFC', 'mean'), MFC_std=('MFC', 'std'),
        CLS_mean=('CLS', 'mean'), CLS_std=('CLS', 'std')
    ).reset_index().fillna(0)

    combined_df = pd.merge(diversity_df, agg_indices_df, on='filename', how='inner')
    combined_df.to_csv(save_path, index=False)
    return combined_df

# --- 4. Visualization Functions ---
def plot_stickiness(temporal_df, spatial_df, activity_df, num_days):
    # Temporal Stickiness vs. Call Volume
    top_temporal = temporal_df.head(40)
    avg_calls = activity_df[activity_df["label"].isin(top_temporal["label"])].groupby("label").size().reset_index(name="total_calls")
    avg_calls["Avg_Calls_Per_Day"] = avg_calls["total_calls"] / num_days
    avg_calls = avg_calls.set_index("label").reindex(top_temporal["label"]).fillna(0).reset_index()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 10))
    sns.barplot(x='Temporal_Stickiness', y='label', data=top_temporal, palette='plasma', ax=ax1)
    ax1.set_title('Top 40 Species by Temporal Stickiness')
    sns.barplot(x="Avg_Calls_Per_Day", y="label", data=avg_calls, palette="magma", ax=ax2)
    ax2.set_title('Average Daily Call Volume of Top Species')
    ax2.tick_params(axis='y', which='both', left=False, labelleft=False)
    plt.tight_layout()
    plt.show()

    # Spatial Stickiness & Activity Heatmap
    top_spatial = spatial_df.head(80)
    fig, axes = plt.subplots(1, 2, figsize=(20, 12), sharex=True)
    sns.barplot(x='Spatial_Stickiness', y='label', data=top_spatial.head(40), palette='viridis', ax=axes[0])
    axes[0].set_title("Top 40 Species by Spatial Stickiness")
    sns.barplot(x='Spatial_Stickiness', y='label', data=top_spatial.iloc[40:80], palette='viridis', ax=axes[1])
    axes[1].set_title("Next 40 Species by Spatial Stickiness")
    plt.tight_layout()
    plt.show()

    avg_calls_per_spot = activity_df.groupby(['label', 'Spot'])['Date'].nunique().reset_index(name='days_active')
    avg_calls_per_spot = activity_df.groupby(['label', 'Spot']).size().reset_index(name='total_calls').merge(avg_calls_per_spot)
    avg_calls_per_spot['avg_daily_calls'] = avg_calls_per_spot['total_calls'] / avg_calls_per_spot['days_active']
    heatmap_data = avg_calls_per_spot.pivot_table(index='label', columns='Spot', values='avg_daily_calls', fill_value=0)
    aligned_heatmap_data = heatmap_data.reindex(top_spatial['label'].tolist()).fillna(0)
    log_heatmap_data = np.log1p(aligned_heatmap_data)

    fig, axes = plt.subplots(1, 2, figsize=(16, 12))
    sns.heatmap(log_heatmap_data.iloc[0:40], cmap='YlGnBu', ax=axes[0])
    axes[0].set_title('Bird Activity (Top 40 by Stickiness)')
    sns.heatmap(log_heatmap_data.iloc[40:80], cmap='YlGnBu', ax=axes[1])
    axes[1].set_title('Bird Activity (Next 40 by Stickiness)')
    plt.show()

def plot_spot_activity_heatmaps(df, normalized=False):
    activity_df = df[(df['confidence'] >= 0.5) & (~df['label'].str.contains("Engine|Siren", na=False))].copy()
    for spot in sorted(activity_df['Spot'].unique()):
        spot_df = activity_df[activity_df['Spot'] == spot]
        num_days = spot_df['Date'].nunique()
        if num_days == 0: continue
        top_species = spot_df['label'].value_counts().nlargest(25).index
        pivot = spot_df[spot_df['label'].isin(top_species)].pivot_table(index='label', columns='hour', values='filename', aggfunc='count', fill_value=0) / num_days
        
        if normalized:
            pivot = pivot.div(pivot.sum(axis=1), axis=0)
            title = f"Normalized Hourly Activity for {spot.replace('_', ' ').title()}"
            cbar_label = 'Proportion of Daily Activity'
        else:
            title = f"Average Detections per Hour for {spot.replace('_', ' ').title()}"
            cbar_label = 'Avg. Detections per Hour'

        plt.figure(figsize=(20, 10))
        sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".2f", cbar_kws={'label': cbar_label})
        plt.title(title)
        plt.show()

def plot_index_correlations(df, biodiversity_metric='Shannon'):
    indices = ['ADI', 'ACI', 'AEI', 'NDSI', 'MFC', 'CLS']
    results = [{'Index': idx, **dict(zip(['Mean_r', 'CI_lower', 'CI_upper'], bootstrap_spearman(df, idx, biodiversity_metric)))} for idx in indices]
    corr_df = pd.DataFrame(results).sort_values('Mean_r')
    
    plt.figure(figsize=(10, 7))
    plt.errorbar(corr_df['Mean_r'], corr_df['Index'], xerr=[corr_df['Mean_r'] - corr_df['CI_lower'], corr_df['CI_upper'] - corr_df['Mean_r']],
                 fmt='o', color='darkslateblue', capsize=5)
    plt.axvline(0, color='gray', linestyle='--')
    plt.title(f"Correlation of Acoustic Indices with Avian Diversity ({biodiversity_metric})")
    plt.show()

def plot_index_distributions(df):
    plot_indices = ['Shannon', 'CLS', 'ACI', 'MFC']
    for index in plot_indices:
        if index in df.columns:
            plt.figure(figsize=(10, 6))
            sns.boxplot(data=df, x='Spot', y=index, order=sorted(df['Spot'].unique()))
            plt.title(f'Distribution of {index} Across Monitoring Spots')
            plt.show()

# --- 5. Modeling ---
def run_regression_models(df):
    features = [
        'ADI_mean', 'ADI_std', 'ACI_mean', 'ACI_std', 'AEI_mean', 'AEI_std',
        'NDSI_mean', 'NDSI_std', 'MFC_mean', 'MFC_std', 'CLS_mean', 'CLS_std'
    ]
    target = 'Shannon'
    model_df = df.dropna(subset=[target] + features)
    if len(model_df) < 20:
        print("Not enough data for robust model training.")
        return

    X = model_df[features]
    y = model_df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Gradient Boosting Regressor with GridSearchCV
    gb_model = GradientBoostingRegressor(random_state=42)
    param_grid_gb = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [3, 5, 7]}
    grid_search_gb = GridSearchCV(estimator=gb_model, param_grid=param_grid_gb, cv=5, scoring='r2', n_jobs=-1)
    grid_search_gb.fit(X_train, y_train)
    best_gb = grid_search_gb.best_estimator_
    
    print("--- Optimized Gradient Boosting Regressor Results ---")
    print(f"Best parameters: {grid_search_gb.best_params_}")
    print(f"Train R² = {r2_score(y_train, best_gb.predict(X_train)):.4f}")
    print(f"Test R²  = {r2_score(y_test, best_gb.predict(X_test)):.4f}")
    
    importances = pd.DataFrame({'Feature': features, 'Importance': best_gb.feature_importances_}).sort_values('Importance', ascending=False)
    print("\nFeature Importances:\n", importances)

# --- Main Execution ---
if __name__ == '__main__':
    detections, indices = load_and_preprocess_data(DETECTION_FILES, INDEX_FILES)
    
    # Part 3: Behavioral Stickiness
    temporal_stickiness_df, spatial_stickiness_df, activity_df, num_days = analyze_stickiness(detections)
    plot_stickiness(temporal_stickiness_df, spatial_stickiness_df, activity_df, num_days)

    # Part 4: Spot-wise Activity Heatmaps
    plot_spot_activity_heatmaps(detections, normalized=False)
    plot_spot_activity_heatmaps(detections, normalized=True)

    # Part 5: Acoustic & Biodiversity Index Analysis
    combined_indices_df = calculate_and_merge_indices(detections, indices, COMBINED_INDICES_SAVE_PATH)
    if not combined_indices_df.empty:
        plot_index_correlations(combined_indices_df, 'Shannon')
        plot_index_correlations(combined_indices_df, 'Simpson')
        plot_index_distributions(combined_indices_df)
    
        # Part 6: Regression Analysis
        run_regression_models(combined_indices_df)
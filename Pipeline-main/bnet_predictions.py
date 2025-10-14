# %%
import os
import re
import sys
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import soundfile as sf
import tensorflow as tf
from collections import defaultdict
from scipy.special import softmax
from scipy.stats import entropy
from scipy.signal import spectrogram
import gc

# %%
results_combined = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\results.csv", r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\results.csv", r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\results.csv", r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\results.csv"]

# %%
# NOT SURE IF NEEDED ANYMORE, now that we use a library directly
# -------------------- Load GPU Delegate --------------------
delegate = None
try:
    import tflite_runtime.interpreter as tflite
except ModuleNotFoundError:
    from tensorflow import lite as tflite

try:
    delegate = tf.lite.experimental.load_delegate("libtensorflowlite_gpu_delegate.so")
    print("GPU delegate loaded successfully.")
except Exception as e:
    print("GPU delegate not available:", e)

# -------------------- Patch Interpreter BEFORE importing wrapper --------------------
if not hasattr(tflite, "_original_interpreter"):
    tflite._original_interpreter = tflite.Interpreter

    def Interpreter_with_delegate(*args, **kwargs):
        if delegate is not None:
            kwargs["experimental_delegates"] = [delegate]
        return tflite._original_interpreter(*args, **kwargs)

    tflite.Interpreter = Interpreter_with_delegate

# %% [markdown]
# 

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os

# -------------------- Step 1: Data Consolidation --------------------
all_data = []
for i, file_path in enumerate(results_combined):
    df_spot = pd.read_csv(file_path)
    # Add a 'Spot' column to identify the source of the data
    df_spot['Spot'] = f'Spot {i+1}'
    all_data.append(df_spot)

# Concatenate all DataFrames into a single master DataFrame
master_df = pd.concat(all_data, ignore_index=True)

# -------------------- Step 2: Segment Mapping --------------------
def map_to_segment(hour):
    if 21 <= hour or hour < 5:
        return 'Night'
    elif 5 <= hour < 10:
        return 'Morning'
    elif 10 <= hour < 17:
        return 'Day'
    else:  # 17 to 21
        return 'Evening'

master_df['Segment'] = master_df['Hour'].apply(map_to_segment)

# -------------------- Step 3: Aggregation for PCA --------------------
acoustic_indices = ['ADI', 'ACI', 'AEI', 'NDSI', 'CLS']

df_pca = master_df.groupby(['Spot', 'Segment'])[acoustic_indices].mean().reset_index()

print("Aggregated Data for PCA:")
print(df_pca)
print("\n")

# -------------------- Step 4: Scaling and PCA --------------------
features = df_pca[acoustic_indices]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

pca = PCA(n_components=2)
principal_components = pca.fit_transform(scaled_features)

pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'])

# -------------------- Step 5: Combining and Visualization --------------------
final_pca_df = pd.concat([df_pca[['Spot', 'Segment']], pca_df], axis=1)

print("Final PCA Results:")
print(final_pca_df)

# Visualization of PCA results
plt.figure(figsize=(10, 8))
sns.scatterplot(
    data=final_pca_df,
    x='PC1',
    y='PC2',
    hue='Spot',        # Color points by Spot
    style='Segment',   # Differentiate markers by Time Segment
    s=150,             # Set marker size
    palette='viridis'  # Choose a color palette
)

plt.title('PCA of Acoustic Indices by Spot and Time Segment')
plt.xlabel('Principal Component 1 (PC1)')
plt.ylabel('Principal Component 2 (PC2)')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# Optional: Explained variance plot to choose number of components
pca_full = PCA()
pca_full.fit(scaled_features)
explained_variance = pca_full.explained_variance_ratio_

plt.figure(figsize=(8, 6))
plt.plot(np.cumsum(explained_variance), marker='o', linestyle='--')
plt.title('Explained Variance vs. Number of Components')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.grid(True, linestyle='--', alpha=0.6)
plt.axhline(y=0.95, color='r', linestyle='-', label='95% Cutoff')
plt.legend()
plt.show()


# %%
# -------------------- Step 1: Data Consolidation --------------------
all_data = []
for i, file_path in enumerate(results_combined):
    df_spot = pd.read_csv(file_path)
    # Add a 'Spot' column to identify the source of the data
    df_spot['Spot'] = f'Spot {i+1}'
    all_data.append(df_spot)

master_df = pd.concat(all_data, ignore_index=True)

# -------------------- Step 2: Segment Mapping --------------------
def map_to_segment(hour):
    if 21 <= hour or hour < 5:
        return 'Night'
    elif 5 <= hour < 10:
        return 'Morning'
    elif 10 <= hour < 17:
        return 'Day'
    else:  # 17 to 21
        return 'Evening'

master_df['Segment'] = master_df['Hour'].apply(map_to_segment)

# -------------------- Step 3: Aggregation for PCA --------------------
acoustic_indices = ['ADI', 'ACI', 'AEI', 'NDSI', 'CLS']
df_pca = master_df.groupby(['Spot', 'Segment'])[acoustic_indices].mean().reset_index()

# -------------------- Step 4: Scaling and PCA --------------------
features = df_pca[acoustic_indices]
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)
pca = PCA(n_components=2)
principal_components = pca.fit_transform(scaled_features)
pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'])
final_pca_df = pd.concat([df_pca[['Spot', 'Segment']], pca_df], axis=1)


# -------------------- Step 5: Create the PCA Matrix Grid --------------------
# Create two pivot tables, one for PC1 and one for PC2
pc1_grid = final_pca_df.pivot(index='Segment', columns='Spot', values='PC1')
pc2_grid = final_pca_df.pivot(index='Segment', columns='Spot', values='PC2')

# Reorder the index to match the time segments
segment_order = ['Night', 'Morning', 'Day', 'Evening']
pc1_grid = pc1_grid.reindex(segment_order)
pc2_grid = pc2_grid.reindex(segment_order)

# -------------------- Step 6: Visualize the Matrix Grids --------------------

# --- Heatmap for PC1 ---
plt.figure(figsize=(10, 6))
sns.heatmap(
    pc1_grid,
    annot=True,          # Show the numerical values
    fmt=".2f",           # Format to two decimal places
    cmap="coolwarm",     # Use a diverging color palette
    center=0,            # Center the color scale at 0
    linewidths=.5,
    cbar_kws={'label': 'Aggregated Acoustic Profile (PC1 Score)'}
)
plt.title('PC1 Score Matrix Grid by Spot and Time Segment')
plt.xlabel('Monitoring Spot')
plt.ylabel('Time Segment')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# --- Heatmap for PC2 ---
plt.figure(figsize=(10, 6))
sns.heatmap(
    pc2_grid,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=.5,
    cbar_kws={'label': 'Aggregated Acoustic Profile (PC2 Score)'}
)
plt.title('PC2 Score Matrix Grid by Spot and Time Segment')
plt.xlabel('Monitoring Spot')
plt.ylabel('Time Segment')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()


# %%
# -------------------- Boxplot Visualization --------------------
# Create boxplots for each index (Confidence, ADI, ACI, AEI, NDSI) by Hour.

for i in range(len(results_combined)):
    plt.figure(figsize=(12, 6))
    pd.read_csv(results_combined[i]).boxplot(column="CLS", by="Hour", grid=True)
    plt.title(f"CLS per Hour (Boxplot) Spot {i+1}")
    plt.suptitle("")
    plt.xlabel("Hour")
    plt.ylabel("CLS")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    # plt.savefig(f"boxplot _per_hour.png")
    plt.show()

# %% [markdown]
# ### Part 2: Generation of BirdNet predictions
# 
# - **Generating Lat-Long specific species list**
# - **Predictions** Gives one bird for one 3 second segment if detected (also no bird for some segments) with a confidence score
# 

# %%
!python "E:\archive\BirdNET-Analyzer\analyze.py" --i "E:\Sanjay_Van_Monitoring\Origin Spot\02062025-13062025_30R30W\recordings\04213SPOT1_20250602_120000.wav" --o "E:\Sanjay_Van_Monitoring\Origin Spot\02062025-13062025_30R30W\BirdNET_Temp_Results" --lat 28.53 --lon 77.18 --week 24 --min_conf 0.5 --rtype csv


# %%
import librosa
audio, sr = librosa.load(r"E:\Sanjay_Van_Monitoring\Origin Spot\02062025-13062025_30R30W\recordings\04213SPOT1_20250602_120000.wav", sr=None)
print(f"Loaded successfully with sample rate: {sr}")

# %%
!python E:\archive\BirdNET-Analyzer\species.py --lat 28.53 --lon 77.18 --week 24 --sf_thresh 0.1 "E:\species_list.txt"

# %%
import subprocess

script_path = r"E:\archive\BirdNET-Analyzer\species.py"

output_file = r"E:\species_list.txt"

# Set the location, week, and threshold
lat = "28.53"
lon = "77.18"
week = "24"
threshold = "0.05"

command = [
    sys.executable, script_path,
    "--lat", lat,
    "--lon", lon,
    "--week", week,
    "--threshold", threshold,
    "--o", output_file
]

# Run the command
try:
    subprocess.run(command, check=True)
    print(f"✅ Species list written to: {output_file}")
except subprocess.CalledProcessError as e:
    print("❌ Failed to generate species list:")
    print(e.stderr)


# %%
!pip install birdnetlib --trusted-host pypi.org --trusted-host files.pythonhosted.org
!pip install resampy --trusted-host pypi.org --trusted-host files.pythonhosted.org

# %%
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime


import os
import re
import sys
import pandas as pd
import subprocess
import numpy as np
np.complex = complex  # Monkey patch for compatibility
import librosa
import soundfile as sf


TARGET_SR = 48000
SNR_DB = 18

# ==================== DENOISING FUNCTION ====================
def remove_static_noise(audio, noise_ref, sr=TARGET_SR, snr_db=SNR_DB):
    if len(noise_ref) > len(audio):
        noise_ref = noise_ref[:len(audio)]
    else:
        noise_ref = np.pad(noise_ref, (0, len(audio) - len(noise_ref)), 'wrap')
    audio_power = np.mean(audio ** 2)
    noise_power = np.mean(noise_ref ** 2)
    desired_noise_power = audio_power / (10 ** (snr_db / 10))
    noise_ref_scaled = noise_ref * np.sqrt(desired_noise_power / noise_power)
    audio_td = audio - noise_ref_scaled
    stft = librosa.stft(audio_td, n_fft=2048, hop_length=512)
    magnitude, phase = np.abs(stft), np.angle(stft)
    noise_stft = librosa.stft(noise_ref, n_fft=2048, hop_length=512)
    noise_mag = np.abs(noise_stft)
    noise_threshold = np.mean(noise_mag, axis=1, keepdims=True) * 1.2
    gated_mag = np.where(magnitude > noise_threshold, magnitude, 0)
    cleaned_stft = gated_mag * np.exp(1j * phase)
    return librosa.istft(cleaned_stft, hop_length=512)

# ==================== LOAD STATIC NOISE CLIP ====================
STATIC_NOISE_PATH = r"E:\projects\acoustic_biodiversity\static_noise.wav"
noise_clip, _ = librosa.load(STATIC_NOISE_PATH, sr=TARGET_SR)

import tempfile
def analyze_bird_audio(audio_path, lat, lon):
    # Step 1: Load audio with original sampling rate
    audio_raw, orig_sr = librosa.load(audio_path, sr=None)
    
    # Step 2: Resample if needed
    if orig_sr != TARGET_SR:
        audio_raw = librosa.resample(y=audio_raw, orig_sr=orig_sr, target_sr=TARGET_SR)

    
    # Step 3: Denoise
    final_sound = remove_static_noise(audio_raw, noise_clip, sr=TARGET_SR, snr_db=SNR_DB)

    # Step 4: Save to temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        sf.write(tmpfile.name, final_sound, samplerate=TARGET_SR)
        tmp_audio_path = tmpfile.name

    # Step 5: Analyze with BirdNET
    analyzer = Analyzer()
    recording = Recording(
        analyzer,
        tmp_audio_path,
        lat=lat,
        lon=lon,
        #date=date,
        #min_conf=min_conf,
    )
    recording.analyze()
    
    return pd.DataFrame(recording.detections)



# %%
detections_df = analyze_bird_audio(
    audio_path=r"E:\monitoring_data\sound_recordings\spot_1_original_spot\21062025-05072025_5R5W\recordings\04213SPOT1_20250621_081000.wav",
    lat=28.53,
    lon=77.18,
    # date="2024-06-12",
    #min_conf=0.3
)

print(detections_df.head()) 

# %%
DATASETS = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\recordings", r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\recordings", r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\recordings", r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\recordings"]
OUTPUTS = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\birdnet_classification.csv"]

# %%
# THIS IS THE FINAL PREDICTIONS FUNCTION
# IT GIVES A REALLY HUGE CELL OUTPUT SO THAT NEEDS TO BE CHANGED TO ONE LIKE PER FILE HOPEFULLY

# Your function to extract datetime components
def extract_year_month_date_hour_and_minute(filename):
    match_date = re.search(r'_(\d{8})_', filename)
    match = re.search(r'_(\d{6})\.wav$', filename)
    if match and match_date:
        time_str = match.group(1)
        date_str = match_date.group(1)
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:]
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        return year, month, day, hour, minute
    return None, None, None, None, None

# Directory containing WAV recordings

for i in range(4):
    # Store all detections
    all_detections = []

    # Loop through all .wav files
    for fname in os.listdir(DATASETS[i]):
        if fname.lower().endswith(".wav"):
            filepath = os.path.join(DATASETS[i], fname)

            # Extract date from filename (required by BirdNET)
            year, month, day, hour, minute = extract_year_month_date_hour_and_minute(fname)
            if None in [year, month, day]:
                print(f"Skipping file due to unmatched filename format: {fname}")
                continue

            # Format as YYYY-MM-DD
            date_str = f"{year}-{month}-{day}"

            try:
                # Run BirdNET analysis
                detections_df = analyze_bird_audio(
                    audio_path=filepath,
                    lat=28.53,
                    lon=77.18
                    # date=date_str,
                    # min_conf=0.3
                )

                # Add filename and datetime columns
                detections_df["filename"] = fname
                detections_df["year"] = year
                detections_df["month"] = month
                detections_df["day"] = day
                detections_df["hour"] = hour
                detections_df["minute"] = minute

                all_detections.append(detections_df)

                # ✅ Print progress
                print(f"Processed file: {fname} with {len(detections_df)} detections.")

            except Exception as e:
                print(f"Error processing {fname}: {e}")

    # Combine all detections
    if all_detections:
        final_df = pd.concat(all_detections, ignore_index=True)
        final_df.to_csv(OUTPUTS[i], index=False)
        print("Saved detections to 'birdnet_detections_all.csv'")
    else:
        print("No detections processed.")


# %%
import pandas as pd
DATASETS = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\birdnet_classification.csv", r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\birdnet_classification.csv"]


dataset_list = [pd.read_csv(file) for file in DATASETS]
data = pd.concat(dataset_list, ignore_index=True)

print(data.head())


# %%
# Get unique common names
unique_names = data["label"].dropna().unique()

# Save to a text file
with open("unique_common_names.txt", "w", encoding="utf-8") as f:
    for name in unique_names:
        f.write(name + "\n")


# %% [markdown]
# ### Part 7: Validation of Output 
# 
# - **Confusion Matrix** This gives all the values needed for the confusion matrix
# - The latest species list is generated from unique bird names from combined_df in graph_spot3_4
# - The 222 validation bird list has been created from eBird and is considered as ground truth since it is the same list on Myna
# 

# %%

import re
from collections import defaultdict

# --- DATA INPUT ---
# The raw text data variables will be placed here.
# I'm omitting them for brevity in this response, but they are the same as before.

ebird_raw_text = """
"""

birdnet_spot1_raw = """


"""

# --- DATA PROCESSING FUNCTIONS (Unchanged) ---
def parse_ebird_list(raw_text):
    species_set = set()
    pattern = re.compile(r"^(.*?)\s+[A-Z][a-z]+ [a-z]+")
    for line in raw_text.strip().split('\n'):
        line = line.strip()
        if not line: continue
        match = pattern.match(line)
        if match:
            common_name = match.group(1).strip()
            # Standardize a name for better matching
            if "Honey Buzzard" in common_name:
                common_name = "Oriental Honey-buzzard"
            species_set.add(common_name)
    return species_set

def parse_birdnet_list(raw_text):
    species_set = set()
    non_bird_sounds = {
        'Engine', 'Siren', 'Fireworks', 'Gun', 'Human vocal', 'Gray Wolf',
        'Southeastern Field Cricket', 'Jumping Bush Cricket', 'Carolina Ground Cricket',
        'Green Treefrog', 'American Bullfrog', 'Adelie Penguin', 'King Penguin'
    }
    for line in raw_text.strip().split('\n'):
        line = line.strip()
        if not line or '_' not in line or 'Spot' in line: continue
        parts = line.split('_', 1)
        if len(parts) < 2: continue
        common_name = parts[1].replace('-', ' ').strip()
        is_junk = any(junk in common_name for junk in non_bird_sounds)
        if not is_junk:
            species_set.add(common_name)
    return species_set

def check_plausibility(species_list):
    implausible_keywords = [
        # Continents/Regions
        'American', 'African', 'Andean', 'Puerto Rican', 'Madagascar', 'Palau', 'Yungas',
        # North/Central America
        'Canada', 'Canadian', 'Carolina', 'Kentucky', 'Louisiana', 'Mississippi', 'Acadian',
        'MacGillivray', 'Red cockaded', 'Pileated', 'Gila', 'Red bellied', 'Hairy',
        'Cuban', 'Yucatan', 'Bahama', 'Cave Swallow', 'Sinaloa', 'Mexican', 'Steller', 'Bald Eagle',
        # South America
        'Peruvian', 'Bamboo Antshrike', 'Acre Tody Tyrant', 'Hoatzin',
        # Australia/Pacific
        'Pacific', 'Mauritius', 'Ryukyu', 'Akiapolaau', 'Akohekohe',
        'Wonga Pigeon', 'Noisy Miner', 'Pied Currawong', 'Crescent Honeyeater',
        # Marine/Antarctic
        'Penguin', 'Kittiwake', 'Manx Shearwater', 'Auklet', 'Loon',
        # Specific out-of-place species
        'Veery', 'Wonga Pigeon'
    ]
    plausible, implausible = [], []
    for species in sorted(list(species_list)):
        is_implausible = any(keyword in species for keyword in implausible_keywords)
        if is_implausible:
            implausible.append(species)
        else:
            plausible.append(species)
    return plausible, implausible

def print_list(title, item_list, indent=""):
    print(f"{indent}--- {title} ({len(item_list)}) ---")
    if not item_list:
        print(f"{indent}None")
        return
    for item in sorted(item_list):
        print(f"{indent}- {item}")

# --- ANALYSIS EXECUTION (CORRECTED LOGIC) ---

# 1. Parse all data
ebird_species = parse_ebird_list(ebird_raw_text)
birdnet_spot1 = parse_birdnet_list(birdnet_spot1_raw)


# 2. Create the UNION of all BirdNET detections
birdnet_total_union = birdnet_spot1 

# 3. Compare the complete eBird list vs the complete BirdNET list
confirmed_by_birdnet = ebird_species & birdnet_total_union
missed_by_birdnet = ebird_species - birdnet_total_union
birdnet_only_detections = birdnet_total_union - ebird_species

# 4. Categorize the BirdNET-only detections
plausible_birdnet_only, implausible_birdnet_only = check_plausibility(birdnet_only_detections)

# 5. For deeper analysis, find where the plausible detections occurred
#    FIX: Convert the list 'plausible_birdnet_only' to a set for intersection operations
plausible_set = set(plausible_birdnet_only)


# --- REVISED REPORTING ---

print("############################################################")
print("###      Sanjayvan Bird Data Analysis (Site-Level)       ###")
print("############################################################")

print("\n================== OVERALL SUMMARY ===================")
print(f"eBird Species List (Ground Truth): {len(ebird_species)}")
print(f"Total Unique Bird Detections by BirdNET (across both spots): {len(birdnet_total_union)}")

print("\n\n=============== PART 1: CONFIRMED SPECIES ===============")
print("This section compares the eBird list to the total BirdNET detections.")
print_list("Species on eBird List CONFIRMED by BirdNET (at one or both spots)", confirmed_by_birdnet)
print_list("Species on eBird List MISSED by BirdNET (Acoustic Blind Spots)", missed_by_birdnet)


print("\n\n========= PART 2: THE INVESTIGATION LIST (PLAUSIBLE but UNCONFIRMED) =========")
print("This is the PRIMARY list for manual review. These are species that are geographically")
print("plausible but not on the official eBird list for Sanjayvan.")
print_list("TOTAL Plausible but Unconfirmed Species found across both spots", plausible_birdnet_only)


print("\n\n=============== PART 3: THE JUNK PILE (IMPLAUSIBLE DETECTIONS) ===============")
print("These are clear system errors where BirdNET misidentified sounds as birds from")
print("other continents or environments. They should be disregarded.")
print_list("TOTAL Geographically IMPLAUSIBLE species detected", implausible_birdnet_only)

print("\n############################################################")
print("###                 Analysis Conclusion                  ###")
print("############################################################")
print(f"""
This revised analysis takes a site-level approach, providing a clearer picture for Sanjayvan as a whole.

1.  **System Performance:** BirdNET successfully confirmed the presence of **{len(confirmed_by_birdnet)}** species from the official {len(ebird_species)}-species eBird list. However, it completely missed **{len(missed_by_birdnet)}** known species, highlighting its limitations with non-vocal or quiet birds.

2.  **The Actionable 'Investigation List':** The most critical output is the single, unified list of **{len(plausible_birdnet_only)} plausible but unconfirmed species**. This list, created by taking the **union** of all plausible detections from both spots, represents every potential new sighting or misidentification that warrants expert review.
    - To help prioritize this list, of these species were detected at *both* spots. These should be investigated first, as multiple detections could indicate a higher (though still low) chance of being a genuine, repeated call.

3.  **Quantifying System Error:** The analysis identified a Junk Pile of **{len(implausible_birdnet_only)} geographically impossible species**. The presence of birds like the 'Red-shouldered Hawk' (North America) and 'Congo Serpent Eagle' (Africa) is definitive proof of the system's high error rate. This number serves as a crucial reminder to treat all unconfirmed BirdNET detections with extreme skepticism.

**Final Recommendation:**
The workflow for a researcher or manager should be:
1.  **Trust the eBird list** as the verified baseline.
2.  **Use the 'Investigation List' ({len(plausible_birdnet_only)} species) as your to-do list.** Go back to the source audio files for each of these detections and have an expert ornithologist listen to them to determine if they are genuine vagrants or misidentifications of common local species.
3.  **Completely disregard the 'Junk Pile'** of {len(implausible_birdnet_only)} species as known system errors.
""")

# %%




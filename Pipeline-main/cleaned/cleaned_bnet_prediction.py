import os
import re
import sys
import tempfile
import subprocess
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

delegate = None
try:
    import tflite_runtime.interpreter as tflite
    delegate = tf.lite.experimental.load_delegate("libtensorflowlite_gpu_delegate.so")
except (ModuleNotFoundError, Exception):
    from tensorflow import lite as tflite
    try:
        delegate = tf.lite.experimental.load_delegate("libtensorflowlite_gpu_delegate.so")
    except Exception as e:
        print(f"GPU delegate not available: {e}")

if delegate and not hasattr(tflite, "_original_interpreter"):
    tflite._original_interpreter = tflite.Interpreter
    def Interpreter_with_delegate(*args, **kwargs):
        kwargs["experimental_delegates"] = [delegate]
        return tflite._original_interpreter(*args, **kwargs)
    tflite.Interpreter = Interpreter_with_delegate

def map_to_segment(hour):
    if 21 <= hour or hour < 5:
        return 'Night'
    elif 5 <= hour < 10:
        return 'Morning'
    elif 10 <= hour < 17:
        return 'Day'
    else:
        return 'Evening'

def remove_static_noise(audio, noise_ref, sr, snr_db):
    if len(noise_ref) > len(audio):
        noise_ref = noise_ref[:len(audio)]
    else:
        noise_ref = np.pad(noise_ref, (0, len(audio) - len(noise_ref)), 'wrap')

    audio_power = np.mean(audio ** 2)
    noise_power = np.mean(noise_ref ** 2)
    if noise_power == 0:
        return audio

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

def analyze_bird_audio(audio_path, lat, lon, noise_clip, target_sr, snr_db):
    audio_raw, orig_sr = librosa.load(audio_path, sr=None)

    if orig_sr != target_sr:
        audio_raw = librosa.resample(y=audio_raw, orig_sr=orig_sr, target_sr=target_sr)

    final_sound = remove_static_noise(audio_raw, noise_clip, sr=target_sr, snr_db=snr_db)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        sf.write(tmpfile.name, final_sound, samplerate=target_sr)
        tmp_audio_path = tmpfile.name

    analyzer = Analyzer()
    recording = Recording(analyzer, tmp_audio_path, lat=lat, lon=lon)
    recording.analyze()

    os.remove(tmp_audio_path)
    return pd.DataFrame(recording.detections)

def extract_year_month_date_hour_and_minute(filename):
    match_date = re.search(r'_(\d{8})_', filename)
    match_time = re.search(r'_(\d{6})\.wav$', filename)
    if match_time and match_date:
        time_str = match_time.group(1)
        date_str = match_date.group(1)
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:]
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        return year, month, day, hour, minute
    return None, None, None, None, None

def parse_ebird_list(raw_text):
    species_set = set()
    pattern = re.compile(r"^(.*?)\s+[A-Z][a-z]+ [a-z]+")
    for line in raw_text.strip().split('\n'):
        line = line.strip()
        if not line: continue
        match = pattern.match(line)
        if match:
            common_name = match.group(1).strip()
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
        'American', 'African', 'Andean', 'Puerto Rican', 'Madagascar', 'Palau', 'Yungas',
        'Canada', 'Canadian', 'Carolina', 'Kentucky', 'Louisiana', 'Mississippi', 'Acadian',
        'MacGillivray', 'Red cockaded', 'Pileated', 'Gila', 'Red bellied', 'Hairy',
        'Cuban', 'Yucatan', 'Bahama', 'Cave Swallow', 'Sinaloa', 'Mexican', 'Steller', 'Bald Eagle',
        'Peruvian', 'Bamboo Antshrike', 'Acre Tody Tyrant', 'Hoatzin',
        'Pacific', 'Mauritius', 'Ryukyu', 'Akiapolaau', 'Akohekohe',
        'Wonga Pigeon', 'Noisy Miner', 'Pied Currawong', 'Crescent Honeyeater',
        'Penguin', 'Kittiwake', 'Manx Shearwater', 'Auklet', 'Loon', 'Veery'
    ]
    plausible, implausible = [], []
    for species in sorted(list(species_list)):
        if any(keyword in species for keyword in implausible_keywords):
            implausible.append(species)
        else:
            plausible.append(species)
    return plausible, implausible

## Section 1: PCA Analysis of Acoustic Indices
results_combined_paths = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\results.csv"
]

all_data = []
for i, file_path in enumerate(results_combined_paths):
    df_spot = pd.read_csv(file_path)
    df_spot['Spot'] = f'Spot {i+1}'
    all_data.append(df_spot)

master_df = pd.concat(all_data, ignore_index=True)
master_df['Segment'] = master_df['Hour'].apply(map_to_segment)

acoustic_indices = ['ADI', 'ACI', 'AEI', 'NDSI', 'CLS']
df_pca = master_df.groupby(['Spot', 'Segment'])[acoustic_indices].mean().reset_index()

features = df_pca[acoustic_indices]
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)
pca = PCA(n_components=2)
principal_components = pca.fit_transform(scaled_features)
pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'])
final_pca_df = pd.concat([df_pca[['Spot', 'Segment']], pca_df], axis=1)

plt.figure(figsize=(10, 8))
sns.scatterplot(data=final_pca_df, x='PC1', y='PC2', hue='Spot', style='Segment', s=150, palette='viridis')
plt.title('PCA of Acoustic Indices by Spot and Time Segment')
plt.xlabel('Principal Component 1 (PC1)')
plt.ylabel('Principal Component 2 (PC2)')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

pca_full = PCA().fit(scaled_features)
plt.figure(figsize=(8, 6))
plt.plot(np.cumsum(pca_full.explained_variance_ratio_), marker='o', linestyle='--')
plt.title('Explained Variance vs. Number of Components')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.grid(True, linestyle='--', alpha=0.6)
plt.axhline(y=0.95, color='r', linestyle='-', label='95% Cutoff')
plt.legend()
plt.show()

segment_order = ['Night', 'Morning', 'Day', 'Evening']
pc1_grid = final_pca_df.pivot(index='Segment', columns='Spot', values='PC1').reindex(segment_order)
pc2_grid = final_pca_df.pivot(index='Segment', columns='Spot', values='PC2').reindex(segment_order)

plt.figure(figsize=(10, 6))
sns.heatmap(pc1_grid, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=.5, cbar_kws={'label': 'Aggregated Acoustic Profile (PC1 Score)'})
plt.title('PC1 Score Matrix Grid by Spot and Time Segment')
plt.xlabel('Monitoring Spot')
plt.ylabel('Time Segment')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
sns.heatmap(pc2_grid, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=.5, cbar_kws={'label': 'Aggregated Acoustic Profile (PC2 Score)'})
plt.title('PC2 Score Matrix Grid by Spot and Time Segment')
plt.xlabel('Monitoring Spot')
plt.ylabel('Time Segment')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

## Section 2: Boxplot Visualization
for i, path in enumerate(results_combined_paths):
    plt.figure(figsize=(12, 6))
    pd.read_csv(path).boxplot(column="CLS", by="Hour", grid=True)
    plt.title(f"CLS per Hour (Boxplot) Spot {i+1}")
    plt.suptitle("")
    plt.xlabel("Hour")
    plt.ylabel("CLS")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()

## Section 3: Generate Species List
script_path = r"E:\archive\BirdNET-Analyzer\species.py"
output_file = r"E:\species_list.txt"
command = [sys.executable, script_path, "--lat", "28.53", "--lon", "77.18", "--week", "24", "--threshold", "0.05", "--o", output_file]
try:
    subprocess.run(command, check=True)
    print(f"Species list written to: {output_file}")
except subprocess.CalledProcessError as e:
    print(f"Failed to generate species list: {e}")

## Section 4: BirdNet Predictions
TARGET_SR = 48000
SNR_DB = 18
STATIC_NOISE_PATH = r"E:\projects\acoustic_biodiversity\static_noise.wav"
noise_clip, _ = librosa.load(STATIC_NOISE_PATH, sr=TARGET_SR)

DATASET_DIRS = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\recordings",
    r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\recordings",
    r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\recordings",
    r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\recordings"
]
OUTPUT_FILES = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\birdnet_classification.csv"
]

for i in range(len(DATASET_DIRS)):
    all_detections = []
    for fname in os.listdir(DATASET_DIRS[i]):
        if fname.lower().endswith(".wav"):
            filepath = os.path.join(DATASET_DIRS[i], fname)
            year, month, day, hour, minute = extract_year_month_date_hour_and_minute(fname)
            if None in [year, month, day]:
                print(f"Skipping file due to unmatched format: {fname}")
                continue
            try:
                detections_df = analyze_bird_audio(
                    audio_path=filepath, lat=28.53, lon=77.18,
                    noise_clip=noise_clip, target_sr=TARGET_SR, snr_db=SNR_DB
                )
                detections_df["filename"] = fname
                detections_df["year"] = year
                detections_df["month"] = month
                detections_df["day"] = day
                detections_df["hour"] = hour
                detections_df["minute"] = minute
                all_detections.append(detections_df)
                print(f"Processed file: {fname} with {len(detections_df)} detections.")
            except Exception as e:
                print(f"Error processing {fname}: {e}")

    if all_detections:
        final_df = pd.concat(all_detections, ignore_index=True)
        final_df.to_csv(OUTPUT_FILES[i], index=False)
        print(f"Saved detections to {OUTPUT_FILES[i]}")

## Section 5: Post-Prediction Analysis
DETECTION_CSVS = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\20072025-29072025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_2_peacock_spot\20072025-03082025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_4_yoga_spot\20072025-03082025_2R4W\birdnet_classification.csv",
    r"E:\monitoring_data\sound_recordings\spot_3_investigation_spot\20072025-03082025_2R4W\birdnet_classification.csv"
]
dataset_list = [pd.read_csv(file) for file in DETECTION_CSVS]
combined_data = pd.concat(dataset_list, ignore_index=True)

unique_names = combined_data["label"].dropna().unique()
with open("unique_common_names.txt", "w", encoding="utf-8") as f:
    for name in unique_names:
        f.write(name + "\n")

## Section 6: Validation of Output
ebird_raw_text = """
"""
birdnet_spot1_raw = """
"""

ebird_species = parse_ebird_list(ebird_raw_text)
birdnet_total_union = parse_birdnet_list(birdnet_spot1_raw)
confirmed_by_birdnet = ebird_species & birdnet_total_union
missed_by_birdnet = ebird_species - birdnet_total_union
birdnet_only_detections = birdnet_total_union - ebird_species
plausible_birdnet_only, implausible_birdnet_only = check_plausibility(birdnet_only_detections)

print(f"eBird Species List (Ground Truth): {len(ebird_species)}")
print(f"Total Unique Bird Detections by BirdNET: {len(birdnet_total_union)}")
print(f"Species on eBird List CONFIRMED by BirdNET: {len(confirmed_by_birdnet)}")
print(f"Species on eBird List MISSED by BirdNET: {len(missed_by_birdnet)}")
print(f"TOTAL Plausible but Unconfirmed Species: {len(plausible_birdnet_only)}")
print(f"TOTAL Geographically IMPLAUSIBLE species detected: {len(implausible_birdnet_only)}")
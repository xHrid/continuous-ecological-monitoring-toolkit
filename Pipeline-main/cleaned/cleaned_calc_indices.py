import os
import re
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, find_peaks
from scipy.stats import entropy

# --- Configuration ---
TARGET_SR = 48000
SEGMENT_DURATION_S = 120.0
SKIP_DURATION_S = 60.0
TOTAL_SEGMENTS = 2
STATIC_NOISE_PATH = r"E:\projects\acoustic_biodiversity\static_noise.wav"

DATASET_PATHS = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\21062025-05072025_5R5W\recordings",
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\08072025-11072025_2R4W\recordings"
]
OUTPUT_CSVS = [
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\21062025-05072025_5R5W\results.csv",
    r"E:\monitoring_data\sound_recordings\spot_1_original_spot\08072025-11072025_2R4W\results.csv"
]

# --- Core Functions ---
def extract_year_month_date_hour_and_minute(filename):
    match_date = re.search(r'_(\d{8})_', filename)
    match_time = re.search(r'_(\d{6})\.wav$', filename)
    if match_time and match_date:
        time_str = match_time.group(1)
        date_str = match_date.group(1)
        return date_str[:4], date_str[4:6], date_str[6:], int(time_str[:2]), int(time_str[2:4])
    return None, None, None, None, None

def remove_static_noise(audio, noise_ref, sr, snr_db=18):
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

def compute_acoustic_indices(y, sr):
    f, t, Sxx = spectrogram(y, fs=sr, nperseg=1024, noverlap=512)
    Sxx += 1e-10

    S_norm = Sxx / Sxx.sum(axis=0, keepdims=True)
    ADI = np.mean(entropy(S_norm, axis=0))
    AEI = 1.0 - (ADI / np.log(Sxx.shape[0])) if Sxx.shape[0] > 1 else 1.0

    delta = np.abs(np.diff(Sxx, axis=1))
    ACI_vals = np.sum(delta, axis=1) / (np.sum(Sxx[:, :-1], axis=1))
    ACI_total = np.mean(ACI_vals)

    bio_band = (f >= 2000) & (f <= 11000)
    anthro_band = (f >= 100) & (f <= 2000)
    B = np.sum(Sxx[bio_band, :])
    A = np.sum(Sxx[anthro_band, :])
    NDSI = (B - A) / (B + A) if (B + A) > 0 else 0.0

    mid_band = (f >= 2000) & (f <= 8000)
    mid_band_energy = np.sum(Sxx[mid_band, :], axis=0)
    total_energy = np.sum(Sxx, axis=0)
    threshold = 0.2 * total_energy
    MFC = np.mean(mid_band_energy > threshold)

    CLS_list = [len(find_peaks(frame / np.max(frame), height=0.5)[0]) for frame in Sxx.T]
    CLS = np.mean(CLS_list)

    return ADI, ACI, AEI, NDSI, MFC, CLS

def segment_audio(audio, fs, segment_duration, skip_duration, total_segments):
    segment_samples = int(segment_duration * fs)
    skip_samples = int(skip_duration * fs)
    segments = []
    start = 0
    for _ in range(total_segments):
        end = start + segment_samples
        if end > len(audio):
            break
        segments.append(audio[start:end])
        start += segment_samples + skip_samples
    return segments

# --- Main Execution ---
noise_clip, _ = librosa.load(STATIC_NOISE_PATH, sr=TARGET_SR)

for i in range(len(DATASET_PATHS)):
    dataset_path = DATASET_PATHS[i]
    output_csv = OUTPUT_CSVS[i]
    results_data = []

    print(f"--- Processing Directory: {dataset_path} ---")
    for filename in sorted(os.listdir(dataset_path)):
        if filename.lower().endswith(".wav"):
            year, month, date, hour, minute = extract_year_month_date_hour_and_minute(filename)
            if hour is None:
                continue

            filepath = os.path.join(dataset_path, filename)
            print(f"Processing {filename}...")

            audio, sr = librosa.load(filepath, sr=TARGET_SR)
            audio_denoised = remove_static_noise(audio, noise_clip, sr)
            segments = segment_audio(audio_denoised, sr, SEGMENT_DURATION_S, SKIP_DURATION_S, TOTAL_SEGMENTS)

            if not segments:
                print(f"Skipped {filename} (too short for segmentation)")
                continue

            for j, segment in enumerate(segments):
                ADI, ACI, AEI, NDSI, MFC, CLS = compute_acoustic_indices(segment, sr)
                results_data.append({
                    "Filename": filename, "Segment": j + 1,
                    "Year": year, "Month": month, "Date": date, "Hour": hour, "Minute": minute,
                    "Second": j * (SEGMENT_DURATION_S + SKIP_DURATION_S),
                    "ADI": ADI, "ACI": ACI, "AEI": AEI, "NDSI": NDSI, "MFC": MFC, "CLS": CLS
                })

    results_df = pd.DataFrame(results_data)
    results_df.to_csv(output_csv, index=False)
    print(f"--- Results saved to {output_csv} ---\n")

# --- Visualization (uses results from the last processed dataset) ---
if 'results_df' in locals() and not results_df.empty:
    results_df.sort_values(by=["Filename", "Segment"], inplace=True)
    results_df.reset_index(drop=True, inplace=True)
    results_df["X_pos"] = range(len(results_df))

    for idx in ["ADI", "ACI", "AEI", "NDSI"]:
        plt.figure(figsize=(14, 6))
        plt.plot(results_df["X_pos"], results_df[idx], marker='o', linestyle='-', alpha=0.8)
        plt.xticks(results_df["X_pos"][::10], results_df["Hour"][::10], rotation=45)
        plt.title(f"{idx} Across Segments (from last dataset)")
        plt.xlabel("Hour of Day (label only; segments are evenly spaced)")
        plt.ylabel(idx)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.show()
else:
    print("No data was processed, skipping visualization.")
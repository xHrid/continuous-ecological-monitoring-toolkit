# %% [markdown]
# ### Part 1: Calculation of Indices
# 
# - Calculates and saves indices into a csv after preprocessing sound data
# - Indices Computed: ADI, ACI, AEI, NDSI, CLS, MFC
# 

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
from scipy.signal import spectrogram, find_peaks
from scipy.stats import entropy
import gc

# %%
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

# %%
DATASET_PATH = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\21062025-05072025_5R5W\recordings", r"E:\monitoring_data\sound_recordings\spot_1_original_spot\08072025-11072025_2R4W\recordings"]
STATIC_NOISE_PATH = r"E:\projects\acoustic_biodiversity\static_noise.wav"
TARGET_SR = 48000
OUTPUT_CSV = [r"E:\monitoring_data\sound_recordings\spot_1_original_spot\21062025-05072025_5R5W\results.csv", r"E:\monitoring_data\sound_recordings\spot_1_original_spot\08072025-11072025_2R4W\results.csv"]

# %%
def extract_year_month_date_hour_and_minute(filename):
    """Extracts hour and minute from filenames like '2MM07103_20250330_143000.wav'."""
    match_date = re.search(r'_(\d{8})_', filename)
    match = re.search(r'_(\d{6})\.wav$', filename)
    if match and match_date:
        time_str = match.group(1)
        date_str = match_date.group(1)
        year = date_str[:4]
        month = date_str[4:6]
        date = date_str[6:]
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        return year, month, date, hour, minute
    return None, None, None, None, None

def remove_static_noise(audio, noise_ref, sr=TARGET_SR, snr_db=18):
    """
    Combines time-domain noise subtraction and spectral gating to remove static noise.
    
    1. Time-Domain Subtraction:  
       - The noise reference is padded (using 'wrap' mode) to match the audio length.
       - Its power is scaled (using the desired SNR) and subtracted from the audio.
       
    2. Spectral Gating:  
       - The resulting audio is transformed into the frequency domain using STFT.
       - A noise threshold is computed from the noise reference (via its STFT).
       - Frequency bins with energy below the threshold are zeroed out.
       - The audio is reconstructed using the inverse STFT.
    """
    # --- Time-Domain Subtraction ---
    if len(noise_ref) > len(audio):
        noise_ref = noise_ref[:len(audio)]
    else:
        noise_ref = np.pad(noise_ref, (0, len(audio) - len(noise_ref)), 'wrap')
    
    audio_power = np.mean(audio ** 2)
    noise_power = np.mean(noise_ref ** 2)
    desired_noise_power = audio_power / (10 ** (snr_db / 10))
    noise_ref_scaled = noise_ref * np.sqrt(desired_noise_power / noise_power)
    audio_td = audio - noise_ref_scaled

    # --- Spectral Gating ---
    stft = librosa.stft(audio_td, n_fft=2048, hop_length=512)
    magnitude, phase = np.abs(stft), np.angle(stft)

    noise_stft = librosa.stft(noise_ref, n_fft=2048, hop_length=512)
    noise_mag = np.abs(noise_stft)
    noise_threshold = np.mean(noise_mag, axis=1, keepdims=True) * 1.2  # threshold factor

    gated_mag = np.where(magnitude > noise_threshold, magnitude, 0)
    cleaned_stft = gated_mag * np.exp(1j * phase)
    audio_cleaned = librosa.istft(cleaned_stft, hop_length=512)

    return audio_cleaned

import pandas as pd
import numpy as np
import librosa  # For loading audio files
import os
from scipy.signal import spectrogram, find_peaks
from scipy.stats import entropy

# --------------------------------------------------------------------------
# --- 1. CORE CALCULATION FUNCTIONS ---
# --------------------------------------------------------------------------

def compute_acoustic_indices(y, sr):
    """
    Computes six eco-acoustic indices from an audio signal.
    """
    # Create the spectrogram
    f, t, Sxx = spectrogram(y, fs=sr, nperseg=1024, noverlap=512)
    Sxx += 1e-10  # Add a small epsilon to avoid log(0) or division by zero

    # --- ADI (Acoustic Diversity Index) & AEI (Acoustic Evenness Index) ---
    S_norm = Sxx / Sxx.sum(axis=0, keepdims=True)
    ADI = np.mean(entropy(S_norm, axis=0))
    # Avoid division by zero if Sxx has only one frequency bin
    AEI = 1.0 - (ADI / np.log(Sxx.shape[0])) if Sxx.shape[0] > 1 else 1.0

    # --- ACI (Acoustic Complexity Index) ---
    delta = np.abs(np.diff(Sxx, axis=1))
    ACI_vals = np.sum(delta, axis=1) / (np.sum(Sxx[:, :-1], axis=1))
    ACI_total = np.mean(ACI_vals)

    # --- NDSI (Normalized Difference Soundscape Index) ---
    bio_band = np.logical_and(f >= 2000, f <= 11000)
    anthro_band = np.logical_and(f >= 100, f <= 2000)
    B = np.sum(Sxx[bio_band, :])
    A = np.sum(Sxx[anthro_band, :])
    NDSI = (B - A) / (B + A)

    # --- MFC (Mid-Frequency Cover) ---
    mid_band = np.logical_and(f >= 2000, f <= 8000)
    mid_band_energy = np.sum(Sxx[mid_band, :], axis=0)
    total_energy = np.sum(Sxx, axis=0)
    threshold = 0.2 * total_energy
    MFC = np.mean(mid_band_energy > threshold)

    # --- CLS (Cluster Label Count) ---
    CLS_list = []
    for frame in Sxx.T: # Iterate through each time frame
        norm_frame = frame / (np.max(frame))
        peaks, _ = find_peaks(norm_frame, height=0.5)
        CLS_list.append(len(peaks))
    CLS = np.mean(CLS_list)
    
    return {'ADI': ADI, 'ACI': ACI_total, 'AEI': AEI, 'NDSI': NDSI, 'MFC': MFC, 'CLS': CLS}



# %%
TARGET_SR = 48000
SEGMENT_DURATION = 120.0  # 120 seconds
SKIP_DURATION = 60    # skip 1 minute after each segment
TOTAL_SEGMENTS = 2      # desired number of 2-min samples

def segment_audio(audio, fs=TARGET_SR):
    """
    Extracts 10 evenly spaced 1-minute segments from a 30-minute audio clip,
    with 2-minute skips between each segment.
    """
    segment_samples = int(SEGMENT_DURATION * fs)
    skip_samples = int(SKIP_DURATION * fs)
    segments = []

    start = 0
    for _ in range(TOTAL_SEGMENTS):
        end = start + segment_samples
        if end > len(audio):
            break
        segment = audio[start:end]
        segments.append(segment)
        start += segment_samples + skip_samples  # move start by 3 minutes

    return np.array(segments) if segments else None

# %% [markdown]
# !ffmpeg -i "/kaggle/input/noisee/Untitled video - Made with Clipchamp.mp4" -vn -acodec pcm_s16le -ar 22050 -ac 1 static_noise.wav
# 

# %%
for j in range(len(DATASET_PATH)):
    # Main execution
    results = []
    filepath = ""
    # Load static noise clip once
    noise_clip, _ = librosa.load(STATIC_NOISE_PATH, sr=TARGET_SR)

    for filename in sorted(os.listdir(DATASET_PATH[j])):
        if filename.lower().endswith(".wav"):
            year, month, date, hour, minute = extract_year_month_date_hour_and_minute(filename)
            filepath = os.path.join(DATASET_PATH[j], filename)
            print(f"Processing {filename} (Hour: {hour}, Minute: {minute}) ...")

            # Load and denoise audio
            audio, sr = librosa.load(filepath, sr=TARGET_SR)
            audio_denoised = remove_static_noise(audio, noise_clip)

            # Segment into 10x 1-minute samples spaced apart
            segments = segment_audio(audio_denoised)

            if segments is None:
                print(f"Skipped {filename} (too short)")
                continue

            # Process each segment
            for i, segment in enumerate(segments):
                ADI, ACI, AEI, NDSI, MFC, CLS = compute_acoustic_indices(segment.flatten(), sr)
                results.append({
                    "filename": filename,
                    "Segment": i + 1,
                    "Year": year,
                    "Month": month,
                    "Date": date,
                    "Hour": hour,
                    "Minute": minute,
                    "Second": i * (SEGMENT_DURATION + SKIP_DURATION),  # seconds from start
                    "ADI": ADI,
                    "ACI": ACI,
                    "AEI": AEI,
                    "NDSI": NDSI,
                    "MFC": MFC,
                    "CLS": CLS
                })
    

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_CSV[j], index=False)



# %%
import pandas as pd
import matplotlib.pyplot as plt

# Load results into DataFrame
results_df = pd.DataFrame(results)

# Sort by filename and segment number for logical progression
results_df.sort_values(by=["Filename", "Segment"], inplace=True)
results_df.reset_index(drop=True, inplace=True)

# Add an evenly spaced position (X-axis) for plotting
results_df["X"] = range(len(results_df))  # 0, 1, 2, ...

# Plot each index
for idx in ["ADI", "ACI", "AEI", "NDSI"]:
    plt.figure(figsize=(14, 6))
    plt.plot(results_df["X"], results_df[idx], marker='o', linestyle='-', alpha=0.8)

    # Use Hour as label on the x-axis (even though X is just 0,1,2...)
    plt.xticks(results_df["X"][::10], results_df["Hour"][::10], rotation=45)  # show label every 10 segments

    plt.title(f"{idx} Across Segments (Labelled by Hour)")
    plt.xlabel("Hour (label only; segments evenly spaced)")
    plt.ylabel(idx)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(f"lineplot_{idx.lower()}_evenly_spaced_by_hour.png")
    plt.show()




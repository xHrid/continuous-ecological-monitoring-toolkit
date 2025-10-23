import os
import re
import argparse
import sys
import librosa
import numpy as np
import pandas as pd
from scipy.signal import spectrogram, find_peaks
from scipy.stats import entropy

# --- Core Processing Functions (Extracted from original script) ---

def extract_metadata_from_filename(filename):
    """Extracts date and time info from the standard filename format."""
    match_date = re.search(r'_(\d{8})_', filename)
    match_time = re.search(r'_(\d{6})\.wav$', filename)
    if match_time and match_date:
        time_str = match_time.group(1)
        date_str = match_date.group(1)
        return date_str[:4], date_str[4:6], date_str[6:], int(time_str[:2]), int(time_str[2:4])
    return None, None, None, None, None

def remove_static_noise(audio, noise_ref, sr, snr_db=18):
    """Subtracts a scaled version of the noise reference from the audio."""
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
    return audio - noise_ref_scaled # Simplified version for this context

def compute_acoustic_indices(y, sr):
    """Calculates a suite of standard acoustic indices."""
    f, t, Sxx = spectrogram(y, fs=sr, nperseg=1024, noverlap=512)
    Sxx += 1e-10 # Add epsilon to avoid division by zero

    S_norm = Sxx / Sxx.sum(axis=0, keepdims=True)
    ADI = np.mean(entropy(S_norm, axis=0))
    AEI = 1.0 - (ADI / np.log(Sxx.shape[0])) if Sxx.shape[0] > 1 else 1.0

    delta = np.abs(np.diff(Sxx, axis=1))
    ACI_vals = np.sum(delta, axis=1) / (np.sum(Sxx[:, :-1], axis=1) + 1e-10)
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

    CLS_list = [len(find_peaks(frame / (np.max(frame) + 1e-10), height=0.5)[0]) for frame in Sxx.T]
    CLS = np.mean(CLS_list)

    return ADI, ACI_total, AEI, NDSI, MFC, CLS

def segment_audio(audio, fs, segment_duration, skip_duration, total_segments):
    """Splits an audio file into multiple segments."""
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

# --- Main Execution Block ---
def main(args):
    """Main processing loop driven by command-line arguments."""
    try:
        # Load the static noise reference clip once
        noise_clip, _ = librosa.load(args.noise_file, sr=args.target_sr)
    except Exception as e:
        print(f"Error: Could not load noise file '{args.noise_file}'. Details: {e}", file=sys.stderr)
        sys.exit(1)

    results_data = []
    print(f"--- Starting Acoustic Index Calculation ---")
    print(f"Processing {len(args.input_files)} audio file(s).")

    for filepath in args.input_files:
        filename = os.path.basename(filepath)
        print(f"Processing {filename}...")
        try:
            year, month, date, hour, minute = extract_metadata_from_filename(filename)
            if hour is None:
                print(f"Warning: Could not extract metadata from '{filename}'. Skipping.")
                continue

            audio, sr = librosa.load(filepath, sr=args.target_sr)
            audio_denoised = remove_static_noise(audio, noise_clip, sr, args.snr_db)
            segments = segment_audio(audio_denoised, sr, args.segment_duration, args.skip_duration, args.total_segments)

            if not segments:
                print(f"Warning: Skipped '{filename}' (too short for segmentation).")
                continue

            for j, segment in enumerate(segments):
                ADI, ACI, AEI, NDSI, MFC, CLS = compute_acoustic_indices(segment, sr)
                results_data.append({
                    "Filename": filename, "Segment": j + 1,
                    "Year": year, "Month": month, "Date": date, "Hour": hour, "Minute": minute,
                    "ADI": ADI, "ACI": ACI, "AEI": AEI, "NDSI": NDSI, "MFC": MFC, "CLS": CLS
                })
        except Exception as e:
            print(f"Error processing file '{filename}'. Details: {e}", file=sys.stderr)
            # Continue to the next file
            continue

    if not results_data:
        print("Error: No data was processed successfully. Output file will not be created.", file=sys.stderr)
        sys.exit(1)

    # Save results to the specified output CSV file
    results_df = pd.DataFrame(results_data)
    try:
        results_df.to_csv(args.output_file, index=False)
        print(f"--- Results successfully saved to {args.output_file} ---")
    except Exception as e:
        print(f"Error: Could not write to output file '{args.output_file}'. Details: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculate acoustic indices from audio files.")
    
    parser.add_argument('--input-files', nargs='+', required=True, help="One or more paths to input audio WAV files.")
    parser.add_argument('--output-file', type=str, required=True, help="Path to save the output CSV file.")
    parser.add_argument('--noise-file', type=str, required=True, help="Path to the static noise reference WAV file.")
    
    # Parameters with defaults matching the original script
    parser.add_argument('--target-sr', type=int, default=48000, help="Target sample rate for audio processing.")
    parser.add_argument('--segment-duration', type=float, default=120.0, help="Duration of each audio segment in seconds.")
    parser.add_argument('--skip-duration', type=float, default=60.0, help="Time to skip between segments in seconds.")
    parser.add_argument('--total-segments', type=int, default=2, help="Maximum number of segments to process per file.")
    parser.add_argument('--snr-db', type=float, default=18.0, help="Signal-to-noise ratio in dB for noise reduction.")

    args = parser.parse_args()
    main(args)
import sys
import json
import subprocess
from pathlib import Path
import os
from glob import glob

def main():
    if len(sys.argv) < 2:
        print("Error: Path to payload.json not provided.", file=sys.stderr)
        sys.exit(1)

    payload_path = Path(sys.argv[1])
    if not payload_path.exists():
        print(f"Error: Payload file not found at {payload_path}", file=sys.stderr)
        sys.exit(1)

    with open(payload_path, 'r') as f:
        payload = json.load(f)

    # --- Define Paths Relative to This Script ---
    script_dir = Path(__file__).parent
    core_script_path = script_dir / "core_script.py"
    noise_file_path = script_dir / "static_noise.wav" # Bundled noise file

    if not noise_file_path.exists():
        print(f"Error: static_noise.wav not found in {script_dir}", file=sys.stderr)
        sys.exit(1)

    input_sources = payload['input_files']

    # --- NEW LOGIC: Expand directories into file lists ---
    expanded_input_files = []
    for source_path_str in input_sources:
        source_path = Path(source_path_str)
        if source_path.is_dir():
            # It's a directory, find all .wav files inside
            wav_files = glob(os.path.join(source_path, "**", "*.wav"), recursive=True)
            expanded_input_files.extend(wav_files)
        elif source_path.is_file() and source_path.name.lower().endswith('.wav'):
            # It's a single file, just add it
            expanded_input_files.append(str(source_path))

    if not expanded_input_files:
        print("Error: No .wav files found in the selected directories.", file=sys.stderr)
        sys.exit(1)
    # --- END NEW LOGIC ---

    # --- Construct the Command ---
    command = [
        sys.executable,
        str(core_script_path),
        '--output-file', payload['output_file'],
        '--static-noise-file', str(noise_file_path),
        '--lat', "28.53",  # Hardcoded for now, could be a parameter
        '--lon', "77.18",  # Hardcoded for now, could be a parameter
        '--min-confidence', str(payload.get('parameters', {}).get('min_confidence', 0.5)),
        '--input-files', *expanded_input_files
    ]

    # --- Execute the Command ---
    print(f"Wrapper: Executing command...\n{' '.join(command)}\n")
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='', file=sys.stderr)
        
    process.wait()
    
    if process.returncode != 0:
        print(f"\nWrapper: Core script failed (exit code {process.returncode}).", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nWrapper: Core script finished successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
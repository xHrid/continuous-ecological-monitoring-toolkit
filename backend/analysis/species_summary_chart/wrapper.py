import sys
import json
import subprocess
from pathlib import Path
import tempfile
import os
from glob import glob  # <-- Make sure this import is here

def run_subprocess(command, job_dir):
    """Helper function to run a subprocess and print output."""
    stdout_path = job_dir / f"{Path(command[2]).stem}_stdout.log"
    stderr_path = job_dir / f"{Path(command[2]).stem}_stderr.log"
    
    print(f"\n--- Running Command ---\n{' '.join(command)}\n")
    
    with open(stdout_path, 'w') as stdout_file, open(stderr_path, 'w') as stderr_file:
        process = subprocess.run(command, stdout=stdout_file, stderr=stderr_file, text=True, encoding='utf-8')

    # Print logs after completion
    print(f"--- {Path(command[2]).stem} STDOUT ---")
    with open(stdout_path, 'r') as f: print(f.read())
    print(f"--- {Path(command[2]).stem} STDERR ---")
    with open(stderr_path, 'r') as f: print(f.read(), file=sys.stderr)

    if process.returncode != 0:
        print(f"\nError: Subprocess {Path(command[2]).stem} failed with exit code {process.returncode}.", file=sys.stderr)
        return False
    return True


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

    job_dir = payload_path.parent
    parameters = payload.get('parameters', {})
    
    # --- Define paths ---
    # (Paths remain unchanged)
    birdnet_script_dir = Path(__file__).parent.parent / "birdnet_predict"
    birdnet_core_script_path = birdnet_script_dir / "core_script.py"
    noise_file_path = birdnet_script_dir / "static_noise.wav" 

    graphing_script_dir = Path(__file__).parent
    graphing_core_script_path = graphing_script_dir / "core_script.py"

    temp_csv_path = job_dir / "birdnet_results_temp.csv"
    final_plot_prefix = payload['output_file'].replace('.csv', '_plot')

    # --- NEW LOGIC: Expand directories into a file list ---
    # This must be done BEFORE Stage 1
    print("Expanding directories to find .wav files...")
    input_sources = payload['input_files']
    expanded_input_files = []
    
    for source_path_str in input_sources:
        full_source_path = str(Path(source_path_str).resolve()) 
        
        if os.path.isdir(full_source_path):
            search_pattern = os.path.join(full_source_path, "**", "*.wav")
            wav_files = glob(search_pattern, recursive=True)
            expanded_input_files.extend(wav_files)
        elif os.path.isfile(full_source_path) and full_source_path.lower().endswith('.wav'):
            expanded_input_files.append(full_source_path)

    if not expanded_input_files:
        print("Error: No .wav files found in the selected directories.", file=sys.stderr)
        sys.exit(1) # Fail fast
    print(f"Found {len(expanded_input_files)} .wav files to process.")
    # --- END NEW LOGIC ---


    # --- STAGE 1: Run BirdNet Predictions ---
    print("\n--- STAGE 1: Running BirdNet Predictions ---")
    birdnet_command = [
        sys.executable,
        str(birdnet_core_script_path),
        '--output-file', str(temp_csv_path),
        '--static-noise-file', str(noise_file_path),
        '--lat', "28.53", 
        '--lon', "77.18", 
        '--min-confidence', str(parameters.get('min_confidence_birdnet', 0.5)),
        '--input-files', *expanded_input_files  # <--- MODIFIED
    ]

    if not run_subprocess(birdnet_command, job_dir):
        print("BirdNet prediction stage failed. Aborting.", file=sys.stderr)
        sys.exit(1)

    if not temp_csv_path.exists() or temp_csv_path.stat().st_size == 0:
         print("Warning: BirdNet predictions did not produce an output file or the file is empty. Cannot generate graph.", file=sys.stderr)
         Path(payload['output_file']).touch() 
         sys.exit(0)


    # --- STAGE 2: Run Graph Generation ---
    # (This stage needs NO changes, as its input is temp_csv_path)
    print("\n--- STAGE 2: Generating Summary Chart ---")
    graphing_command = [
        sys.executable,
        str(graphing_core_script_path),
        '--input-csv', str(temp_csv_path), # <--- Input is the temp file
        '--output-prefix', final_plot_prefix,
        '--min-confidence-chart', str(parameters.get('min_confidence_chart', 0.3)),
        '--species-per-plot', str(parameters.get('species_per_plot', 50))
    ]

    if not run_subprocess(graphing_command, job_dir):
        print("Graph generation stage failed.", file=sys.stderr)
        try:
            os.remove(temp_csv_path)
            print(f"Cleaned up temporary file: {temp_csv_path}")
        except OSError as e:
            print(f"Warning: Could not remove temporary file {temp_csv_path}: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Cleanup ---
    try:
        os.remove(temp_csv_path)
        print(f"Cleaned up temporary file: {temp_csv_path}")
    except OSError as e:
        print(f"Warning: Could not remove temporary file {temp_csv_path}: {e}", file=sys.stderr)

    Path(payload['output_file']).touch() 
    print("\n--- Pipeline finished successfully ---")
    sys.exit(0)


if __name__ == "__main__":
    main()
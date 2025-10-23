import sys
import json
import subprocess
from pathlib import Path

def main():
    """
    This wrapper script acts as the bridge between the FastAPI backend and core_script.py.
    It reads a JSON payload, constructs the correct command-line arguments,
    and executes the core script, providing the fixed path for the noise file.
    """
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
    noise_file_path = script_dir / "noise.wav" 

    # --- Construct the Command ---
    command = [
        sys.executable,
        str(core_script_path),
        '--output-file', payload['output_file'],
        '--noise-file', str(noise_file_path),  
        '--input-files', *payload['input_files']
    ]

    # Add optional parameters from the payload if they exist
    parameters = payload.get('parameters', {})
    for key, value in parameters.items():
        if value is not None:
            # Converts snake_case (e.g., segment_duration) to kebab-case (--segment-duration)
            arg_name = '--' + key.replace('_', '-')
            command.extend([arg_name, str(value)])

    # --- Execute the Command ---
    print(f"Wrapper: Executing command...\n{' '.join(command)}\n")
    
    # Use Popen to stream stdout/stderr in real-time
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    
    # Print stdout and stderr as they come in, which helps with logging
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='', file=sys.stderr)
        
    process.wait()
    
    if process.returncode != 0:
        print(f"\nWrapper: Core script finished with an error (exit code {process.returncode}).", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nWrapper: Core script finished successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
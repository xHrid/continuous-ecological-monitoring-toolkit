import time
import json
import sys
from pathlib import Path

def main():
    """
    A dummy script that simulates a long-running analysis.
    It reads a list of file paths from a payload.json,
    waits for 3 minutes, and then writes the same list to results.json.
    """
    # The first command-line argument is the path to the job directory
    job_dir = Path(sys.argv[1])
    payload_file = job_dir / "payload.json"
    results_file = job_dir / "results.json"
    
    # Log that the job has started
    with open(results_file, 'w') as f:
        json.dump({"status": "running", "message": "Job started..."}, f)

    try:
        # Read the input files from the payload
        with open(payload_file, 'r') as f:
            payload = json.load(f)
            input_files = payload.get("input_files", [])

        # Simulate a long process
        time.sleep(180) # 3 minutes

        # Write the final results
        results = {
            "status": "completed",
            "processed_files": input_files,
            "message": "Successfully logged file names after a 3-minute delay."
        }
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

    except Exception as e:
        # Log any errors
        error_result = {"status": "failed", "error": str(e)}
        with open(results_file, 'w') as f:
            json.dump(error_result, f, indent=2)

if __name__ == "__main__":
    main()

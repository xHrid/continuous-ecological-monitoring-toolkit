# Pipeline
A full pipeline from audio data to acoustic graphs


## Continuous Ecological Monitoring using Bioacoustics Sensing

This project provides a generic bioacoustics monitoring pipeline for continuous ecological monitoring. The goal is to transform raw audio data into species-level and soundscape-level insights. The library allows researchers to deploy automated acoustic recorders, process the resulting recordings, and generate ecological metrics and visualizations.

Instead of being tied to a specific forest, site, or date, this pipeline is parameterized and can be used in any location for any monitoring campaign.


### Inputs
The project's primary data inputs are raw audio recordings and location-specific metadata.

#### Raw Audio Recordings
- WAV/FLAC/MP3 files containing soundscape data.
#### Metadata File 
- A CSV/JSON with site-specific information such as:
  - site_id (unique identifier)
  - latitude, longitude (or region identifier)
  - habitat_description (optional)
  - recorder_model, sample_rate, duty_cycle (optional, for reproducibility)
  - start_date, end_date of deployment


### Acoustic Data Collection

The following parameters are configurable by the user and should be included in the metadata file or CLI arguments:
1. Recording Device Model (e.g., Song Meter Micro, Audiomoth, etc.)
2. Duty Cycle (recording schedule, e.g., 2 minutes on / 4 minutes off)
3. Deployment Duration (start and end date)
4. Number of Sites and Site Selection Criteria (NDVI stratification, habitat zones, random sampling, etc.)

### Monitoring Spot Characteristics

Each monitoring spot should have associated attributes (e.g., vegetation density, proximity to water, canopy cover) to allow downstream correlation with acoustic metrics. These are provided by the user as part of the metadata input.

### Outputs and Analysis
The pipeline produces two major categories of outputs:

### Species-Level Analysis

BirdNet Identifications
- Input: Raw audio files
- Process: Passes each file through the BirdNet model to obtain probabilistic species identifications.
- Output: CSV with columns: [timestamp, site_id, species, confidence].

Reliability assessment is done by comparing against a reference species list (e.g., eBird regional checklist provided by user):
- Confirmed Present (True Positives): Species found on both the reference list and detections.
- Confirmed Absent / Missed (False Negatives): On list but not detected.
Implausible Errors (False Positives): Detected but not on list (flagged for review).
- Implausible Errors (False Positives): Detected but not on list (flagged for review).

- Hourly Activity Heat Maps:

  - Normalized Heat Maps: These maps show the proportion of a species' total daily activity per hour. The data is normalized for each species, allowing for a fair comparison of activity timing regardless of how common or vocal a species is.<img width="1004" height="508" alt="Screenshot 2025-09-13 at 5 20 41 AM" src="https://github.com/user-attachments/assets/88aa3bbe-fcb4-4783-98aa-2d35251368c5" />


  - Non-Normalized Heat Maps: These heat maps display the raw average number of detections per hour for each species. They are crucial for identifying which species contribute the most to the overall soundscape at any given time.
<img width="1004" height="508" alt="Screenshot 2025-09-13 at 5 21 56 AM" src="https://github.com/user-attachments/assets/5e207d86-8a56-4978-86f7-bac5f427e084" />


- "Stickiness" Metrics: These metrics quantify the predictability of species' behavior.

  - Temporal Stickiness: Measures the regularity of a species' daily activity pattern across consecutive days using a Spearman rank correlation of hourly detection counts. A high score indicates a predictable schedule.<img width="597" height="483" alt="Screenshot 2025-09-13 at 5 24 23 AM" src="https://github.com/user-attachments/assets/cfb1a41e-a482-4064-8247-45c0c5e07c52" />



  - Spatial Stickiness: Measures a species' affinity for a specific location. It's calculated by comparing the spot ranking (based on detection counts) from one day to the next.
  
<img width="525" height="581" alt="Screenshot 2025-09-13 at 5 23 47 AM" src="https://github.com/user-attachments/assets/2dbce094-8a00-4e7f-b6aa-86f409ca6b3e" />


  - Temporal-Spatial Stickiness: A combined metric that assesses the predictability of a species' hourly activity at a specific spot across multiple days.
<img width="597" height="483" alt="Screenshot 2025-09-13 at 5 24 43 AM" src="https://github.com/user-attachments/assets/e514a1ac-663c-4ba4-b19a-0781269acc74" />

### Soundscape-Level Analysis (Acoustic Indices)

Acoustic indices are single-value metrics that provide a broad, rapid assessment of the soundscape's characteristics. The following indices were computed hourly for each location:

- Acoustic Diversity Index (ADI): Measures how evenly sound energy is distributed across frequency bands. A high ADI suggests a rich and healthy ecosystem with a wide variety of vocalizing species.
- Acoustic Complexity Index (ACI): Measures rapid variations in sound intensity over time. High ACI often correlates with a complex biological soundscape.
- Acoustic Evenness Index (AEI): Evaluates whether acoustic energy is evenly distributed or concentrated in a few frequency bands. A high AEI indicates a balanced soundscape.
 
- Normalized Difference Soundscape Index (NDSI): Compares biological sound energy (E_Bio) to human-made noise energy (E_Anthro) in different frequency ranges.

- Mid Frequency Cover (MFC): Measures the proportion of the soundscape with a strong mid-frequency signal, which is typically a signature of birds and insects.

- Clustered Level of Sound (CLS): Assesses the balance of energy among different frequency clusters. A high CLS indicates a diverse set of sound sources.<img width="1048" height="417" alt="Screenshot 2025-09-13 at 5 30 12 AM" src="https://github.com/user-attachments/assets/c96643b9-2f72-4597-ab42-551d13cc288d" />

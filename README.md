# Field Data Collector with Dynamic Geovisualization

Turn any location on Earth into an interactive, data-rich field site. This application is a self-hosted data collection tool that puts you in control; from generating custom satellite maps for your study area to owning the data you collect.

Designed for ecologists, geologists, and field researchers, this app bridges the gap between simple GPS loggers and complex GIS platforms. Its standout feature is the ability to automatically create land-cover stratification maps using Google Earth Engine for any area you define with a KML file. Alongside that, it supports multimedia observations, route recording, and external data integration — all saved locally in an organized format for long-term use.

All your data — spots, routes, sites, overlays, photos, and audio — are stored directly on your computer, giving you complete ownership, privacy, and flexibility.

---

## Core Use Cases

This tool can support a wide range of fieldwork and research:

* **Ecological Surveys**: Track wildlife sightings, nesting sites, or vegetation patterns. Each spot can store notes, images, audio, and other relevant data.
* **Urban Planning**: Document infrastructure, land use, or areas requiring maintenance.
* **Geological Studies**: Record outcrops, sampling locations, and field notes.
* **Personal Projects**: Maintain a private, geotagged journal of hikes, explorations, or memories.

---

## Key Features

* **Dynamic Site Creation**: Upload a KML file to instantly define your study area anywhere in the world.
* **Automated Land-Cover Maps**: Generate stratified land-cover overlays via Google Earth Engine with multiple clustering levels for comparison.
* **Rich Spot Logging**: Add points of interest with detailed, time-based observations.
* **Multimedia Support**: Attach notes, photos, and audio recordings to any observation.
* **Route Tracking**: Record and save GPS-based routes, ideal for surveys or exploration paths.
* **External Data Import**: Attach other datasets or media — such as CSVs, PDFs, or images — to a specific spot for better organization and context.
* **Background Processing**: All long-running tasks (like GEE stratification or analysis scripts) run safely in the background, letting you continue using the app while processing completes.
* **Local Data Ownership**: Everything is stored directly on your machine in a clean, structured format — no external servers, no dependencies.
* **Persistent Memory**: All spots, routes, and sites remain accessible across sessions.
* **Script-Based Analysis**: Run analysis scripts (e.g., acoustic or data summaries) directly from the app. Simply choose a script, select input files, and the system will process them in the background, saving results automatically.

---

## How the Stratification Works

The automated stratification is the heart of this application, powered by Google Earth Engine. It transforms your boundary file into a meaningful land-cover map in just a few steps:

1. **Area of Interest (AOI)**: Upload a KML file to define the boundary.
2. **Satellite Imagery Source**: The app uses Google’s Satellite Embeddings (V1) — compact representations of Sentinel-2 imagery optimized for analysis.
3. **Vegetation Masking**: Based on Google’s Dynamic World dataset, the system focuses on vegetated areas (trees by default).
4. **Unsupervised Clustering**: k-Means clustering groups spectrally similar pixels into land-cover clusters, repeated for each selected cluster level.
5. **Map Generation**: Distinct colors are assigned to each cluster, clipped to your site boundary, and returned as PNG overlays ready to view on the map.

---

## Workflow

The app is designed for real-world fieldwork and supports two main working modes:

### Mode A: Local-First / Field-Ready

* **Prepare at home:** Open the app while online and explore your area of interest. Map tiles will automatically cache for offline use.
* **In the field:** Run the Python server on your laptop, share its Wi-Fi hotspot, and connect through your phone or tablet.
* **Collect & save:** Add spots, observations, and routes. Everything is stored locally and safely.

### Mode B: Remote Access

* **Run from home or lab:** Start the server and use a tunneling service like ngrok to make it accessible from anywhere.
* **Connect remotely:** Use the generated URL on your device.
* **Centralized data:** Observations collected remotely are stored directly on your main computer or lab system.

---

## Tech Stack

* **Backend:** Python + FastAPI
* **Frontend:** Vanilla JavaScript, HTML5, CSS3
* **Maps:** Leaflet.js for interactive mapping
* **Geospatial Processing:** Google Earth Engine for stratification and analysis

---

## Installation

### Prerequisites

* Python 3.8 or newer
* pip (Python package manager)
* A Google Earth Engine account
* (Optional) ngrok for remote access

### 1. Clone the Repository

```bash
git clone https://github.com/xHrid/continuous-ecological-monitoring-toolkit.git
cd continuous-ecological-monitoring-toolkit
```

### 2. Set Up the Environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 3. Authenticate with Google Earth Engine

```bash
earthengine authenticate
```

Follow the prompts to sign in with Google and provide the authorization code.

### 4. Run the Server

```bash
uvicorn backend.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 5. (Optional) Enable Remote Access

For this, we will need to set up ngrok on our system.

What ngrok does is called tunneling. ngrok is a tool that creates a secure, encrypted tunnel between your local machine and a public URL.

Installing ngrok itself requires a guide, which is readily available on the internet. Please follow one and install it.

```bash
ngrok http 8000
```

Use the generated link to access your server from any device via internet.

---

## Using the App

### Adding a Site

1. Click **Add Site**.
2. Provide a name and upload a KML file.
3. Select the number of cluster levels for stratification.
4. Submit and wait for your overlay to appear on the map.

### Creating Spots and Observations

* Click **Add Spot**, fill in the form, and save.
* Each spot can store notes, images, audio, and multiple observations over time.
* Open a spot to view or extend its timeline with more data.

### Recording Routes

* Click **Record Route**, walk or drive your path, and save it with a name.
* Routes can be revisited or followed later for repeat surveys.

### Importing External Data

* Use the **Import** button to attach additional media or datasets to a spot — perfect for linking lab data, spreadsheets, or past reports.
* Uploaded files are safely organized and stored within that spot’s folder.

### Running Analysis Scripts

* Click **Analysis** to view all available processing scripts.
* Select a script, choose the input files (from your spots or external data), and click **Run**.
* The script runs in the background and reports back when finished, with results saved automatically to your `data/processing` folder.

---

## Data Storage

All data is saved locally under the `data/` directory in a clear, human-readable structure:

* `sites/`: Stores site metadata and generated stratification overlays.
* `spots/`: Contains each spot’s metadata, images, audio, and imported data.
* `routes/`: JSON files for recorded routes.
* `processing/jobs/`: Stores background analysis jobs, including inputs, outputs, and logs.

This structure ensures everything remains portable, transparent, and future-proof.

---

## Customization Guide

This toolkit is designed to be fully adaptable to your workflow.

### Frontend Customization

* **UI Text & Forms** (`public/index.html`):

  * Change titles, placeholders, and labels directly in HTML.
  * Add new fields as needed and map them to the backend models.
* **Styling** (`public/styles/`):

  * Edit colors, layouts, and themes via CSS files.
* **Map Settings** (`public/scripts/map.js`):

  * Adjust the default zoom, map center, or tile provider to suit your study region.

### Backend Customization

* **Analysis Scripts** (`backend/analysis/`):

  * Add new scripts or modify existing ones. Each script includes a `manifest.json` that defines its inputs and outputs.
* **Data Models & API** (`backend/core/` and `backend/api/`):

  * Extend the data model or create new endpoints to suit your project’s needs.

---

## Data Privacy

Everything you collect stays on your device.
There are no third-party uploads, logins, or hidden cloud dependencies.
You own the data — permanently.

---

## Summary

This Field Data Collector is a practical, flexible toolkit for scientists and explorers who need to document the world — from small-scale observations to full study sites — with complete control over their data.
Whether you’re analyzing acoustic indices, mapping vegetation patterns, or simply building your own ecological dataset, it’s your field companion for structured, private, and dynamic data collection.

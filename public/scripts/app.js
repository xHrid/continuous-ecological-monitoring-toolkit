const addSiteForm = document.getElementById("add-site-form");
const addSiteStatus = document.getElementById("add-site-status");
const kmlFileNameDisplay = document.getElementById("kml-file-name");
const audioToggle = document.getElementById("audio-toggle");
const audioPlayback = document.getElementById("audioPlayback");

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordedAudioBlob = null; 


addSiteForm.onsubmit = async (e) => {
    e.preventDefault();
    addSiteStatus.textContent = "Processing with Google Earth Engine, this may take a minute...";
    const formData = new FormData(addSiteForm);

    try {
        const response = await fetch('/api/add-site', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorResult = await response.json();
            throw new Error(errorResult.message || 'An unknown error occurred.');
        }

        const siteData = await response.json();
        alert(siteData.message);

        displaySiteControls(siteData); 

        addSiteStatus.textContent = "";
        addSiteForm.reset();
        kmlFileNameDisplay.textContent = "No file chosen";
        document.getElementById("add-site-popup-form").style.display = "none";

    } catch (error) {
        console.error("Error submitting site:", error);
        addSiteStatus.textContent = `Error: ${error.message}`;
        alert(`Failed to add site: ${error.message}`);
    }
};


audioToggle.addEventListener("click", async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                recordedAudioBlob = new Blob(audioChunks, { type: "audio/webm" });
                audioPlayback.src = URL.createObjectURL(recordedAudioBlob);
                stream.getTracks().forEach((track) => track.stop());
            };
            mediaRecorder.start();
            isRecording = true;
            audioToggle.classList.add("recording");
        } catch (err) {
            console.error("Microphone error:", err);
            alert("Could not access the microphone. Please check your browser permissions.");
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        audioToggle.classList.remove("recording");
    }
});


async function loadExistingSites() {
    try {
        const response = await fetch('/api/get-sites');
        if (!response.ok) {
            throw new Error('Failed to fetch existing sites.');
        }
        const sites = await response.json();
        const controlsContainer = document.getElementById("stratification-controls");
        controlsContainer.innerHTML = ''; 
        sites.forEach(site => displaySiteControls(site)); 
    } catch (error) {
        console.error("Error loading existing sites:", error);
        alert(error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadExistingSites();
});


const importMediaForm = document.getElementById('import-media-form');

async function handleOpenImportModal() {
    try {
        const response = await fetch('/api/get-spots');
        if (!response.ok) throw new Error('Failed to fetch spots.');
        const spots = await response.json();
        populateSpotSelector(spots); 
        document.getElementById('import-media-popup').style.display = 'flex';
        updatePathPreview(); 
    } catch (error) {
        console.error('Error opening import modal:', error);
        alert('Could not load spots for import. Please try again.');
    }
}
window.handleOpenImportModal = handleOpenImportModal;

importMediaForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    const selectedSpots = Array.from(document.querySelectorAll('#spot-selection-container input[type="checkbox"]:checked')).map(cb => cb.value);
    if (selectedSpots.length === 0) {
        alert('Please select at least one spot.');
        return;
    }
    const files = document.getElementById('external-file-input').files;
    if (files.length === 0) {
        alert('Please select at least one file to import.');
        return;
    }
    const formData = new FormData();
    selectedSpots.forEach(spotName => formData.append('spot_names', spotName));
    for (const file of files) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch('/api/import-external-media', {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            alert('Media imported successfully!');
            document.getElementById('import-media-popup').style.display = 'none';
            importMediaForm.reset();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to import media.');
        }
    } catch (error) {
        console.error('Error importing media:', error);
        alert(`An error occurred: ${error.message}`);
    }
});

const analysisBtn = document.getElementById('analysis-btn');
const jobsBtn = document.getElementById('jobs-btn');
const analysisPopup = document.getElementById('analysis-popup');
const jobsPopup = document.getElementById('jobs-popup');
const cancelAnalysisBtn = document.getElementById('cancel-analysis-btn');
const closeJobsBtn = document.getElementById('close-jobs-btn');
const refreshJobsBtn = document.getElementById('refresh-jobs-btn');
const analysisForm = document.getElementById('analysis-form');
const scriptSelect = document.getElementById('analysis-script-select');
const scriptDescription = document.getElementById('analysis-description');
const fileSelectionContainer = document.getElementById('analysis-file-selection');
const jobsListContainer = document.getElementById('jobs-list');

let availableScripts = []; 

analysisBtn.addEventListener('click', openAnalysisModal);
jobsBtn.addEventListener('click', openJobsModal);
cancelAnalysisBtn.addEventListener('click', () => analysisPopup.style.display = 'none');
closeJobsBtn.addEventListener('click', () => jobsPopup.style.display = 'none');
refreshJobsBtn.addEventListener('click', populateJobsList);

scriptSelect.addEventListener('change', () => {
    const selectedScript = availableScripts.find(s => s.id === scriptSelect.value);
    scriptDescription.textContent = selectedScript ? selectedScript.description : '';
});

analysisForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const selectedFiles = Array.from(fileSelectionContainer.querySelectorAll('input:checked'))
                               .map(input => input.value);

    if (!scriptSelect.value) {
        alert('Please select an analysis script.');
        return;
    }
    if (selectedFiles.length === 0) {
        alert('Please select at least one input file.');
        return;
    }

    const jobRequest = {
        script_id: scriptSelect.value,
        input_files: selectedFiles,
        spot_names: [] 
    };

    try {
        const response = await fetch('/api/analysis/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(jobRequest)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to start job.');
        }

        const result = await response.json();
        alert(`Job '${result.job_id}' started successfully!`);
        analysisPopup.style.display = 'none';
        analysisForm.reset();
        
    } catch (error) {
        console.error('Error starting analysis job:', error);
        alert(`Error: ${error.message}`);
    }
});


async function openAnalysisModal() {
    try {
        const scriptsResponse = await fetch('/api/analysis/scripts');
        if (!scriptsResponse.ok) throw new Error('Could not fetch scripts.');
        availableScripts = await scriptsResponse.json();
        
        scriptSelect.innerHTML = '<option value="">Select a script...</option>';
        availableScripts.forEach(script => {
            const option = document.createElement('option');
            option.value = script.id;
            option.textContent = script.name;
            scriptSelect.appendChild(option);
        });
        scriptDescription.textContent = '';

        const filesResponse = await fetch('/api/analysis/external-files');
        if (!filesResponse.ok) throw new Error('Could not fetch external files.');
        const files = await filesResponse.json();

        fileSelectionContainer.innerHTML = '';
        if (files.length === 0) {
            fileSelectionContainer.innerHTML = '<p>No external files found to analyze.</p>';
        } else {
            files.forEach(file => {
                const id = `file-check-${file.replace(/[^a-zA-Z0-9]/g, "")}`;
                const div = document.createElement('div');
                div.innerHTML = `
                    <input type="checkbox" id="${id}" value="${file}">
                    <label for="${id}" style="font-size: 0.9rem;">${file}</label>
                `;
                fileSelectionContainer.appendChild(div);
            });
        }
        
        analysisPopup.style.display = 'flex';

    } catch (error) {
        console.error('Error preparing analysis modal:', error);
        alert(`Error: ${error.message}`);
    }
}

async function openJobsModal() {
    jobsPopup.style.display = 'flex';
    await populateJobsList();
}

async function populateJobsList() {
    jobsListContainer.innerHTML = '<p>Loading jobs...</p>';
    try {
        const response = await fetch('/api/analysis/jobs');
        if (!response.ok) throw new Error('Failed to fetch job statuses.');
        const jobs = await response.json();

        jobsListContainer.innerHTML = '';
        if (jobs.length === 0) {
            jobsListContainer.innerHTML = '<p>No jobs have been run yet.</p>';
            return;
        }

        jobs.forEach(job => {
            const jobDiv = document.createElement('div');
            jobDiv.className = 'external-data-item';
            let statusClass = '';
            if (job.status === 'completed') statusClass = 'status-completed';
            if (job.status === 'failed') statusClass = 'status-failed';
            if (job.status === 'running' || job.status === 'queued') statusClass = 'status-running';

            jobDiv.innerHTML = `
                <div class="file-info">
                    <strong>Job ID:</strong> ${job.job_id}<br>
                    <strong>Script:</strong> ${job.script_id}<br>
                    <strong>Submitted:</strong> ${new Date(job.submitted_at).toLocaleString()}
                </div>
                <div class="file-actions">
                    <span class="job-status ${statusClass}">${job.status}</span>
                </div>
            `;
            jobsListContainer.appendChild(jobDiv);
        });

    } catch (error) {
        console.error('Error populating jobs list:', error);
        jobsListContainer.innerHTML = `<p style="color: red;">${error.message}</p>`;
    }
}

const style = document.createElement('style');
style.innerHTML = `
.job-status { padding: 3px 8px; border-radius: 12px; color: white; font-weight: bold; font-size: 0.9rem; }
.status-completed { background-color: #28a745; }
.status-failed { background-color: #dc3545; }
.status-running { background-color: #007bff; }
`;
document.head.appendChild(style);
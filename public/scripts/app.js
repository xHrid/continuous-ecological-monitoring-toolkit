// public/scripts/app.js

// --- DOM Element Selection ---
const addSiteForm = document.getElementById("add-site-form");
const addSiteStatus = document.getElementById("add-site-status");
const kmlFileNameDisplay = document.getElementById("kml-file-name");
const audioToggle = document.getElementById("audio-toggle");
const audioPlayback = document.getElementById("audioPlayback");

// --- Media Recording State ---
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordedAudioBlob = null; // This variable needs to be accessible to spots.js

// --- CORE APPLICATION LOGIC ---

/**
 * Handles the submission of the "Add Site" form.
 * It sends the data to the server and then triggers the UI update.
 */
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

        displaySiteControls(siteData); // Call the function from map.js to update the UI

        // Reset UI elements after successful submission
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

/**
 * Handles the logic for recording audio from the user's microphone.
 */
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

/**
 * Fetches the list of existing sites from the server when the app loads.
 */
async function loadExistingSites() {
    try {
        const response = await fetch('/api/get-sites');
        if (!response.ok) {
            throw new Error('Failed to fetch existing sites.');
        }
        const sites = await response.json();
        const controlsContainer = document.getElementById("stratification-controls");
        controlsContainer.innerHTML = ''; // Clear container before loading
        sites.forEach(site => displaySiteControls(site)); // Display controls for each site
    } catch (error) {
        console.error("Error loading existing sites:", error);
        alert(error.message);
    }
}

// --- INITIALIZATION ---
// This is the entry point of the application.
document.addEventListener('DOMContentLoaded', () => {
    loadExistingSites();
});

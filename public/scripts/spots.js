// public/scripts/spots.js

/**
 * Converts a file or blob object into a Base64 encoded string.
 * This is used to transport the file data to the server within a JSON payload.
 * @param {File|Blob} file The file or blob to convert.
 * @returns {Promise<string|null>} A promise that resolves with the Base64 data URL, or null if no file is provided.
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            resolve(null);
            return;
        }
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
    });
}


/**
 * Handles the submission of the spot form for both new spots and new observations.
 */
document.getElementById("spot-form").onsubmit = async function (e) {
    e.preventDefault();

    const form = e.target;
    const spotId = form.dataset.spotId || null; // Get spotId if we are updating
    const name = form.name.value.trim();
    const birds = form.birds.value.trim();
    const desc = form.description.value.trim();
    const imageFile = form.image.files[0];
    const audioBlob = recordedAudioBlob;

    if (!name && !birds && !desc && !imageFile && !audioBlob) {
        document.getElementById("status").textContent = "Please fill at least one field.";
        return;
    }

    try {
        document.getElementById("status").textContent = "Processing and saving...";

        const [imageBase64, audioBase64] = await Promise.all([
            fileToBase64(imageFile),
            fileToBase64(audioBlob)
        ]);

        // This object now includes the spotId if it's an update
        const payload = {
            spotId, // Will be null for new spots
            name,
            latitude: currLat,
            longitude: currLng,
            birds,
            description: desc,
            image_data_url: imageBase64,
            audio_data_url: audioBase64
        };

        const response = await fetch('/api/save-spot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorInfo = await response.json();
            throw new Error(errorInfo.message || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        alert(result.message);

        // Reset the form and UI
        form.reset();
        delete form.dataset.spotId; // Clear the spotId from the form
        document.getElementById("popup-form").style.display = "none";
        document.getElementById("status").textContent = "";
        recordedAudioBlob = null;
        if (window.imageLabel) {
            imageLabel.classList.remove("selected");
        }

        // Refresh the spots on the map to show the new data
        displaySpots();
        // If we just updated a spot, re-open its details to see the new observation
        if(spotId) {
            const updatedSpot = allSpots.find(s => s.spotId === spotId);
            if(updatedSpot) showSpotDetails(updatedSpot);
        }


    } catch (error) {
        console.error("Error adding observation:", error);
        document.getElementById("status").textContent = `Error: ${error.message}`;
        alert(`Failed to save observation: ${error.message}`);
    }
};

// Global variables
let allSpots = [];
spotsLayer = null;

/**
 * Fetches all spot data from the server and displays them on the map.
 */
async function displaySpots() {
  try {
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
    }

    const response = await fetch('/api/get-spots');
    if (!response.ok) throw new Error('Failed to fetch spots.');
    
    allSpots = await response.json();

    spotsLayer = L.layerGroup().addTo(map);
    const isMobile = window.innerWidth <= 768;
    let radius = isMobile ? 16 : 10;

    allSpots.forEach(spot => {
      const circle = L.circleMarker([spot.latitude, spot.longitude], {
        radius: radius,
        fillColor: "#3388ff",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8,
      }).addTo(spotsLayer);

      circle.on("click", () => showSpotDetails(spot));
      circle.on("mouseover", () => circle.setStyle({ fillOpacity: 1, weight: 2 }));
      circle.on("mouseout", () => circle.setStyle({ fillOpacity: 0.8, weight: 1 }));
    });

  } catch (error) {
    console.error("Error fetching spots: ", error);
    alert(error.message);
  }
}

/**
 * Displays the details panel with a timeline of all observations for a spot.
 * @param {object} spot The full spot object, including its `observations` array.
 */
function showSpotDetails(spot) {
  const menu = document.getElementById("spot-details-menu");
  const content = document.getElementById("spot-details-content");

  // Sort observations, newest first
  const sortedObservations = spot.observations.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  // Build the HTML for the timeline from the observations array
  const timelineHtml = sortedObservations.map(obs => {
      const birds = obs.birds
        ? `<ul>${obs.birds.split(',').map(b => `<li>${b.trim()}</li>`).join('')}</ul>`
        : "<p>No birds recorded</p>";

      // Use the new file paths for media
      const image = obs.imagePath
        ? `<img src="${obs.imagePath}" alt="Spot image" style="max-width: 100%; margin-top: 5px; border-radius: 4px;">`
        : "";

      const audio = obs.audioPath
        ? `<audio controls src="${obs.audioPath}" style="width: 100%; margin-top: 5px;"></audio>`
        : "";

      return `
        <div class="spot-entry" style="border: 1px solid #ccc; padding: 8px; margin-top: 10px; border-radius: 8px;">
          <p><small><strong>Observed on:</strong> ${new Date(obs.createdAt).toLocaleString()}</small></p>
          <p><strong>Description:</strong> ${obs.description || "No description"}</p>
          <p><strong>Birds:</strong></p>
          ${birds}
          ${image}
          ${audio}
        </div>
      `;
    }).join("");

  // Update the details panel content
  content.innerHTML = `
    <h2 id="spot-name">${spot.name}</h2>
    <p><span id="spot-coordinates">(${spot.latitude.toFixed(6)}, ${spot.longitude.toFixed(6)})</span></p>
    ${timelineHtml}
    <button id="add-more-button" style="margin-top: 20px;">Add More</button>
  `;

  // Re-attach the "Add More" listener
  document.getElementById("add-more-button").addEventListener("click", () => {
    const form = document.getElementById("spot-form");
    
    // Store the spotId on the form itself to be used on submit
    form.dataset.spotId = spot.spotId;
    
    // Pre-fill and lock the name field
    form.name.value = spot.name;
    form.name.readOnly = true;

    // Set coordinates and show the form
    currLat = spot.latitude;
    currLng = spot.longitude;
    document.getElementById("popup-form").style.display = "flex";
  });

  menu.classList.add("open");
}

// --- EVENT LISTENERS ---

document.getElementById('display-spots').addEventListener('change', function(e) {
  if (this.checked) {
    displaySpots();
  } else {
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
      spotsLayer = null;
    }
  }
});

document.getElementById("close-spot-details").addEventListener("click", () => {
  document.getElementById("spot-details-menu").classList.remove("open");
});

// When the main popup form is closed, reset its state
document.getElementById("close-form").addEventListener("click", () => {
    const form = document.getElementById("spot-form");
    form.reset();
    form.name.readOnly = false;
    delete form.dataset.spotId; // Important: clear the spotId
});

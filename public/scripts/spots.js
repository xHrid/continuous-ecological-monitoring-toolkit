const audioPlayback = document.getElementById("audioPlayback");
const audioToggle = document.getElementById("audio-toggle");
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordedAudioBlob = null;

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
      alert(
        "Could not access the microphone. Please check your browser permissions."
      );
    }
  } else {
    mediaRecorder.stop();
    isRecording = false;
    audioToggle.classList.remove("recording");
  }
});

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

document.getElementById("spot-form").onsubmit = async function (e) {
  e.preventDefault();

  const form = e.target;
  const spotId = form.dataset.spotId || null;
  const name = form.name.value.trim();
  const birds = form.birds.value.trim();
  const desc = form.description.value.trim();
  const imageFile = form.image.files[0];
  const audioBlob = recordedAudioBlob;

  if (!name && !birds && !desc && !imageFile && !audioBlob) {
    document.getElementById("status").textContent =
      "Please fill at least one field.";
    return;
  }

  try {
    document.getElementById("status").textContent = "Processing and saving...";

    const [imageBase64, audioBase64] = await Promise.all([
      fileToBase64(imageFile),
      fileToBase64(audioBlob),
    ]);

    const payload = {
      spotId,
      name,
      latitude: currLat,
      longitude: currLng,
      birds,
      description: desc,
      image_data_url: imageBase64,
      audio_data_url: audioBase64,
    };

    const response = await fetch("/api/save-spot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorInfo = await response.json();
      throw new Error(
        errorInfo.message || `HTTP error! status: ${response.status}`
      );
    }

    const result = await response.json();
    alert(result.message);

    form.reset();
    delete form.dataset.spotId;
    document.getElementById("popup-form").style.display = "none";
    document.getElementById("status").textContent = "";
    recordedAudioBlob = null;
    if (window.imageLabel) {
      imageLabel.classList.remove("selected");
    }

    displaySpots();
    if (spotId) {
      const updatedSpot = allSpots.find((s) => s.spotId === spotId);
      if (updatedSpot) showSpotDetails(updatedSpot);
    }
  } catch (error) {
    console.error("Error adding observation:", error);
    document.getElementById("status").textContent = `Error: ${error.message}`;
    alert(`Failed to save observation: ${error.message}`);
  }
};

let allSpots = [];
spotsLayer = null;

async function displaySpots() {
  try {
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
    }

    const response = await fetch("/api/get-spots");
    if (!response.ok) throw new Error("Failed to fetch spots.");

    allSpots = await response.json();

    spotsLayer = L.layerGroup().addTo(map);
    const isMobile = window.innerWidth <= 768;
    let radius = isMobile ? 16 : 10;

    allSpots.forEach((spot) => {
      const circle = L.circleMarker([spot.latitude, spot.longitude], {
        radius: radius,
        fillColor: "#3388ff",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8,
      }).addTo(spotsLayer);

      circle.on("click", () => showSpotDetails(spot));
      circle.on("mouseover", () =>
        circle.setStyle({ fillOpacity: 1, weight: 2 })
      );
      circle.on("mouseout", () =>
        circle.setStyle({ fillOpacity: 0.8, weight: 1 })
      );
    });
  } catch (error) {
    console.error("Error fetching spots: ", error);
    alert(error.message);
  }
}

function showSpotDetails(spot) {
  const menu = document.getElementById("spot-details-menu");
  const content = document.getElementById("spot-details-content");

  // --- Part 1: Standard Observation Timeline ---
  const sortedObservations = spot.observations
    .filter((obs) => obs.type !== "external_import") // Exclude external data from main timeline
    .sort(
      (a, b) =>
        new Date(b.createdAt || b.timestamp) -
        new Date(a.createdAt || a.timestamp)
    );

  const timelineHtml = sortedObservations
    .map((obs) => {
      const obsDate = new Date(obs.createdAt || obs.timestamp).toLocaleString();
      const birds = obs.birds
        ? `<ul>${obs.birds
            .split(",")
            .map((b) => `<li>${b.trim()}</li>`)
            .join("")}</ul>`
        : "<p>No birds recorded</p>";
      const image = obs.imagePath
        ? `<img src="${obs.imagePath}" alt="Spot image" style="max-width: 100%; margin-top: 5px; border-radius: 4px;">`
        : "";
      const audio = obs.audioPath
        ? `<audio controls src="${obs.audioPath}" style="width: 100%; margin-top: 5px;"></audio>`
        : "";

      return `
            <div class="spot-entry" style="border: 1px solid #ccc; padding: 8px; margin-top: 10px; border-radius: 8px;">
                <p><small><strong>Observed on:</strong> ${obsDate}</small></p>
                <p><strong>Description:</strong> ${
                  obs.description || obs.notes || "No description"
                }</p>
                <p><strong>Birds:</strong></p>
                ${birds}
                ${image}
                ${audio}
            </div>
        `;
    })
    .join("");

  const externalObservations = spot.observations.filter(
    (obs) => obs.type === "external_import"
  );
  const hasExternalData = externalObservations.length > 0;

  content.innerHTML = `
        <h2 id="spot-name">${spot.name}</h2>
        <p><span id="spot-coordinates">(${spot.latitude.toFixed(
          6
        )}, ${spot.longitude.toFixed(6)})</span></p>
        <button id="show-external-data-btn" class="show-external-data-btn" ${
          !hasExternalData ? "disabled" : ""
        }>
            Show External Media
        </button>
        <hr>
        ${timelineHtml || "<p>No field observations recorded yet.</p>"}
        <button id="add-more-button" style="margin-top: 20px;">Add More</button>
    `;

  document.getElementById("add-more-button").addEventListener("click", () => {
    const form = document.getElementById("spot-form");
    form.dataset.spotId = spot.spotId;
    form.name.value = spot.name;
    form.name.readOnly = true;
    currLat = spot.latitude;
    currLng = spot.longitude;
    document.getElementById("popup-form").style.display = "flex";
  });

  if (hasExternalData) {
    document
      .getElementById("show-external-data-btn")
      .addEventListener("click", () => {
        const viewer = document.getElementById("external-data-viewer");
        const dataContent = document.getElementById("external-data-content");

        const filesByDate = externalObservations.reduce((acc, obs) => {
          const date = new Date(obs.timestamp).toLocaleDateString();
          if (!acc[date]) {
            acc[date] = [];
          }
          obs.media.forEach((file) => acc[date].push(file.path));
          return acc;
        }, {});

        const viewerHtml = Object.entries(filesByDate)
          .map(([date, files]) => {
            const fileLinks = files
              .map((path) => {
                const fileName = path.split("/").pop();
                return `<a href="/${path}" target="_blank">${fileName}</a>`;
              })
              .join("");
            return `<h4>${date}</h4>${fileLinks}`;
          })
          .join("");

        dataContent.innerHTML = viewerHtml;
        viewer.style.display = "flex";
      });
  }

  document
    .getElementById("close-external-viewer")
    .addEventListener("click", () => {
      document.getElementById("external-data-viewer").style.display = "none";
    });

  menu.classList.add("open");
}

document
  .getElementById("display-spots")
  .addEventListener("change", function (e) {
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

document.getElementById("close-form").addEventListener("click", () => {
  const form = document.getElementById("spot-form");
  form.reset();
  form.name.readOnly = false;
  delete form.dataset.spotId;
});

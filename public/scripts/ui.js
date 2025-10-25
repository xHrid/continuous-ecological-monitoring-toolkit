const notifiedJobIds = new Set();
const toastElement = document.getElementById("toast-notification");

function showToast(message, status) {
  toastElement.textContent = message;
  toastElement.className = `show ${status}`; // 'success' or 'failed'

  // Hide after 5 seconds
  setTimeout(() => {
    toastElement.className = "";
  }, 5000);
}

async function checkJobStatus() {
  try {
    const response = await fetch("/api/analysis/jobs");
    if (!response.ok) return; // Fail silently

    const jobs = await response.json();

    jobs.forEach((job) => {
      const isDone = job.status === "completed" || job.status === "failed";

      if (isDone && !notifiedJobIds.has(job.job_id)) {
        // We have a new, finished job. Notify the user.
        const message = `Job '${job.script_id}' has ${job.status}.`;
        showToast(message, job.status);
        notifiedJobIds.add(job.job_id);
      } else if (!isDone) {
        // If a job is 'running', remove it from the set
        // in case it was re-run (this is optional)
        notifiedJobIds.delete(job.job_id);
      }
    });
  } catch (error) {
    console.error("Job poller failed:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const controlsPanel = document.getElementById("controls");

  const openSpotFormBtn = document.getElementById("open-form");
  const closeSpotFormBtn = document.getElementById("close-form");
  const spotPopup = document.getElementById("popup-form");
  const addSiteButton = document.querySelector(".add_site");
  const addSitePopup = document.getElementById("add-site-popup-form");
  const closeAddSiteButton = document.getElementById("close-add-site-form");

  const imageInput = document.getElementById("image-upload");
  const imageLabel = document.querySelector('label[for="image-upload"]');
  const kmlUploadInput = document.getElementById("kml-upload");
  const kmlFileNameDisplay = document.getElementById("kml-file-name");

  menuToggle.addEventListener("click", () =>
    controlsPanel.classList.toggle("open")
  );

  openSpotFormBtn.addEventListener("click", () => {
    map.locate({ watch: true, enableHighAccuracy: true });
    spotPopup.style.display = "flex";
  });

  closeSpotFormBtn.addEventListener("click", () => {
    spotPopup.style.display = "none";
  });

  addSiteButton.addEventListener("click", () => {
    addSitePopup.style.display = "flex";
  });

  closeAddSiteButton.addEventListener("click", () => {
    addSitePopup.style.display = "none";
    kmlFileNameDisplay.textContent = "No file chosen"; // Reset file name
  });

  imageInput.addEventListener("change", () => {
    imageLabel.classList.toggle("selected", imageInput.files.length > 0);
  });

  kmlUploadInput.addEventListener("change", () => {
    kmlFileNameDisplay.textContent =
      kmlUploadInput.files.length > 0
        ? kmlUploadInput.files[0].name
        : "No file chosen";
  });
  loadExistingSites();
  setInterval(checkJobStatus, 15000); // Check every 15 seconds
  checkJobStatus(); // Check once on load
});

const importMediaForm = document.getElementById("import-media-form");
const importMediaBtn = document.getElementById("import-media-btn");
const importMediaPopup = document.getElementById("import-media-popup");
const cancelImportBtn = document.getElementById("cancel-import-btn");
const spotSelectionContainer = document.getElementById(
  "spot-selection-container"
);
const destinationPathPreview = document.getElementById(
  "destination-path-preview"
);

async function handleOpenImportModal() {
  try {
    const response = await fetch("/api/get-spots");
    if (!response.ok) throw new Error("Failed to fetch spots.");
    const spots = await response.json();
    populateSpotSelector(spots);
    document.getElementById("import-media-popup").style.display = "flex";
    updatePathPreview();
  } catch (error) {
    console.error("Error opening import modal:", error);
    alert("Could not load spots for import. Please try again.");
  }
}

importMediaForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  const selectedSpots = Array.from(
    document.querySelectorAll(
      '#spot-selection-container input[type="checkbox"]:checked'
    )
  ).map((cb) => cb.value);
  if (selectedSpots.length === 0) {
    alert("Please select at least one spot.");
    return;
  }
  const files = document.getElementById("external-file-input").files;
  if (files.length === 0) {
    alert("Please select at least one file to import.");
    return;
  }
  const formData = new FormData();
  selectedSpots.forEach((spotName) => formData.append("spot_names", spotName));
  for (const file of files) {
    formData.append("files", file);
  }

  try {
    const response = await fetch("/api/import-external-media", {
      method: "POST",
      body: formData,
    });
    if (response.ok) {
      alert("Media imported successfully!");
      document.getElementById("import-media-popup").style.display = "none";
      importMediaForm.reset();
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to import media.");
    }
  } catch (error) {
    console.error("Error importing media:", error);
    alert(`An error occurred: ${error.message}`);
  }
});

function populateSpotSelector(spots) {
  spotSelectionContainer.innerHTML = "";
  if (!spots || spots.length === 0) {
    spotSelectionContainer.innerHTML =
      "<p>No spots found. Please create one first.</p>";
    return;
  }
  spots.forEach((spot) => {
    const spotId = `spot-checkbox-${spot.spotId}`;
    const label = document.createElement("label");
    label.htmlFor = spotId;
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = spotId;
    checkbox.name = "selected_spots";
    checkbox.value = spot.name;
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(` ${spot.name}`));
    spotSelectionContainer.appendChild(label);
  });
}

function updatePathPreview() {
  const selectedSpots = Array.from(
    spotSelectionContainer.querySelectorAll('input[type="checkbox"]:checked')
  ).map((cb) => cb.value);

  const spotNamePlaceholder =
    selectedSpots.length > 0 ? selectedSpots[0] : "{spot_name}";

  const slugifiedSpotName = spotNamePlaceholder
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^\w-]+/g, "");

  const today = new Date();
  const dateStr = `${String(today.getFullYear()).slice(-2)}${String(
    today.getMonth() + 1
  ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;

  const previewPath = `data/spots/${slugifiedSpotName}/external_data/${dateStr}`;

  destinationPathPreview.textContent = previewPath;
}

importMediaBtn.addEventListener("click", handleOpenImportModal);

cancelImportBtn.addEventListener("click", () => {
  importMediaPopup.style.display = "none";
});

spotSelectionContainer.addEventListener("change", updatePathPreview);

const addSiteForm = document.getElementById("add-site-form");
const addSiteStatus = document.getElementById("add-site-status");
const kmlFileNameDisplay = document.getElementById("kml-file-name");

addSiteForm.onsubmit = async (e) => {
  e.preventDefault();
  addSiteStatus.textContent =
    "Processing with Google Earth Engine, this may take a minute...";
  const formData = new FormData(addSiteForm);

  try {
    const response = await fetch("/api/add-site", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorResult = await response.json();
      throw new Error(errorResult.message || "An unknown error occurred.");
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

async function loadExistingSites() {
  try {
    const response = await fetch("/api/get-sites");
    if (!response.ok) {
      throw new Error("Failed to fetch existing sites.");
    }
    const sites = await response.json();
    const controlsContainer = document.getElementById(
      "stratification-controls"
    );
    controlsContainer.innerHTML = "";
    sites.forEach((site) => displaySiteControls(site));
  } catch (error) {
    console.error("Error loading existing sites:", error);
    alert(error.message);
  }
}

function displaySiteControls(siteData) {
  const controlsContainer = document.getElementById("stratification-controls");

  const siteContainer = document.createElement("div");
  siteContainer.className = "site-control-block";

  const title = document.createElement("div");
  title.className = "div-label";
  title.textContent = siteData.siteName;
  siteContainer.appendChild(title);

  const radioDiv = document.createElement("div");
  radioDiv.className = "control radios_div";

  const radioGroupName = `geojsonOption_${siteData.siteId}`;

  const noneLabel = document.createElement("label");
  noneLabel.innerHTML = `<input type="radio" name="${radioGroupName}" value="clear" checked />None`;
  radioDiv.appendChild(noneLabel);

  let lastImagePath = "";

  siteData.stratifications.forEach((strat) => {
    stratificationDataStore[strat.image_path] = {
      bounds: strat.bounds,
      name: siteData.siteName,
    };
    const newLayerLabel = document.createElement("label");
    newLayerLabel.innerHTML = `<input type="radio" name="${radioGroupName}" value="${strat.image_path}" />${strat.cluster_count} Clusters`;
    radioDiv.appendChild(newLayerLabel);
    lastImagePath = strat.image_path;
  });

  siteContainer.appendChild(radioDiv);
  controlsContainer.appendChild(siteContainer); // Append the new site block

  document
    .querySelectorAll(`input[name="${radioGroupName}"]`)
    .forEach((radio) => {
      radio.addEventListener("change", (e) => {
        document
          .querySelectorAll(
            `input[type="radio"]:not([name="${radioGroupName}"])`
          )
          .forEach((otherRadio) => {
            if (otherRadio.value === "clear") otherRadio.checked = true;
          });
        if (e.target.checked) loadStratification(e.target.value);
      });
    });

  const isNewlyAdded =
    document.activeElement &&
    document.activeElement.form &&
    document.activeElement.form.id === "add-site-form";
  if (isNewlyAdded && lastImagePath) {
    const newRadio = document.querySelector(`input[value="${lastImagePath}"]`);
    if (newRadio) {
      newRadio.checked = true;
      newRadio.dispatchEvent(new Event("change"));
    }
  }
}

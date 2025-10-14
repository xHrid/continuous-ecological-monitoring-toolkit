const map = L.map("map", { minZoom: 3, maxZoom: 18, zoomControl: false }).setView([20, 0], 3);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors', noWrap: false }).addTo(map);

let clusterLayer = null; let spotsLayer = null;
const stratificationDataStore = {};


function displaySiteControls(siteData) {
    const controlsContainer = document.getElementById("stratification-controls");
    
    const siteContainer = document.createElement('div');
    siteContainer.className = 'site-control-block';

    const title = document.createElement('div');
    title.className = 'div-label';
    title.textContent = siteData.siteName;
    siteContainer.appendChild(title);

    const radioDiv = document.createElement('div');
    radioDiv.className = 'control radios_div';
    
    const radioGroupName = `geojsonOption_${siteData.siteId}`;

    const noneLabel = document.createElement('label');
    noneLabel.innerHTML = `<input type="radio" name="${radioGroupName}" value="clear" checked />None`;
    radioDiv.appendChild(noneLabel);
    
    let lastImagePath = '';

    siteData.stratifications.forEach(strat => {
        stratificationDataStore[strat.image_path] = { bounds: strat.bounds, name: siteData.siteName };
        const newLayerLabel = document.createElement('label');
        newLayerLabel.innerHTML = `<input type="radio" name="${radioGroupName}" value="${strat.image_path}" />${strat.cluster_count} Clusters`;
        radioDiv.appendChild(newLayerLabel);
        lastImagePath = strat.image_path;
    });

    siteContainer.appendChild(radioDiv);
    controlsContainer.appendChild(siteContainer); // Append the new site block

    document.querySelectorAll(`input[name="${radioGroupName}"]`).forEach((radio) => {
        radio.addEventListener("change", (e) => {
            document.querySelectorAll(`input[type="radio"]:not([name="${radioGroupName}"])`).forEach(otherRadio => {
                if(otherRadio.value === 'clear') otherRadio.checked = true;
            });
            if (e.target.checked) loadStratification(e.target.value);
        });
    });

    const isNewlyAdded = document.activeElement && document.activeElement.form && document.activeElement.form.id === 'add-site-form';
    if (isNewlyAdded && lastImagePath) {
        const newRadio = document.querySelector(`input[value="${lastImagePath}"]`);
        if (newRadio) { newRadio.checked = true; newRadio.dispatchEvent(new Event('change')); }
    }
}

function loadStratification(imagePath) {
    if (clusterLayer) { map.removeLayer(clusterLayer); clusterLayer = null; }
    if (imagePath === "clear") return;
    const data = stratificationDataStore[imagePath];
    if (!data) { console.error("Could not find stratification data for path:", imagePath); return; }
    clusterLayer = L.imageOverlay(imagePath, data.bounds).addTo(map);
   map.fitBounds(data.bounds);
}
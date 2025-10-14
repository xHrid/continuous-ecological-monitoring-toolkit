document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.getElementById('menu-toggle');
    const controlsPanel = document.getElementById('controls');

    const openSpotFormBtn = document.getElementById('open-form');
    const closeSpotFormBtn = document.getElementById('close-form');
    const spotPopup = document.getElementById('popup-form');
    const addSiteButton = document.querySelector(".add_site");
    const addSitePopup = document.getElementById("add-site-popup-form");
    const closeAddSiteButton = document.getElementById("close-add-site-form");

    const imageInput = document.getElementById('image-upload');
    const imageLabel = document.querySelector('label[for="image-upload"]');
    const kmlUploadInput = document.getElementById("kml-upload");
    const kmlFileNameDisplay = document.getElementById("kml-file-name");


    menuToggle.addEventListener('click', () => controlsPanel.classList.toggle('open'));

    openSpotFormBtn.addEventListener('click', () => {
        map.locate({ watch: true, enableHighAccuracy: true });
        spotPopup.style.display = "flex";
    });

    closeSpotFormBtn.addEventListener('click', () => {
        spotPopup.style.display = "none";
    });

    addSiteButton.addEventListener('click', () => {
        addSitePopup.style.display = "flex";
    });

    closeAddSiteButton.addEventListener('click', () => {
        addSitePopup.style.display = "none";
        kmlFileNameDisplay.textContent = "No file chosen"; // Reset file name
    });

    imageInput.addEventListener("change", () => {
        imageLabel.classList.toggle("selected", imageInput.files.length > 0);
    });

    kmlUploadInput.addEventListener("change", () => {
        kmlFileNameDisplay.textContent = kmlUploadInput.files.length > 0 ?
            kmlUploadInput.files[0].name :
            "No file chosen";
    });
});


    const importMediaBtn = document.getElementById('import-media-btn');
    const importMediaPopup = document.getElementById('import-media-popup');
    const cancelImportBtn = document.getElementById('cancel-import-btn');
    const spotSelectionContainer = document.getElementById('spot-selection-container');
    const destinationPathPreview = document.getElementById('destination-path-preview');

    function populateSpotSelector(spots) {
        spotSelectionContainer.innerHTML = '';
        if (!spots || spots.length === 0) {
            spotSelectionContainer.innerHTML = '<p>No spots found. Please create one first.</p>';
            return;
        }
        spots.forEach(spot => {
            const spotId = `spot-checkbox-${spot.spotId}`;
            const label = document.createElement('label');
            label.htmlFor = spotId;
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = spotId;
            checkbox.name = 'selected_spots';
            checkbox.value = spot.name;
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(` ${spot.name}`));
            spotSelectionContainer.appendChild(label);
        });
    }

    function updatePathPreview() {
        const selectedSpots = Array.from(spotSelectionContainer.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        
        const spotNamePlaceholder = selectedSpots.length > 0 ? selectedSpots[0] : '{spot_name}';
        
        const slugifiedSpotName = spotNamePlaceholder.toLowerCase().replace(/\s+/g, '_').replace(/[^\w-]+/g, '');
        
        const today = new Date();
        const dateStr = `${String(today.getFullYear()).slice(-2)}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
        
        const previewPath = `data/spots/${slugifiedSpotName}/external_data/${dateStr}`;
        
        destinationPathPreview.textContent = previewPath;
    }

    importMediaBtn.addEventListener('click', () => {
        window.handleOpenImportModal();
    });

    cancelImportBtn.addEventListener('click', () => {
        importMediaPopup.style.display = 'none';
    });

    spotSelectionContainer.addEventListener('change', updatePathPreview);
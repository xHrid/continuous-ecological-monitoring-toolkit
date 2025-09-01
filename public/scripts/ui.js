// public/scripts/ui.js

// This file handles all general-purpose UI interactions, such as
// showing/hiding elements and handling simple click events.

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element Selection ---
    const menuToggle = document.getElementById('menu-toggle');
    const controlsPanel = document.getElementById('controls');

    // Pop-up form elements
    const openSpotFormBtn = document.getElementById('open-form');
    const closeSpotFormBtn = document.getElementById('close-form');
    const spotPopup = document.getElementById('popup-form');
    const addSiteButton = document.querySelector(".add_site");
    const addSitePopup = document.getElementById("add-site-popup-form");
    const closeAddSiteButton = document.getElementById("close-add-site-form");

    // File input elements
    const imageInput = document.getElementById('image-upload');
    const imageLabel = document.querySelector('label[for="image-upload"]');
    const kmlUploadInput = document.getElementById("kml-upload");
    const kmlFileNameDisplay = document.getElementById("kml-file-name");

    // --- Event Listeners for UI Interactions ---

    // Toggle the main sidebar
    menuToggle.addEventListener('click', () => controlsPanel.classList.toggle('open'));

    // Show "Add Spot" popup
    openSpotFormBtn.addEventListener('click', () => {
        map.locate({ watch: true, enableHighAccuracy: true });
        spotPopup.style.display = "flex";
    });

    // Hide "Add Spot" popup
    closeSpotFormBtn.addEventListener('click', () => {
        spotPopup.style.display = "none";
    });

    // Show "Add Site" popup
    addSiteButton.addEventListener('click', () => {
        addSitePopup.style.display = "flex";
    });

    // Hide "Add Site" popup
    closeAddSiteButton.addEventListener('click', () => {
        addSitePopup.style.display = "none";
        kmlFileNameDisplay.textContent = "No file chosen"; // Reset file name
    });

    // Update UI when an image is selected for a spot
    imageInput.addEventListener("change", () => {
        imageLabel.classList.toggle("selected", imageInput.files.length > 0);
    });

    // Update UI text when a KML file is selected
    kmlUploadInput.addEventListener("change", () => {
        kmlFileNameDisplay.textContent = kmlUploadInput.files.length > 0 ?
            kmlUploadInput.files[0].name :
            "No file chosen";
    });
});

const map = L.map("map", {
  minZoom: 3,
  maxZoom: 18,
  zoomControl: false,
}).setView([20, 0], 3);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  noWrap: false,
}).addTo(map);

let clusterLayer = null;
let spotsLayer = null;
const stratificationDataStore = {};

function loadStratification(imagePath) {
  if (clusterLayer) {
    map.removeLayer(clusterLayer);
    clusterLayer = null;
  }
  if (imagePath === "clear") return;
  const data = stratificationDataStore[imagePath];
  if (!data) {
    console.error("Could not find stratification data for path:", imagePath);
    return;
  }
  clusterLayer = L.imageOverlay(imagePath, data.bounds).addTo(map);
  map.fitBounds(data.bounds);
}

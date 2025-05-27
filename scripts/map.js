/* setting up the map */
const map = L.map("map", {
  minZoom: 15,
  maxZoom: 17,
  maxBoundsViscosity: 1.0,
  zoomControl: false
}).setView([28.522722996428367, 77.16883125123917], 2);

map.on("zoomend", () => {
  const currentZoom = map.getZoom();
  if (currentZoom < 15) map.setZoom(15);
  else if (currentZoom > 17) map.setZoom(17);
});

fetch("./geojson/bounding_box.geojson")
  .then((res) => res.json())
  .then((strataData) => {
    const strataLayer = L.geoJSON(strataData, {
      style: { color: "#3388ff", weight: 0.5, fillOpacity: 0 },
    }).addTo(map);

    const bounds = strataLayer.getBounds();
    map.fitBounds(bounds);
    map.setMaxBounds(bounds);
    const initialZoom = Math.min(17, Math.max(15, map.getZoom()));
    map.setZoom(initialZoom);
  });

L.tileLayer("./tiles/{z}/{x}/{y}.png", {
  maxZoom: 17,
  minZoom: 15,
  noWrap: true,
  errorTileUrl: "./leaflet/images/white_box.png",
}).addTo(map);

let clusterLayer = null;
let spotsLayer = null;


function loadStratification(imagePath) {
  // Clear existing overlay if "clear" is selected
  if (imagePath === "clear") {
    if (clusterLayer) {
      map.removeLayer(clusterLayer);
      clusterLayer = null;
    }
    return;
  }

  // Define bounds for known images
  const boundsMap = {
    "cp2img.png": [
      [28.522530327, 77.167391345],
      [28.542287423, 77.194349070],
    ],
    "cp3img.png": [
      [28.522235660, 77.167398810],
      [28.542703774, 77.195326689],
    ],
    "cp4img.png": [
      [28.522235660, 77.167977352],
      [28.542703774, 77.194748147],
    ],
  };

  const bounds = boundsMap[imagePath];
  if (!bounds) {
    alert("Unknown stratification image.");
    return;
  }

  // Remove previous image overlay
  if (clusterLayer) {
    map.removeLayer(clusterLayer);
    clusterLayer = null;
  }

  const fullImagePath = "./images/" + imagePath;

  // Add image overlay
  clusterLayer = L.imageOverlay(fullImagePath, bounds).addTo(map);
}


document.querySelectorAll('input[name="geojsonOption"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    if (radio.checked) {
      loadStratification(radio.value);
    }
  });
});

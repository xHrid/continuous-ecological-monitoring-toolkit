/* setting up the map */
const map = L.map("map", {
  minZoom: 15,
  maxZoom: 17,
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
    map.fitBounds(bounds, { padding: [20, 20] });
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

/*A function to load the stratification */
function loadStratification(filename) {
  if (filename == "clear") {
    map.removeLayer(clusterLayer);
    return;
  }
  colors = ["red", "blue", "green", "orange", "purple", "brown"];

  if (filename == "cp4.geojson")
    colors = ["green", "red", "blue", "orange", "purple", "brown"];

  filename = "./geojson/" + filename;
  fetch(filename)
    .then((res) => res.json())
    .then((data) => {
      if (clusterLayer) map.removeLayer(clusterLayer);
      clusterLayer = L.geoJSON(data, {
        pointToLayer: (feat, latlng) => {
          const c = feat.properties.cluster;
          return L.circleMarker(latlng, {
            radius: 5,
            fillColor: colors[c % colors.length],
            fillOpacity: 0.8,
            stroke: false,
          });
        },
      }).addTo(map);
    })
    .catch((err) => {
      console.error(`Error loading ${filename}:`, err);
      alert("Failed to load cluster data.");
    });
}

document.querySelectorAll('input[name="geojsonOption"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    if (radio.checked) {
      loadStratification(radio.value);
    }
  });
});

const latlon_label = document.querySelector("#latlon label");

map.locate({ watch: true, enableHighAccuracy: true });

let currentMarker = null,
  currentCircle = null,
  firstFix = true;

map.on("locationfound", (e) => {
  const lat = e.latitude || e.latlng.lat;
  const lon = e.longitude || e.latlng.lng;

  latlon_label.textContent = `Latitude: ${lat}, Longitude: ${lon}`;
  const r = e.accuracy / 2;
  if (currentMarker) map.removeLayer(currentMarker);
  if (currentCircle) map.removeLayer(currentCircle);

  currentMarker = L.marker(e.latlng).addTo(map).bindPopup("You are here");
  currentCircle = L.circle(e.latlng, r).addTo(map);

  if (firstFix) {
    map.setView(e.latlng, map.getZoom());
    firstFix = false;
  }
});

document.getElementById("open-form").onclick = () => {
  document.getElementById("popup-form").style.display = "flex";
};

document.getElementById("close-form").onclick = () => {
  document.getElementById("popup-form").style.display = "none";
};

document.getElementById("spot-form").onsubmit = async function (e) {
  e.preventDefault();

  const form = e.target;
  const name = form.name.value.trim();
  const birds = form.birds.value.trim();
  const desc = form.description.value.trim();

  if (!name && !birds && !desc) {
    document.getElementById("status").textContent =
      "Please fill at least one field.";
    return;
  }

  const formData = new FormData(form);

  // Add lat/lon and timestamp in later steps

  document.getElementById("status").textContent = "Form is ready to submit!";
};

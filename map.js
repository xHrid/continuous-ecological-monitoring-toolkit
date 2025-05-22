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
let spotsLayer = null;

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

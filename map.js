/* setting up the map */
const map = L.map("map", {
  minZoom: 14,
  maxZoom: 17,
  maxBoundsViscosity: 1.0,
}).setView([28.522722996428367, 77.16883125123917], 2);

map.on("zoomend", () => {
  const currentZoom = map.getZoom();
  if (currentZoom < 14) map.setZoom(14);
  else if (currentZoom > 17) map.setZoom(17);
});

fetch("./geojson/bounding_box.geojson")
  .then((res) => res.json())
  .then((strataData) => {
    const strataLayer = L.geoJSON(strataData, {
      style: { color: "#3388ff", weight: 2, fillOpacity: 0 },
    }).addTo(map);

    const bounds = strataLayer.getBounds();
    map.fitBounds(bounds);
    map.setMaxBounds(bounds);
    const initialZoom = Math.min(17, Math.max(14, map.getZoom()));
    map.setZoom(initialZoom);
  });

L.tileLayer("./tiles/{z}/{x}/{y}.png", {
  maxZoom: 17,
  minZoom: 14,
  noWrap: true,
  errorTileUrl: "./leaflet/images/white_box.png",
}).addTo(map);

let clusterLayer = null;
let spotsLayer = null;

/*A function to load the stratification */
function loadStratification(filename) {
  if (filename === "clear") {
    if (clusterLayer) {
      map.removeLayer(clusterLayer);
      clusterLayer = null;
    }
    return;
  }

  let colors = ["red", "blue", "green", "orange", "purple", "brown"];

  if (filename === "cp4.geojson") {
    colors = ["green", "red", "blue", "orange", "purple", "brown"];
  }

  filename = "./geojson/" + filename;

  fetch(filename)
    .then((res) => res.json())
    .then((data) => {
      if (clusterLayer) map.removeLayer(clusterLayer);

      const firstGeomType = data.features?.[0]?.geometry?.type;

      if (firstGeomType === "Point") {
        // Handle point-based stratification
        clusterLayer = L.geoJSON(data, {
          pointToLayer: (feat, latlng) => {
            const c = feat.properties.cluster || 0;
            return L.circleMarker(latlng, {
              radius: 5,
              fillColor: colors[c % colors.length],
              fillOpacity: 0.8,
              stroke: false,
            });
          },
        }).addTo(map);
      } else {
        // Handle polygon-based stratification
        clusterLayer = L.geoJSON(data, {
          style: (feat) => {
            const c = feat.properties.cluster || 0;
            return {
              color: colors[c % colors.length],
              weight: 2,
              fillOpacity: 0.2,
            };
          },
        }).addTo(map);
      }
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

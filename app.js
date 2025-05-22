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

let mediaRecorder;
let audioChunks = [];
let audioBlob = null;

const startBtn = document.getElementById('start-recording');
const stopBtn = document.getElementById('stop-recording');
const statusText = document.getElementById('recording-status');

startBtn.onclick = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Audio recording not supported on this browser.");
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = e => {
    audioChunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    statusText.textContent = "Recording complete.";
  };

  mediaRecorder.start();
  statusText.textContent = "Recording...";
  startBtn.disabled = true;
  stopBtn.disabled = false;
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
  startBtn.disabled = false;
  stopBtn.disabled = true;
};

document.getElementById('spot-form').onsubmit = async function(e) {
  e.preventDefault();

  const form = e.target;
  const name = form.name.value.trim();
  const birds = form.birds.value.trim();
  const desc = form.description.value.trim();
  const image = form.image.files[0];

  if (!name && !birds && !desc && !image && !audioBlob) {
    document.getElementById('status').textContent = "Please fill at least one field.";
    return;
  }

  const formData = new FormData(form);

  if (audioBlob) {
    formData.append('audio', audioBlob, 'recording.webm');
  }

  // In next step, add location and timestamp here

  // Send data
  const res = await fetch('/api/add-spot', {
    method: 'POST',
    body: formData,
  });

  if (res.ok) {
    alert("Spot submitted!");
    form.reset();
    document.getElementById('recording-status').textContent = '';
    audioBlob = null;
  } else {
    alert("Error submitting form.");
  }
};

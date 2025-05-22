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

const latlon_label = document.querySelector("#latlon label");

map.locate({ watch: true, enableHighAccuracy: true });

let currentMarker = null,
  currentCircle = null,
  firstFix = true;

let currLat = null;
let currLng = null;

map.on("locationfound", (e) => {
  const lat = e.latitude || e.latlng.lat;
  const lon = e.longitude || e.latlng.lng;
  currLat = lat;
  currLng = lon;

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
  map.locate({ watch: true, enableHighAccuracy: true });
  document.getElementById("popup-form").style.display = "flex";
};

document.getElementById("close-form").onclick = () => {
  document.getElementById("popup-form").style.display = "none";
};

// let constrainsObj = {
//   audio: true,
//   video: false,
// }
// const startBtn = document.getElementById('btnStart');
// const stopBtn = document.getElementById('btnStop');
// const audioPlayback = document.getElementById('audioPlayback');

// let mediaRecorder;
// let audioChunks = [];
// let audioBlob = null;

// startBtn.addEventListener('click', async () => {
//   try {
//     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//     mediaRecorder = new MediaRecorder(stream);
//     audioChunks = [];

//     mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

//     mediaRecorder.onstop = () => {
//       audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
//       const audioURL = URL.createObjectURL(audioBlob);
//       audioPlayback.src = audioURL;

//       mediaRecorder.stream.getTracks().forEach(track => track.stop());

//     };

//     mediaRecorder.start();
//     console.log("Recording started");

//     startBtn.disabled = true;
//     stopBtn.disabled = false;
//   } catch (err) {
//     console.error("Error accessing microphone:", err);
//   }
// });

// stopBtn.addEventListener('click', () => {
//   if (mediaRecorder && mediaRecorder.state !== 'inactive') {
//     mediaRecorder.stop();
//     console.log("Recording stopped");

//     startBtn.disabled = false;
//     stopBtn.disabled = true;
//   }
// });

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

  try {
    const spotData = {
      name: name || null,
      createdAt: firebaseServices.serverTimestamp(),
      latitude: currLat,
      longitude: currLng,
      birds: birds ? birds.split(",").map((b) => b.trim()) : [],
      description: desc || null,
    };

    await firebaseServices.addDoc(
      firebaseServices.collection(firebaseServices.db, "spots"),
      spotData
    );

    alert("Spot submitted successfully!");
    form.reset();
    document.getElementById("popup-form").style.display = "none";
  } catch (error) {
    console.error("Error adding document: ", error);
    document.getElementById("status").textContent = "Error submitting spot.";
  }
};

async function displaySpots() {
  try {
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
    }

    const querySnapshot = await firebaseServices.getDocs(
      firebaseServices.collection(firebaseServices.db, "spots")
    );

    const spots = [];
    querySnapshot.forEach((doc) => {
      spots.push({ id: doc.id, ...doc.data() });
    });

    spotsLayer = L.layerGroup().addTo(map);

    spots.forEach((spot) => {
      const circle = L.circleMarker([spot.latitude, spot.longitude], {
        radius: 8, 
        fillColor: "#3388ff", 
        color: "#000", 
        weight: 1, 
        opacity: 1, 
        fillOpacity: 0.8, 
      }).addTo(spotsLayer);

      circle.spotData = spot;

      circle.on("click", (e) => {
        showSpotDetails(spot);
      });

      circle.on("mouseover", () => {
        circle.setStyle({
          fillOpacity: 1,
          weight: 2,
        });
      });

      circle.on("mouseout", () => {
        circle.setStyle({
          fillOpacity: 0.8,
          weight: 1,
        });
      });
    });
  } catch (error) {
    console.error("Error fetching spots: ", error);
    alert("Failed to load spots.");
  }
}

function showSpotDetails(spot) {
  const menu = document.getElementById("spot-details-menu");
  const content = document.getElementById("spot-details-content");

  // Format the birds list
  const birdsList =
    spot.birds && spot.birds.length > 0
      ? `<ul>${spot.birds.map((bird) => `<li>${bird}</li>`).join("")}</ul>`
      : "<p>No birds recorded</p>";

  content.innerHTML = `
    <h2>${spot.name || "Unnamed Spot"}</h2>
    <p><strong>Description:</strong> ${spot.description || "No description"}</p>
    <p><strong>Birds observed:</strong></p>
    ${birdsList}
    <p><strong>Coordinates:</strong> ${spot.latitude.toFixed(
      6
    )}, ${spot.longitude.toFixed(6)}</p>
  `;

  menu.classList.add("open");
}

// Add event listener to close the menu
document.getElementById("close-spot-details").addEventListener("click", () => {
  document.getElementById("spot-details-menu").classList.remove("open");
});

document.getElementById('display-spots').addEventListener('change', function(e) {
  if (this.checked) {
    displaySpots(); // Show spots when checked
  } else {
    // Hide spots when unchecked
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
      spotsLayer = null;
    }
  }
});
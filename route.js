let routePoints = [];
let routePolyline = null;
let isTracking = false;

function startTracking() {
  isTracking = true;
  routePoints = [];
}

function stopTracking() {
  isTracking = false;
  // map.stopLocate();
}

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

  if (!isTracking) return;

  const newPoint = e.latlng;
  routePoints.push(newPoint);

  // Update or create the polyline
  if (!routePolyline) {
    routePolyline = L.polyline(routePoints, {
      color: "#3498db",
      weight: 6,
      opacity: 0.8,
    }).addTo(map);
  } else {
    routePolyline.setLatLngs(routePoints);
  }

  console.log(routePoints);
  

  // Optional: Pan map to follow user
  map.setView(newPoint);
});



document.getElementById('start-tracking').addEventListener('click', () => {
  startTracking();
});

document.getElementById('stop-tracking').addEventListener('click', () => {
  stopTracking();
});
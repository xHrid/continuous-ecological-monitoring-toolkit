let routePoints = [];
let routePolyline = null;
let isTracking = false;

function startTracking() {
  isTracking = true;
  routePoints = [];
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

  currentMarker = L.marker(e.latlng, { interactive: false }).addTo(map);
// no .bindPopup("You are here") if you don’t want interaction

currentCircle = L.circle(e.latlng, {
  radius: r,
  interactive: false, // disable clicking, hovering, etc.
  color: "#136aec",
  fillColor: "#136aec",
  fillOpacity: 0.2
}).addTo(map);


  if (firstFix) {
    map.setView(e.latlng, map.getZoom());
    firstFix = false;
  }

  if (!isTracking) return;


  const newPoint = {
    lat: e.latlng.lat,
    lng: e.latlng.lng
  };

  if (routePoints.length > 0) {
    const lastPoint = routePoints[routePoints.length - 1];
    
    const lastLatLng = L.latLng(lastPoint.lat, lastPoint.lng);
    const newLatLng = L.latLng(newPoint.lat, newPoint.lng);
    
    const distance = lastLatLng.distanceTo(newLatLng);

    if (distance <= 5) return;
  }

  routePoints.push(newPoint);
  console.log(routePoints);
  

  if (!routePolyline) {
  routePolyline = L.polyline(
  routePoints.map(p => [p.lat, p.lng]),
  { 
    color: "#3498db", 
    weight: 6, 
    opacity: 0.8,
    dashArray: '5,10' // Makes it dashed
  }
).addTo(map);
} else {
  routePolyline.setLatLngs(routePoints.map(p => [p.lat, p.lng]));
}

});


let _isTracking = false;

document.getElementById('toggle-tracking').addEventListener('click', () => {
  const button = document.getElementById('toggle-tracking');

  if (!_isTracking) {
    startTracking();
    button.textContent = 'Save';
    button.style.backgroundColor = 'red'; // Change color when tracking
  } else {
    stopTracking();
    button.textContent = 'Record';
    button.style.backgroundColor = ''; // Reset to default or another color
  }

  _isTracking = !_isTracking;
  button.classList.toggle('tracking-active');

});


const saveRouteDialog = document.getElementById('save-route-dialog');
const routeForm = document.getElementById('route-form');
const closeButton = document.querySelector('#save-route-dialog .close');

function stopTracking() {
  isTracking = false;
  
  if (routePoints.length > 0) {
    saveRouteDialog.style.display = 'block';
  }
}

closeButton.onclick = function() {
  saveRouteDialog.style.display = 'none';
}

window.onclick = function(event) {
  if (event.target == saveRouteDialog) {
    saveRouteDialog.style.display = 'none';
  }
}

routeForm.onsubmit = async function (e) {
  e.preventDefault();

  const routeName = document.getElementById("route-name").value.trim();

  try {
    const { error } = await supabaseClient.from("routes").insert([
      {
        name: routeName || null,
        created_at: new Date().toISOString(), // or let DB handle it with default
        points: routePoints, // should be an array of { lat, lng }
        point_count: routePoints.length,
      },
    ]);

    if (error) throw error;

    alert("Route saved successfully!");
    saveRouteDialog.style.display = "none";
  } catch (error) {
    console.error("Error saving route:", error);
    alert("Failed to save route. Please try again.");
  }
};


document.querySelector('#route-form .cancel-btn').onclick = function() {
  saveRouteDialog.style.display = 'none';
};

function calculateRouteDistance(points) {
  let distance = 0;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i-1];
    const curr = points[i];
    distance += L.latLng(prev.lat, prev.lng).distanceTo(
      L.latLng(curr.lat, curr.lng)
  )}
  return distance;
}



// Add this near your other variables
let allRoutes = []; // Stores all route data
let routeLayers = []; // Stores Leaflet polyline layers

// Add this event listener (put it with your other event listeners)
document.getElementById('show-routes-toggle').addEventListener('change', async function(e) {
  if (e.target.checked) {
    await fetchAndDisplayRoutes();
  } else {
    hideAllRoutes();
  }
});

async function fetchAndDisplayRoutes() {
  try {
    hideAllRoutes(); // Clear existing

    const { data: routes, error } = await supabaseClient
      .from("routes")
      .select("*");

    if (error) throw error;

    allRoutes = routes;

    routes.forEach((routeData) => {
      const latLngs = routeData.points.map((pt) => [pt.lat, pt.lng]);

      const polyline = L.polyline(latLngs, {
        color: "#ff0000",
        weight: 4,
        opacity: 0.8,
      }).addTo(map);

      const dateStr = routeData.created_at
        ? new Date(routeData.created_at).toLocaleString()
        : "Unknown";

      polyline.bindPopup(`
        <strong>${routeData.name || "Unnamed Route"}</strong><br>
        Points: ${routeData.point_count}<br>
        Date: ${dateStr}
      `);

      routeLayers.push(polyline);
    });
  } catch (error) {
    console.error("Error fetching routes:", error);
    alert("Failed to load routes. Please try again.");
  }
}

function hideAllRoutes() {
  // Remove all route polylines from map
  routeLayers.forEach(layer => map.removeLayer(layer));
  routeLayers = [];
  allRoutes = [];
}
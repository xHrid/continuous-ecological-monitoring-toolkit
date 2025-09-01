// public/scripts/routes.js

let routePoints = [];
let routePolyline = null;
let isTracking = false;

function startTracking() {
  isTracking = true;
  routePoints = [];
  // Clear any old route line from the map when starting a new one
  if (routePolyline) {
    map.removeLayer(routePolyline);
    routePolyline = null;
  }
}

const latlon_label = document.querySelector("#latlon label");

map.locate({ watch: true, enableHighAccuracy: true });

let currentMarker = null,
  currentCircle = null,
  firstFix = true;

// These are now the primary source for the current location
let currLat = null;
let currLng = null;

map.on("locationfound", (e) => {
  const lat = e.latitude || e.latlng.lat;
  const lon = e.longitude || e.latlng.lng;
  currLat = lat;
  currLng = lon;

  latlon_label.textContent = `Latitude: ${lat.toFixed(6)}, Longitude: ${lon.toFixed(6)}`;
  const r = e.accuracy / 2;
  if (currentMarker) map.removeLayer(currentMarker);
  if (currentCircle) map.removeLayer(currentCircle);

  currentMarker = L.marker(e.latlng, { interactive: false }).addTo(map);
  currentCircle = L.circle(e.latlng, {
    radius: r,
    interactive: false,
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

    // Only add a point if it's more than 5 meters away from the last one
    if (distance <= 5) return;
  }

  routePoints.push(newPoint);
  
  if (!routePolyline) {
    routePolyline = L.polyline(
      routePoints.map(p => [p.lat, p.lng]),
      { 
        color: "#3498db", 
        weight: 6, 
        opacity: 0.8,
        dashArray: '5,10'
      }
    ).addTo(map);
  } else {
    routePolyline.addLatLng([newPoint.lat, newPoint.lng]);
  }
});


let _isTracking = false;

document.getElementById('toggle-tracking').addEventListener('click', () => {
  const button = document.getElementById('toggle-tracking');

  if (!_isTracking) {
    startTracking();
    button.textContent = 'Save';
    button.style.backgroundColor = 'red';
  } else {
    stopTracking();
    button.textContent = 'Record';
    button.style.backgroundColor = '';
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
  
  const routeData = {
      name: routeName || null,
      createdAt: new Date().toISOString(),
      points: routePoints,
      pointCount: routePoints.length,
  };

  try {
    const response = await fetch('/api/save-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(routeData),
    });

    if (!response.ok) {
        const errorInfo = await response.json();
        throw new Error(errorInfo.message || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    alert(result.message);

    saveRouteDialog.style.display = "none";
    routeForm.reset();
    
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }
    routePoints = [];

    if (document.getElementById('show-routes-toggle').checked) {
        fetchAndDisplayRoutes();
    }

  } catch (error) {
    console.error("Error saving route:", error);
    alert(`Failed to save route: ${error.message}`);
  }
};


document.querySelector('#route-form .cancel-btn').onclick = function() {
  saveRouteDialog.style.display = 'none';
  routeForm.reset();
};

let allRoutes = [];
let routeLayers = [];

document.getElementById('show-routes-toggle').addEventListener('change', async function(e) {
  if (e.target.checked) {
    await fetchAndDisplayRoutes();
  } else {
    hideAllRoutes();
  }
});

async function fetchAndDisplayRoutes() {
  try {
    hideAllRoutes();

    const response = await fetch('/api/get-routes');
    if (!response.ok) {
        throw new Error('Failed to fetch routes from server.');
    }
    const routes = await response.json();
    allRoutes = routes;

    routes.forEach((routeData) => {
      const latLngs = routeData.points.map((pt) => [pt.lat, pt.lng]);

      const polyline = L.polyline(latLngs, {
        color: "#ff0000",
        weight: 4,
        opacity: 0.8,
      }).addTo(map);

      const dateStr = routeData.createdAt
        ? new Date(routeData.createdAt).toLocaleString()
        : "Unknown";

      polyline.bindPopup(`
        <strong>${routeData.name || "Unnamed Route"}</strong><br>
        Points: ${routeData.pointCount}<br>
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
  routeLayers.forEach(layer => map.removeLayer(layer));
  routeLayers = [];
  allRoutes = [];
}

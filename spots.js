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
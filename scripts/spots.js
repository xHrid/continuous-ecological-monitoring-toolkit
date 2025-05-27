document.getElementById("spot-form").onsubmit = async function (e) {
  e.preventDefault();

  const form = e.target;
  const name = form.name.value.trim();
  const birds = form.birds.value.trim();
  const desc = form.description.value.trim();

  const imageFile = form.image.files[0];
  const audioBlob = recordedAudioBlob; // your recorded audio blob variable
  let lastViewedSpot = null

  if (!name && !birds && !desc) {
    document.getElementById("status").textContent = "Please fill at least one field.";
    return;
  }

  try {
    document.getElementById("status").textContent = "Uploading files...";

    const [imageUrl, audioUrl] = await Promise.all([
      uploadFile(imageFile, "images"),
      uploadFile(audioBlob, "audio")
    ]);

    const spotData = {
      name: name || null,
      created_at: new Date().toISOString(),
      latitude: currLat,
      longitude: currLng,
      birds: birds || null,
      description: desc || null,
      image_url: imageUrl,
      audio_url: audioUrl
    };

    const { error } = await supabaseClient.from("spots").insert([spotData]);
    if (error) throw error;

    alert("Spot submitted successfully!");
    form.reset();
    document.getElementById("popup-form").style.display = "none";
    document.getElementById("status").textContent = "";

  } catch (error) {
    console.error("Error adding spot:", error);
    document.getElementById("status").textContent = "Error submitting spot.";
  }
};


let allSpots = []; // Global list to hold all entries

async function displaySpots() {
  try {
    // Remove old layer if it exists
    if (spotsLayer) {
      map.removeLayer(spotsLayer);
    }

    const { data: spots, error } = await supabaseClient
      .from("spots")
      .select("*");

    if (error) {
      throw error;
    }

    allSpots = spots; // Save for later use (grouping, timeline)

    // Group by unique spot (based on name + lat + lng)
    const uniqueSpots = {};
    spots.forEach(spot => {
      const key = `${spot.name || "Unnamed"}_${spot.latitude}_${spot.longitude}`;
      if (!uniqueSpots[key]) {
        uniqueSpots[key] = spot; // Just pick the first occurrence
      }
    });

    // Add markers for unique spots
    spotsLayer = L.layerGroup().addTo(map);
    const isMobile = window.innerWidth <= 768;
    let r = 10;
    if (isMobile) {
      r = 16;
    }

    Object.values(uniqueSpots).forEach(spot => {
      const circle = L.circleMarker([spot.latitude, spot.longitude], {
        radius: r,
        fillColor: "#3388ff",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8,
      }).addTo(spotsLayer);

      circle.on("click", () => {
        showSpotDetails(spot); // Will use `allSpots` to show full timeline
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
  lastViewedSpot = spot;

  const menu = document.getElementById("spot-details-menu");
  const content = document.getElementById("spot-details-content");

  // Set the spot name and location in the header
  document.getElementById("spot-name").textContent = spot.name || "Unnamed Spot";
  document.getElementById("spot-coordinates").textContent = `${spot.latitude.toFixed(6)}, ${spot.longitude.toFixed(6)}`;

  // Filter all entries for this location
  const matchingSpots = allSpots.filter(s =>
    s.name === spot.name &&
    s.latitude === spot.latitude &&
    s.longitude === spot.longitude
  );

  // Group by date
  const grouped = {};
  matchingSpots.forEach(s => {
    const date = new Date(s.created_at).toLocaleDateString();
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(s);
  });

  // Build timeline
  const timelineHtml = Object.entries(grouped)
    .sort((a, b) => new Date(b[0]) - new Date(a[0])) // newest date first
    .map(([date, entries]) => {
      const items = entries.map(entry => {
        const birds = entry.birds
          ? `<ul>${entry.birds.split(',').map(b => `<li>${b.trim()}</li>`).join('')}</ul>`
          : "<p>No birds recorded</p>";

        const image = entry.image_url
          ? `<img src="${entry.image_url}" style="max-width: 100%; margin-top: 5px;">`
          : "<p>No image</p>";

        const audio = entry.audio_url
          ? `<audio controls src="${entry.audio_url}" style="width: 100%; margin-top: 5px;"></audio>`
          : "<p>No audio</p>";

        return `
          <div class="spot-entry" style="border: 1px solid #ccc; padding: 8px; margin-top: 10px; border-radius: 8px;">
            <p><strong>Description:</strong> ${entry.description || "No description"}</p>
            <p><strong>Birds:</strong></p>
            ${birds}
            ${image}
            ${audio}
          </div>
        `;
      }).join("");

      return `
        <div class="spot-date-group" style="margin-top: 20px;">
          <h3 style="margin-bottom: 5px;">${date}</h3>
          ${items}
        </div>
      `;
    }).join("");

  // Replace content
  content.innerHTML = `
    <h2 id="spot-name">${spot.name || "Unnamed Spot"}</h2>
    <p><span id="spot-coordinates">(${spot.latitude.toFixed(6)}, ${spot.longitude.toFixed(6)})</span></p>
    ${timelineHtml}
    <button id="add-more-button" style="margin-top: 20px;">Add More</button>
  `;

  // Re-attach Add More listener
  document.getElementById("add-more-button").addEventListener("click", () => {
    const form = document.getElementById("spot-form");
    form.name.value = spot.name;
    form.name.readOnly = true;

    currLat = spot.latitude;
    currLng = spot.longitude;

    document.getElementById("popup-form").style.display = "flex";
  });

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

// document.getElementById("add-more-button").addEventListener("click", () => {
//   const form = document.getElementById("spot-form");
  
//   // Set values
//   form.name.value = lastViewedSpot.name;
//   form.name.readOnly = true;

//   // Store lat/lng in hidden fields (or just vars)
//   currLat = lastViewedSpot.latitude;
//   currLng = lastViewedSpot.longitude;

//   // Show form
//   document.getElementById("popup-form").style.display = "block";
// });

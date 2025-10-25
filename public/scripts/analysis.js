const analysisBtn = document.getElementById("analysis-btn");
const jobsBtn = document.getElementById("jobs-btn");
const analysisPopup = document.getElementById("analysis-popup");
const jobsPopup = document.getElementById("jobs-popup");
const cancelAnalysisBtn = document.getElementById("cancel-analysis-btn");
const closeJobsBtn = document.getElementById("close-jobs-btn");
const refreshJobsBtn = document.getElementById("refresh-jobs-btn");
const analysisForm = document.getElementById("analysis-form");
const scriptSelect = document.getElementById("analysis-script-select");
const scriptDescription = document.getElementById("analysis-description");
const fileSelectionContainer = document.getElementById(
  "analysis-file-selection"
);
const jobsListContainer = document.getElementById("jobs-list");

let availableScripts = [];

analysisBtn.addEventListener("click", openAnalysisModal);
jobsBtn.addEventListener("click", openJobsModal);
cancelAnalysisBtn.addEventListener(
  "click",
  () => (analysisPopup.style.display = "none")
);
closeJobsBtn.addEventListener(
  "click",
  () => (jobsPopup.style.display = "none")
);
refreshJobsBtn.addEventListener("click", populateJobsList);

const dynamicParamsContainer = document.getElementById(
  "dynamic-script-parameters"
);

scriptSelect.addEventListener("change", () => {
  // Clear old parameters
  dynamicParamsContainer.innerHTML = "";

  const selectedScript = availableScripts.find(
    (s) => s.id === scriptSelect.value
  );

  if (selectedScript) {
    scriptDescription.textContent = selectedScript.description;

    // --- THIS IS THE NEW LOGIC ---
    // Check if the manifest has parameters and build them
    if (selectedScript.parameters && selectedScript.parameters.length > 0) {
      selectedScript.parameters.forEach((param) => {
        const paramWrapper = document.createElement("div");
        paramWrapper.className = "form-group"; // For styling

        const label = document.createElement("label");
        label.htmlFor = `param-${param.name}`;
        label.textContent = param.label;

        const input = document.createElement("input");
        input.type = param.type || "text"; // e.g., 'number'
        if (input.type === "number") {
          input.step = "any"; // Allows any decimal value
        }
        input.id = `param-${param.name}`;
        input.name = param.name;
        input.placeholder = param.placeholder || "";
        input.value = param.default || "";
        input.required = param.required || false;

        paramWrapper.appendChild(label);
        paramWrapper.appendChild(input);
        dynamicParamsContainer.appendChild(paramWrapper);
      });
    }
  } else {
    scriptDescription.textContent = "";
  }
});

analysisForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const selectedFiles = Array.from(
    fileSelectionContainer.querySelectorAll("input:checked")
  ).map((input) => input.value);

  if (!scriptSelect.value) {
    alert("Please select an analysis script.");
    return;
  }
  if (selectedFiles.length === 0) {
    alert("Please select at least one input file.");
    return;
  }
  // --- THIS IS THE NEW LOGIC ---
  // Scrape parameters from the dynamic form
  const parameters = {};
  const paramInputs = dynamicParamsContainer.querySelectorAll("input");
  paramInputs.forEach((input) => {
    parameters[input.name] = input.value;
  });
  const jobRequest = {
    script_id: scriptSelect.value,
    input_files: selectedFiles,
    parameters: parameters,
  };

  try {
    const response = await fetch("/api/analysis/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jobRequest),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to start job.");
    }

    const result = await response.json();
    alert(`Job '${result.job_id}' started successfully!`);
    analysisPopup.style.display = "none";
    analysisForm.reset();
  } catch (error) {
    console.error("Error starting analysis job:", error);
    alert(`Error: ${error.message}`);
  }
});

async function openAnalysisModal() {
  try {
    const scriptsResponse = await fetch("/api/analysis/scripts");
    if (!scriptsResponse.ok) throw new Error("Could not fetch scripts.");
    availableScripts = await scriptsResponse.json();

    scriptSelect.innerHTML = '<option value="">Select a script...</option>';
    availableScripts.forEach((script) => {
      const option = document.createElement("option");
      option.value = script.id;
      option.textContent = script.name;
      scriptSelect.appendChild(option);
    });
    scriptDescription.textContent = "";

    const filesResponse = await fetch("/api/analysis/audio-sources");
    if (!filesResponse.ok) throw new Error("Could not fetch external files.");
    const files = await filesResponse.json();

    fileSelectionContainer.innerHTML = "";
    if (files.length === 0) {
      fileSelectionContainer.innerHTML =
        "<p>No audio source directories found.</p>";
    } else {
      files.forEach((file) => {
        const id = `file-check-${file.replace(/[^a-zA-Z0-9]/g, "")}`;
        const div = document.createElement("div");
        div.innerHTML = `
                    <input type="checkbox" id="${id}" value="${file}">
                    <label for="${id}" style="font-size: 0.9rem;">${file}</label>
                `;
        fileSelectionContainer.appendChild(div);
      });
    }

    analysisPopup.style.display = "flex";
  } catch (error) {
    console.error("Error preparing analysis modal:", error);
    alert(`Error: ${error.message}`);
  }
}

async function openJobsModal() {
  jobsPopup.style.display = "flex";
  await populateJobsList();
}

async function populateJobsList() {
  jobsListContainer.innerHTML = "<p>Loading jobs...</p>";
  try {
    const response = await fetch("/api/analysis/jobs");
    if (!response.ok) throw new Error("Failed to fetch job statuses.");
    const jobs = await response.json();

    jobsListContainer.innerHTML = "";
    if (jobs.length === 0) {
      jobsListContainer.innerHTML = "<p>No jobs have been run yet.</p>";
      return;
    }

    jobs.forEach((job) => {
      const jobDiv = document.createElement("div");
      jobDiv.className = "external-data-item";
      let statusClass = "";
      if (job.status === "completed") statusClass = "status-completed";
      if (job.status === "failed") statusClass = "status-failed";
      if (job.status === "running" || job.status === "queued")
        statusClass = "status-running";

      jobDiv.innerHTML = `
                <div class="file-info">
                    <strong>Job ID:</strong> ${job.job_id}<br>
                    <strong>Script:</strong> ${job.script_id}<br>
                    <strong>Submitted:</strong> ${new Date(
                      job.submitted_at
                    ).toLocaleString()}
                </div>
                <div class="file-actions">
                    <span class="job-status ${statusClass}">${job.status}</span>
                </div>
            `;
      jobsListContainer.appendChild(jobDiv);
    });
  } catch (error) {
    console.error("Error populating jobs list:", error);
    jobsListContainer.innerHTML = `<p style="color: red;">${error.message}</p>`;
  }
}

const style = document.createElement("style");
style.innerHTML = `
.job-status { padding: 3px 8px; border-radius: 12px; color: white; font-weight: bold; font-size: 0.9rem; }
.status-completed { background-color: #28a745; }
.status-failed { background-color: #dc3545; }
.status-running { background-color: #007bff; }
`;
document.head.appendChild(style);

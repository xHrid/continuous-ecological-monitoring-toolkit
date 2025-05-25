const imageInput = document.getElementById("image-upload");
const imageLabel = document.querySelector("label[for='image-upload']");

imageInput.addEventListener("change", () => {
  if (imageInput.files.length > 0) {
    imageLabel.classList.add("selected");
  } else {
    imageLabel.classList.remove("selected");
  }
});

document.getElementById('menu-toggle').addEventListener('click', () => {
  document.getElementById('controls').classList.toggle('open');
});

document.getElementById("open-form").onclick = () => {
  map.locate({ watch: true, enableHighAccuracy: true });
  document.getElementById("popup-form").style.display = "flex";
};

document.getElementById("close-form").onclick = () => {
  document.getElementById("popup-form").style.display = "none";
};

let constrainsObj = {
  audio: true,
  video: false,
};
const audioToggle = document.getElementById("audio-toggle");
const audioPlayback = document.getElementById("audioPlayback");

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordedAudioBlob = null;


audioToggle.addEventListener("click", async () => {
  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

      mediaRecorder.onstop = () => {
  recordedAudioBlob = new Blob(audioChunks, { type: "audio/webm" }); // ✅ Save to global var
  audioPlayback.src = URL.createObjectURL(recordedAudioBlob);
  stream.getTracks().forEach((track) => track.stop());
};


      mediaRecorder.start();
      isRecording = true;
      audioToggle.classList.add("recording");
      console.log("Recording started");
    } catch (err) {
      console.error("Microphone error:", err);
    }
  } else {
    mediaRecorder.stop();
    isRecording = false;
    audioToggle.classList.remove("recording");
    console.log("Recording stopped");
  }
});

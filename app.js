
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
const startBtn = document.getElementById("btnStart");
const stopBtn = document.getElementById("btnStop");
const audioPlayback = document.getElementById("audioPlayback");

let mediaRecorder;
let audioChunks = [];
let audioBlob = null;

startBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

    mediaRecorder.onstop = () => {
      audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const audioURL = URL.createObjectURL(audioBlob);
      audioPlayback.src = audioURL;

      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
    };

    mediaRecorder.start();
    console.log("Recording started");

    startBtn.disabled = true;
    stopBtn.disabled = false;
  } catch (err) {
    console.error("Error accessing microphone:", err);
  }
});

stopBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    console.log("Recording stopped");

    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
});

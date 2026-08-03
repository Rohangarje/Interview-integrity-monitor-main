const video = document.getElementById('webcam');
const canvas = document.getElementById('capture-canvas');
const ctx = canvas.getContext('2d');
const faceVal = document.getElementById('face-val');
const faceStatusBox = document.getElementById('status-face');
const micVal = document.getElementById('mic-val');
const micStatusBox = document.getElementById('status-mic');
const violationVal = document.getElementById('violation-count');
const violationBox = document.getElementById('status-violation');
const alertContainer = document.getElementById('alert-container');

// Alert Function
function showAlert(message, type = 'warn') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    alertContainer.appendChild(toast);

    // Remove after animation (4.3s)
    setTimeout(() => {
        toast.remove();
    }, 4500);
}

let audioContext;
let analyser;
let microphone;
let javascriptNode;
let isSilent = true;

// Config
const FRAME_SEND_INTERVAL = 1000; // 1 FPS
const AUDIO_CHECK_INTERVAL = 1000;
let silenceStartTime = null;

async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        video.srcObject = stream;

        // Init Audio
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream); // Fixed potential typo/cache issue
        javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;

        microphone.connect(analyser);
        analyser.connect(javascriptNode);
        javascriptNode.connect(audioContext.destination);

        javascriptNode.onaudioprocess = function () {
            var array = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(array);
            var values = 0;
            var length = array.length;
            for (var i = 0; i < length; i++) {
                values += (array[i]);
            }
            var average = values / length;

            // Threshold for silence (adjustable)
            checkAudio(average);
        }

        startMonitoring();
    } catch (err) {
        alert("Camera/Mic permission denied or error: " + err);
        console.error(err);
    }
}

function checkAudio(volume) {
    // If volume < 5, consider silent
    const THRESHOLD = 2;
    let currentIsSilent = volume < THRESHOLD;

    // Update UI immediately (or throttled)
    micVal.innerText = currentIsSilent ? "Silent" : "Active (" + Math.round(volume) + ")";
    micStatusBox.className = currentIsSilent ? "status-item warn" : "status-item good";

    // Send state periodically handled by separate loop or just sync with frame?
    // Let's use a global var and send it in the loop
    isSilent = currentIsSilent;
}

function startMonitoring() {
    // Frame Loop
    setInterval(() => {
        captureAndSendFrame();
        sendAudioStatus(); // Piggyback or separate? Separate is safer.
    }, FRAME_SEND_INTERVAL);
}

async function captureAndSendFrame() {
    if (!video.videoWidth) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Data = canvas.toDataURL('image/jpeg', 0.5); // Compression

    try {
        const response = await fetch('/api/process_frame/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                frame: base64Data
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            updateFaceUI(data.face_status, data.violation);
        }
    } catch (e) {
        console.error("Frame send error", e);
    }
}

async function sendAudioStatus() {
    try {
        const response = await fetch('/api/send_audio_activity/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                is_silent: isSilent
            })
        });
        const data = await response.json();
        if (data.status === 'success' && data.violation) {
            showAlert("Violation: " + data.violation, "error");
            let count = parseInt(violationVal.innerText) || 0;
            violationVal.innerText = count + 1;
            violationBox.className = "status-item bad";
        }
    } catch (e) { }
}

function updateFaceUI(status, violation) {
    if (status === 'ok') {
        faceVal.innerText = "Good";
        faceStatusBox.className = "status-item good";
    } else if (status === 'no_face') {
        faceVal.innerText = "No Face";
        faceStatusBox.className = "status-item warn"; // Warn first
    } else if (status === 'multiple_faces') {
        faceVal.innerText = "Multiple Faces";
        faceStatusBox.className = "status-item bad";
    }

    if (violation) {
        faceStatusBox.className = "status-item bad"; // Force red on violation
        let count = parseInt(violationVal.innerText) || 0;
        violationVal.innerText = count + 1;
        violationBox.className = "status-item bad";

        // Show alert
        showAlert("Violation: " + violation, "error");
        console.log("Violation:", violation);
    }
}

// Tab Switching
document.addEventListener("visibilitychange", async () => {
    let eventType = document.hidden ? "hidden" : "visible";
    if (document.hidden) {
        try {
            await fetch('/api/log_tab_switch/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: SESSION_ID,
                    event_type: eventType
                })
            });
            // Also increment local counter for feedback
            let count = parseInt(violationVal.innerText) || 0;
            violationVal.innerText = count + 1;
            violationBox.className = "status-item bad";

            showAlert("Violation: Tab Switch Detected!", "error");
        } catch (e) { }
    }
});

window.onblur = async () => {
    try {
        await fetch('/api/log_tab_switch/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                event_type: "blur"
            })
        });
        showAlert("Violation: Window Focus Lost!", "warn");
    } catch (e) { }
};

async function endSession() {
    if (confirm("End Interview?")) {
        try {
            const response = await fetch('/api/end_interview/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: SESSION_ID })
            });
            const data = await response.json();
            alert(`Interview Ended.\nScore: ${data.final_score}\nRisk: ${data.risk_level}`);
            window.location.href = '/';
        } catch (e) {
            window.location.href = '/';
        }
    }
}

// Start
initCamera();

const connEl = document.getElementById("conn");
const statusEl = document.getElementById("status");
const micBtn = document.getElementById("micBtn");
const finalEl = document.getElementById("finalText");
const partialEl = document.getElementById("partialText");
const placeholderEl = document.getElementById("placeholder");
const transcriptEl = document.getElementById("transcript");

let ws = null;
let listening = false;

function setConnected(connected) {
  connEl.textContent = connected ? "Connected" : "Disconnected";
  connEl.className = "badge " + (connected ? "on" : "off");
  micBtn.disabled = !connected;
  if (!connected) setListening(false);
}

function setListening(value) {
  listening = value;
  micBtn.classList.toggle("recording", value);
  statusEl.textContent = value ? "Listening… speak now" : "Idle";
  if (!value) partialEl.textContent = "";
}

function scrollDown() {
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function connect() {
  ws = new WebSocket(`ws://${location.hostname}:8765`);

  ws.onopen = () => setConnected(true);

  ws.onclose = () => {
    setConnected(false);
    setTimeout(connect, 1500); // auto-reconnect
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === "status") {
      setListening(msg.listening);
    } else if (msg.type === "partial") {
      partialEl.textContent = msg.text;
      if (msg.text) placeholderEl.style.display = "none";
    } else if (msg.type === "final") {
      placeholderEl.style.display = "none";
      finalEl.textContent += (finalEl.textContent ? " " : "") + msg.text;
      partialEl.textContent = "";
    }
    scrollDown();
  };
}

micBtn.addEventListener("click", () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(listening ? "stop" : "start");
});

document.getElementById("copyBtn").addEventListener("click", async () => {
  await navigator.clipboard.writeText(finalEl.textContent);
  statusEl.textContent = "Copied to clipboard";
});

document.getElementById("downloadBtn").addEventListener("click", () => {
  const blob = new Blob([finalEl.textContent], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "transcript.txt";
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById("clearBtn").addEventListener("click", () => {
  finalEl.textContent = "";
  partialEl.textContent = "";
  placeholderEl.style.display = "";
});

setConnected(false);
connect();
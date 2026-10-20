import asyncio
import json
import os
import queue
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel
from websockets.asyncio.server import serve

SAMPLE_RATE = 16000
MODEL_PATH = "model"
TRANSCRIPT_FILE = "transcript.txt"
HTTP_PORT = 8000
WS_PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

clients = set()
audio_q = queue.Queue()
stream = None
loop = None


def broadcast(payload):
    """Send a JSON message to every connected browser (thread-safe)."""
    if loop is None:
        return
    msg = json.dumps(payload)
    for ws in list(clients):
        asyncio.run_coroutine_threadsafe(ws.send(msg), loop)


def recognizer_worker():
    """Runs in a thread: turns microphone audio into text."""
    rec = KaldiRecognizer(Model(MODEL_PATH), SAMPLE_RATE)
    while True:
        data = audio_q.get()

        if data is None:  # mic stopped: flush whatever is left
            text = json.loads(rec.FinalResult()).get("text", "")
            if text:
                broadcast({"type": "final", "text": text})
                save_line(text)
            continue

        if rec.AcceptWaveform(data):
            text = json.loads(rec.Result()).get("text", "")
            if text:
                broadcast({"type": "final", "text": text})
                save_line(text)
        else:
            partial_text = json.loads(rec.PartialResult()).get("partial", "")
            broadcast({"type": "partial", "text": partial_text})


def save_line(text):
    with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def start_listening():
    global stream
    if stream is not None:
        return

    def callback(indata, frames, time, status):
        audio_q.put(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=callback,
    )
    stream.start()
    broadcast({"type": "status", "listening": True})


def stop_listening():
    global stream
    if stream is None:
        return
    stream.stop()
    stream.close()
    stream = None
    audio_q.put(None)
    broadcast({"type": "status", "listening": False})


async def handler(ws):
    clients.add(ws)
    await ws.send(json.dumps({"type": "status", "listening": stream is not None}))
    try:
        async for message in ws:
            if message == "start":
                start_listening()
            elif message == "stop":
                stop_listening()
    finally:
        clients.discard(ws)
        if not clients:
            stop_listening()


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run_http_server():
    handler_cls = partial(QuietHandler, directory=BASE_DIR)
    ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), handler_cls).serve_forever()


async def main():
    global loop
    loop = asyncio.get_running_loop()

    SetLogLevel(-1)
    if not os.path.isdir(MODEL_PATH):
        print("Model folder './model' not found. Download the Vosk model first.")
        return

    threading.Thread(target=recognizer_worker, daemon=True).start()
    threading.Thread(target=run_http_server, daemon=True).start()

    url = f"http://127.0.0.1:{HTTP_PORT}"
    print(f"Open {url} in your browser. Press Ctrl+C to quit.")
    webbrowser.open(url)

    async with serve(handler, "127.0.0.1", WS_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        stop_listening()
        print("\nBye.")
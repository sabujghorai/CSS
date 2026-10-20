import queue
import sounddevice as sd

SAMPLE_RATE = 16000


def mic_stream(block_size=4000):
    """Yield raw microphone audio in small chunks (about 0.25 sec each)."""
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=block_size,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        while True:
            yield q.get()
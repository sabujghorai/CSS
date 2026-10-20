import os
import shutil
import urllib.request
import zipfile

MODEL_NAME = "vosk-model-small-en-us-0.15"
URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
ZIP_FILE = MODEL_NAME + ".zip"
TARGET = "model"

if os.path.isdir(TARGET):
    print("Model folder already exists. Nothing to do.")
else:
    print(f"Downloading {MODEL_NAME} (about 40 MB)...")
    urllib.request.urlretrieve(URL, ZIP_FILE)
    print("Extracting...")
    with zipfile.ZipFile(ZIP_FILE) as z:
        z.extractall(".")
    shutil.move(MODEL_NAME, TARGET)
    os.remove(ZIP_FILE)
    print("Done. Model saved in ./model")
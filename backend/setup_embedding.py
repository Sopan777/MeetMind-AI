import os
import shutil
import glob

download_dir = r"C:\Users\sopan\Downloads"
local_pyannote_dir = r"C:\Users\sopan\.gemini\antigravity\scratch\meetingmind-ai\backend\local_pyannote"
embedding_dir = os.path.join(local_pyannote_dir, "embedding")

os.makedirs(embedding_dir, exist_ok=True)

bins = glob.glob(os.path.join(download_dir, "pytorch_model*.bin"))
bins.sort(key=os.path.getmtime, reverse=True)

if bins:
    latest_bin = bins[0]
    dest = os.path.join(embedding_dir, "pytorch_model.bin")
    print(f"Moving {latest_bin} to {dest}")
    shutil.move(latest_bin, dest)
    print("Successfully moved the embedding model!")
else:
    print("No pytorch_model.bin found in Downloads!")

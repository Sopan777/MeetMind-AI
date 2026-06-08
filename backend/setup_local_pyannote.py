import os
import shutil
import glob
import re

download_dir = r"C:\Users\sopan\Downloads"
local_pyannote_dir = r"C:\Users\sopan\.gemini\antigravity\scratch\meetingmind-ai\backend\local_pyannote"

os.makedirs(os.path.join(local_pyannote_dir, "segmentation"), exist_ok=True)
os.makedirs(os.path.join(local_pyannote_dir, "diarization"), exist_ok=True)

# Find config files
configs = glob.glob(os.path.join(download_dir, "config*.yaml"))
bins = glob.glob(os.path.join(download_dir, "pytorch_model*.bin"))

print("Found configs:", configs)
print("Found bins:", bins)

segmentation_config = None
diarization_config = None

for c in configs:
    with open(c, 'r', encoding='utf-8') as f:
        content = f.read()
        if "segmentation:" in content or "Pipeline" in content:
            diarization_config = c
        elif "PytorchLightningModel" in content or "SincTDNN" in content or "segmentation" in content.lower():
            # some segmentation configs have PytorchLightningModel
            segmentation_config = c

print(f"Detected diarization config: {diarization_config}")
print(f"Detected segmentation config: {segmentation_config}")

if diarization_config:
    shutil.copy(diarization_config, os.path.join(local_pyannote_dir, "diarization", "config.yaml"))
    print("Moved diarization config.")
    
    # Check for embedding model in diarization config
    with open(os.path.join(local_pyannote_dir, "diarization", "config.yaml"), 'r', encoding='utf-8') as f:
        print("Diarization config contents:")
        print(f.read())

if segmentation_config:
    shutil.copy(segmentation_config, os.path.join(local_pyannote_dir, "segmentation", "config.yaml"))
    print("Moved segmentation config.")

if bins:
    # Usually only segmentation has a .bin in pyannote 3.1
    # Diarization uses speechbrain for embeddings.
    # Assuming the first bin is segmentation model
    # Wait, check file sizes.
    for b in bins:
        size = os.path.getsize(b)
        print(f"Found bin: {b} size: {size} bytes")
        # Segmentation model is usually around 20-30 MB or more.
        shutil.copy(b, os.path.join(local_pyannote_dir, "segmentation", "pytorch_model.bin"))
        print("Moved bin to segmentation.")
        break

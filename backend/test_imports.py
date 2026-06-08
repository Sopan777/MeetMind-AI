import sys
import traceback

print("Testing numpy...")
try:
    import numpy as np
    print("Numpy version:", np.__version__)
except Exception as e:
    traceback.print_exc()

print("\nTesting faster_whisper...")
try:
    import faster_whisper
    from faster_whisper import WhisperModel
    print("faster_whisper loaded.")
    # test loading model
    model_path = "C:/Users/sopan/.gemini/antigravity/scratch/meetingmind-ai/backend/local_whisper_model"
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    print("Model loaded successfully")
except Exception as e:
    traceback.print_exc()

print("\nTesting pyannote.audio...")
try:
    import torchaudio
    try:
        torchaudio.set_audio_backend("soundfile")
    except AttributeError:
        torchaudio.set_audio_backend = lambda x: None

    from pyannote.audio import Pipeline
    print("Pyannote loaded.")
except Exception as e:
    traceback.print_exc()

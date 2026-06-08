import os
import torchaudio
try:
    torchaudio.set_audio_backend("soundfile")
except AttributeError:
    torchaudio.set_audio_backend = lambda x: None

from pyannote.audio import Pipeline
from dotenv import load_dotenv

def download_model():
    print("Loading environment variables...")
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    
    if not token:
        print("ERROR: HF_TOKEN not found in .env file!")
        return

    print("Starting download of pyannote/speaker-diarization-3.1 and its dependencies...")
    print("This will download approximately 2.8GB to your HuggingFace cache.")
    
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token
        )
        print("Download successfully completed! The model is now cached.")
    except Exception as e:
        print(f"An error occurred during download: {e}")
        print("Please ensure you have accepted the user conditions on HuggingFace for:")
        print("1. pyannote/speaker-diarization-3.1")
        print("2. pyannote/segmentation-3.0")

if __name__ == "__main__":
    download_model()

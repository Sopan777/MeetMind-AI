import os
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")
print(f"Loaded token starting with: {token[:4] if token else 'None'}")

try:
    path = hf_hub_download(repo_id="pyannote/speaker-diarization-3.1", filename="config.yaml", token=token)
    print("Success! Downloaded config.yaml to", path)
except Exception as e:
    import traceback
    traceback.print_exc()
